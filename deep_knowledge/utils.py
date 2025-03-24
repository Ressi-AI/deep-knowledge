import os
import random
from loguru import logger
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredMarkdownLoader,
    UnstructuredEPubLoader,

    AzureAIDocumentIntelligenceLoader,
    AmazonTextractPDFLoader,
)
from langchain_core.documents import Document
from litellm import model_cost as dct_model_cost
from litellm import token_counter
litellm_models = list(dct_model_cost.keys())

PAGE_BREAK = "<!-- PageBreak -->"
CONTEXT_SCALE_FACTOR = 0.93

loaders = {
    'txt': TextLoader,
    '': TextLoader,
    'pdf': PyMuPDFLoader,
    'docx': UnstructuredWordDocumentLoader,
    'doc': UnstructuredWordDocumentLoader,
    'md': UnstructuredMarkdownLoader,
    'epub': UnstructuredEPubLoader,
}


def needs_ocr(pages: list[Document], char_threshold=100, low_text_page_ratio=0.3) -> bool:
    """
    Determine if a PDF needs OCR by analyzing all pages for text content.
    """
    total_pages = len(pages)
    low_text_pages = 0

    # Check all pages for text content
    for page in pages:
        text = page.page_content
        char_count = len(text.strip())

        if char_count < char_threshold:
            low_text_pages += 1

    # Calculate ratio of pages with low text
    low_text_ratio = low_text_pages / total_pages if total_pages > 0 else 0

    # Recommend OCR if more than the specified ratio of pages have low text
    ocr_recommended = low_text_ratio > low_text_page_ratio
    return ocr_recommended


def ocr_loader(input_path: str):
    loader = None
    if all([x is not None for x in ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "AZURE_DOCUMENT_INTELLIGENCE_KEY"]]):
        logger.info("Using Azure Document Intelligence for OCR")
        loader = AzureAIDocumentIntelligenceLoader(
            api_endpoint=os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"],
            api_key=os.environ["AZURE_DOCUMENT_INTELLIGENCE_KEY"],
            file_path=input_path,
            api_model="prebuilt-layout",
            mode="markdown",
        )

    # TODO AmazonTextractPDFLoader

    if loader is None:
        logger.error("No valid OCR API keys detected")

    return loader


def input_tokens_target(max_num_tokens):
    return int(CONTEXT_SCALE_FACTOR * max_num_tokens)


def model_name_from_langchain_instance(llm) -> str:
    if hasattr(llm, 'model_name'):
        return llm.model_name

    return llm.model


def model_cost(model_name: str):
    if "/" in model_name:
        model_name = model_name.split("/")[1]

    crt_model_cost = dct_model_cost.get(model_name)
    if crt_model_cost is None:
        for litellm_model in litellm_models:
            if model_name in litellm_model:
                model_name = litellm_model
                crt_model_cost = dct_model_cost[litellm_model]
                break

    return crt_model_cost, model_name


def content_for_model(content: str, model_name: str) -> str:
    original_model_name = model_name
    crt_model_cost, model_name = model_cost(model_name)

    try:
        num_content_tokens = token_counter(text=content, model=model_name)
    except:
        num_content_tokens = token_counter(text=content)

    logger.info(f"Content token count: {num_content_tokens}")

    if crt_model_cost is None:
        if num_content_tokens >= input_tokens_target(128_000):
            logger.warning(f"Could not determine input size for model {original_model_name}. Using full content which may lead to errors due to token limits.")
        return content

    context_size = crt_model_cost["max_input_tokens"]
    if num_content_tokens < input_tokens_target(context_size):
        logger.success(f"Input fits within model {original_model_name} token limits: {context_size}")
        return content

    sampled_content = sample_text_for_context(
        text=content,
        num_tokens=num_content_tokens,
        context_size=input_tokens_target(context_size),
    )

    return sampled_content


def sample_text_for_context(text, num_tokens, context_size):
    """
    Sample text to fit within a given LLM context size using random sampling.

    Args:
        text (str): The input text
        num_tokens (int): The number of tokens in the text
        context_size (int): The maximum number of tokens allowed

    Returns:
        str: The sampled text that fits within the context size
    """
    # If text fits within context, return the entire text
    if num_tokens <= context_size:
        return text

    # Split the text into lines
    lines = text.split('\n')
    lines = list(filter(lambda x: x != PAGE_BREAK, lines))
    lines = [line.strip() for line in lines]
    empty_line_indices = [i for i, line in enumerate(lines) if len(line) == 0]
    content_line_indices = [i for i, line in enumerate(lines) if len(line) > 0]
    total_lines = len(content_line_indices)

    # Calculate how many lines we can keep based on token ratio
    keep_ratio = context_size / num_tokens
    if keep_ratio < 1:
        logger.info(f"Sampling text to fit within adapted ({CONTEXT_SCALE_FACTOR} scale factor) LLM context size: {context_size} tokens")
    lines_to_keep = max(1, int(total_lines * keep_ratio))

    # Randomly select line indices
    selected_indices = random.sample(content_line_indices, min(lines_to_keep, total_lines))
    selected_indices += empty_line_indices

    # Sort indices to preserve original order
    selected_indices.sort()

    # Get the selected lines
    selected_lines = [lines[i] for i in selected_indices]

    # Join the selected lines back into a text
    return '\n'.join(selected_lines)
