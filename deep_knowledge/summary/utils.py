import re
from typing import List, Dict, Any
from pydantic import BaseModel


class ModuleOutline(BaseModel):
    module_heading: str
    module_title: str
    module_index: int
    word_count: int
    full_content: str


def extract_module_info(module_heading):
    # Extract the module index (the number)
    index_match = re.search(r'MODULE\s+#?(\d+):', module_heading)
    module_index = int(index_match.group(1)) if index_match else 0

    # Extract the module title (everything after "MODULE #X:")
    module_title = re.sub(r'^MODULE\s+#?\d+:\s*', '', module_heading).strip()

    return module_index, module_title


def extract_modules(architect_output: str) -> List[ModuleOutline]:
    """Extract module information from Summary Architect output using <MODULE> tags."""
    # Find all content between <MODULE> and </MODULE> tags
    module_pattern = r'<MODULE>(.*?)</MODULE>'
    modules_found = re.finditer(module_pattern, architect_output, re.DOTALL)

    result = []
    for match in modules_found:
        # Get the full module content (without the tags)
        full_content = match.group(1).strip()

        # Get the first line which should contain the module heading
        lines = full_content.split('\n')
        module_heading_line = next((line for line in lines if re.search(r'MODULE\s+#?\d+:', line)), "")

        if not module_heading_line:
            continue  # Skip if no valid module heading found

        module_heading = module_heading_line.strip()
        module_index, module_title = extract_module_info(module_heading)

        # Extract word count
        word_count_match = re.search(r'WORD COUNT:\s*(\d+)', full_content)
        word_count = int(word_count_match.group(1)) if word_count_match else 0

        result.append(ModuleOutline(
            module_heading=module_heading,
            module_title=module_title,
            module_index=module_index,
            word_count=word_count,
            full_content=full_content,
        ))

    return result


def batch_modules(modules: List[ModuleOutline], max_words_per_batch: int = 1500) -> List[List[ModuleOutline]]:
    """
    Group modules into batches with a maximum of 1500 words total per batch.

    Args:
        modules: List of ModuleOutline objects
        max_words_per_batch: Maximum total word count per batch (default: 1500)

    Returns:
        List of lists, where each inner list contains modules for one batch
    """
    # Sort modules by index to maintain proper order
    sorted_modules = sorted(modules, key=lambda m: m.module_index)

    batches = []
    current_batch = []
    current_word_count = 0

    for module in sorted_modules:
        # Handle oversized modules (single module exceeds max words)
        if module.word_count > max_words_per_batch:
            # If we have modules in current batch, finalize it first
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_word_count = 0

            # Add oversized module as its own batch
            batches.append([module])
            continue

        # If adding this module would exceed limit and we have modules in batch
        if current_word_count + module.word_count > max_words_per_batch and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_word_count = 0

        # Add module to current batch
        current_batch.append(module)
        current_word_count += module.word_count

    # Add any remaining modules in current batch
    if current_batch:
        batches.append(current_batch)

    return batches


class Synthesis(BaseModel):
    module_index: int
    module_title: str
    full_content: str


def extract_syntheses(text: str) -> list[Synthesis]:
    synthesis_pattern = r'<SYNTHESIS>(.*?)</SYNTHESIS>'
    syntheses_found = re.finditer(synthesis_pattern, text, re.DOTALL)

    result = []
    for match in syntheses_found:
        # Get the full synthesis content (without the tags)
        full_content = match.group(1).strip()

        # Extract module index
        index_match = re.search(r'MODULE_INDEX:\s*(\d+)', full_content)
        module_index = int(index_match.group(1)) if index_match else 0

        # Extract module title
        title_match = re.search(r'MODULE_TITLE:\s*(.*?)(?:\n|<CONTENT>)', full_content, re.DOTALL)
        module_title = title_match.group(1).strip() if title_match else ""

        # Extract content between <CONTENT> and </CONTENT> tags
        content_match = re.search(r'<CONTENT>(.*?)</CONTENT>', full_content, re.DOTALL)
        content = content_match.group(1).strip() if content_match else ""

        # Create and add Synthesis object
        result.append(Synthesis(
            module_index=module_index,
            module_title=module_title,
            full_content=content
        ))

    # Sort by module index
    result.sort(key=lambda x: x.module_index)

    return result
