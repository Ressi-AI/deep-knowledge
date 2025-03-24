import os
from typing import Optional
from collections import defaultdict
from threading import Lock
from functools import partial
from loguru import logger
import sys
logger_format = (
    "<green>{time:HH:mm:ss.SSS}</green> | "
    "<level>{message}</level>"
)
logger.remove()
logger.add(sys.stderr, format=logger_format)
from langchain_core.language_models import BaseChatModel
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, convert_to_openai_messages
from deep_knowledge.generic_llm_provider import GenericLLMProvider
from deep_knowledge.utils import (
    loaders, needs_ocr, ocr_loader,
    model_name_from_langchain_instance, content_for_model,
    dct_model_cost, model_cost, token_counter,
    PAGE_BREAK,
)
from deep_knowledge.summary.utils import extract_modules, batch_modules, extract_syntheses
from deep_knowledge.summary.prompts import (
    system_prompt_mind_map_structural_conceptual,
    initial_prompt_mind_map,

    system_prompt_summary_architect,
    initial_prompt_summary_architect,

    system_prompt_content_synthesizer,
    initial_prompt_content_synthesizer,
)

"""
Possible streaming data:
- while generating with LLM: data = {"type": "generation", "content": "generated content"}
- other events: data = {"type": "event", **kwargs, "content": "event content"}
"""


def default_stream_callback(data):
    if data["type"] == "event":
        kwargs = {k: v for k, v in data.items() if k not in ["type", "content"]}
        logger.info(f"{kwargs}: {data.get('content', '')}")
        return
    if data["type"] == "generation":
        print(data["content"], end="", flush=True)
        return


class Summary:
    def __init__(
            self,
            llm: BaseChatModel | str = "auto",
            input_path: Optional[str] = None,
            input_documents: Optional[list[Document]] = None,
            input_content: Optional[str] = None,
            extra_instructions: Optional[str] = None,
            language: Optional[str] = None,
            stream: Optional[bool] = False,
            streaming_callback: Optional[callable] = None,
    ):
        self.llm = get_llm(llm)
        self.model_name = model_name_from_langchain_instance(self.llm.llm)
        _, self.litellm_model_name = model_cost(self.model_name)
        self.input_path = input_path
        self.input_documents = input_documents
        self.input_content = input_content
        self.extra_instructions = extra_instructions
        self.stream = stream
        self.streaming_callback = streaming_callback
        if self.stream and self.streaming_callback is None:
            self.streaming_callback = default_stream_callback
        self.language = language
        self.content = None
        self.final_input = None
        self.mind_map = None
        self.summary_architecture = None
        self.summary_modules = None
        self.syntheses = None
        self.output = None
        self.token_usage = defaultdict(lambda: {"prompt_tokens": 0, "completion_tokens": 0})
        self.token_usage_lock = Lock()
        return

    def _cost_callback(self, output, model, messages=None, output_content=None):
        if not hasattr(output, "usage_metadata"):
            return

        prompt_tokens = output.usage_metadata.get("prompt_tokens", 0) or output.usage_metadata.get("input_tokens", 0)
        if prompt_tokens <= 0 and messages is not None:
            prompt_tokens = token_counter(model=model, messages=convert_to_openai_messages(messages))
        prompt_tokens = max(0, prompt_tokens)

        completion_tokens = output.usage_metadata.get("completion_tokens", 0) or output.usage_metadata.get("output_tokens", 0)
        if completion_tokens <= 0 and output_content is not None:
            completion_tokens = token_counter(text=output_content, model=model)
        completion_tokens = max(0, completion_tokens)

        with self.token_usage_lock:
            self.token_usage[model]["prompt_tokens"] += prompt_tokens
            self.token_usage[model]["completion_tokens"] += completion_tokens
        return

    @property
    def cost(self):
        """
        Simple cost function that calculates the cost of the prompt and completion tokens for each model
        without taking into consideration batching / caching or other features.
        """
        cost = {
            "prompt": 0,
            "completion": 0,
            "total": 0,
        }
        for model, usage in self.token_usage.items():
            cost["prompt"] += usage["prompt_tokens"] * dct_model_cost[model]["input_cost_per_token"]
            cost["completion"] += usage["completion_tokens"] * dct_model_cost[model]["output_cost_per_token"]

        cost["total"] = cost["prompt"] + cost["completion"]
        return cost

    def prepare_content(self):
        if self.input_content is not None:
            self.content = self.input_content

        input_documents = None
        if self.input_path is not None:
            ext = os.path.splitext(self.input_path)[1][1:].lower()
            if ext not in loaders:
                raise ValueError(f"Unsupported file extension: {ext}")

            loader = loaders[ext](self.input_path)
            input_documents = loader.load()
            if ext == 'pdf' and needs_ocr(input_documents):
                logger.warning("Provided PDF document needs OCR")
                loader = ocr_loader(self.input_path)
                if loader is None:
                    raise ValueError("No valid OCR API keys detected")
                input_documents = loader.load()

        input_documents = input_documents or self.input_documents
        if len(input_documents or []) > 0:
            contents = []
            for doc in input_documents:
                contents.extend([doc.page_content, PAGE_BREAK])
            contents = contents[:-1]
            self.content = "\n\n".join(contents)

        self.final_input = self.content
        if self.content is None:
            raise ValueError("No input content provided")
        return

    def log_usage(self):
        str_usage = "Token Usage:\n"
        for model, usage in self.token_usage.items():
            str_usage += f"  {model}:\n"
            str_usage += f"    Prompt Tokens: {usage['prompt_tokens']:,}\n"
            str_usage += f"    Completion Tokens: {usage['completion_tokens']:,}\n"
        str_usage += f"Total Cost: ${self.cost['total']:.2f}"
        logger.info("\n" + str_usage)
        return

    def run(self):
        self.prepare_content()
        self.final_input = content_for_model(content=self.content, model_name=self.model_name)
        self.generate_mind_map()
        self.generate_summary_architecture()
        self.generate_full_summary()
        self.log_usage()
        return

    def generate_mind_map(self):
        if self.streaming_callback is not None:
            self.streaming_callback({"type": "event", "event_type": "start", "stage": "mind_map", "content": "Generating Mind Map"})
        logger.info("=== Step 1 === Generating Mind Map")
        self.mind_map = self.llm.get_chat_response(
            messages=[
                SystemMessage(system_prompt_mind_map_structural_conceptual(language=self.language)),
                HumanMessage(initial_prompt_mind_map(content=self.final_input))
            ],
            stream=self.stream,
            streaming_callback=self.streaming_callback,
            cost_callback=partial(self._cost_callback, model=self.litellm_model_name),
        )
        if self.streaming_callback is not None:
            self.streaming_callback({"type": "event", "event_type": "stop", "stage": "mind_map", "content": "Finished generating Mind Map"})
        return

    def generate_summary_architecture(self):
        if self.streaming_callback is not None:
            self.streaming_callback({"type": "event", "event_type": "start", "stage": "summary_architect", "content": "Generating Summary Architecture"})
        logger.info("=== Step 2 === Generating Summary Architecture")
        self.summary_architecture = self.llm.get_chat_response(
            messages=[
                SystemMessage(system_prompt_summary_architect(language=self.language)),
                HumanMessage(initial_prompt_summary_architect(
                    content=self.final_input, mind_map=self.mind_map, extra_info=self.extra_instructions
                ))
            ],
            stream=self.stream,
            streaming_callback=self.streaming_callback,
            cost_callback=partial(self._cost_callback, model=self.litellm_model_name),
        )

        self.summary_modules = extract_modules(architect_output=self.summary_architecture)
        wc = sum([x.word_count for x in self.summary_modules])
        logger.info(f"Final summary is attempting to be {wc} words long")
        if self.streaming_callback is not None:
            self.streaming_callback({"type": "event", "event_type": "stop", "stage": "summary_architect", "content": "Finished generating Summary Architecture"})
        return

    def generate_full_summary(self):
        if self.streaming_callback is not None:
            self.streaming_callback({"type": "event", "event_type": "start", "stage": "content_synthesizer", "content": "Generating Full Summary"})
        logger.info("=== Step 3 === Generating Full Summary")
        batches = batch_modules(modules=self.summary_modules)
        dump_all_modules = "\n".join([x.module_heading for x in self.summary_modules])
        summaries = []
        raw_output = False
        syntheses = []
        for batch in batches:
            module_specifications = []
            for i, module in enumerate(batch):
                module_specifications.append(module.full_content)
            if len(batches) > 1:
                module_specifications.append(f"---\nFor reference, here's the list of all modules, BUT YOU SHOULD ONLY WORK ON THE MODULES IN THIS BATCH, mentioned above:\n{dump_all_modules}")
            module_specifications = "\n\n".join(module_specifications)
            response = self.llm.get_chat_response(
                messages=[
                    SystemMessage(system_prompt_content_synthesizer(
                        module_specifications=module_specifications, language=self.language
                    )),
                    HumanMessage(initial_prompt_content_synthesizer(content=self.final_input))
                ],
                stream=self.stream,
                streaming_callback=self.streaming_callback,
                cost_callback=partial(self._cost_callback, model=self.litellm_model_name),
            )
            summaries.append(response)
            crt_syntheses = extract_syntheses(response)
            if len(crt_syntheses) != len(batch):
                logger.warning(f"Expected {len(batch)} syntheses, but got {len(crt_syntheses)}")
                raw_output = True
            syntheses.extend(crt_syntheses)

        if raw_output:
            dump_summary = "\n\n".join(summaries)
        else:
            dump_summary = "\n\n".join([f"## {x.module_title}\n{x.full_content}" for x in syntheses])
        self.output = f"""# MIND MAP\n{self.mind_map}\n\n# SUMMARY\n{dump_summary}"""
        if self.streaming_callback is not None:
            self.streaming_callback({"type": "event", "event_type": "stop", "stage": "content_synthesizer", "content": "Finished generating Full Summary"})
        return


def get_llm(llm: BaseChatModel | str = "auto"):
    if isinstance(llm, str):
        if all([os.environ.get(x) is None for x in ["OPENAI_API_KEY", "GOOGLE_API_KEY"]]):
            raise ValueError("Auto mode working only with OpenAI or Google API keys. None of them detected.")

        if os.environ.get("GOOGLE_API_KEY"):
            model_kwargs = dict(model="gemini-2.0-flash", temperature=0.1)
            logger.info(f"Auto mode, using GOOGLE_API_KEY: {model_kwargs}")
            return GenericLLMProvider.from_provider(provider="google_genai", **model_kwargs)

        if os.environ.get("OPENAI_API_KEY"):
            model_kwargs = dict(model_name="gpt-4o", temperature=0.1)
            logger.info(f"Auto mode, using OPENAI_API_KEY: {model_kwargs}")
            return GenericLLMProvider.from_provider(provider="openai", **model_kwargs)

    return GenericLLMProvider(llm)
