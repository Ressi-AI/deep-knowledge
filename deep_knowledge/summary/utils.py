import re
from typing import List, Dict, Any
from pydantic import BaseModel


class ModuleOutline(BaseModel):
    index: int
    title: str
    word_count: int
    details: str

    def heading(self):
        return f"Module #{self.index}: {self.title}"

    def full_content(self):
        return f"{self.heading()}\nWORD COUNT: {self.word_count}\n\n{self.details}"


def extract_modules(architect_output: str) -> List[ModuleOutline]:
    """Extract module information from Summary Architect output using the new XML tag structure."""
    # Find all content between <MODULE> and </MODULE> tags
    module_pattern = r'<MODULE>(.*?)</MODULE>'
    modules_found = re.finditer(module_pattern, architect_output, re.DOTALL)

    result = []
    for match in modules_found:
        # Get the full module content (without the tags)
        full_content = match.group(1).strip()

        # Extract index, title, and word count using regex
        index_match = re.search(r'<INDEX>(.*?)</INDEX>', full_content, re.DOTALL)
        title_match = re.search(r'<TITLE>(.*?)</TITLE>', full_content, re.DOTALL)
        word_count_match = re.search(r'<WORD_COUNT>(.*?)</WORD_COUNT>', full_content, re.DOTALL)
        details_match = re.search(r'<DETAILS>(.*?)</DETAILS>', full_content, re.DOTALL)

        # Skip if essential information is missing
        if not (index_match and title_match):
            continue

        # Convert index to int, defaulting to 0 if conversion fails
        try:
            index = int(index_match.group(1).strip())
        except (ValueError, TypeError):
            index = 0

        title = title_match.group(1).strip()

        # Get word count, default to 0 if missing or invalid
        try:
            word_count = int(word_count_match.group(1).strip()) if word_count_match else 0
        except (ValueError, TypeError):
            word_count = 0

        # Extract details section, or use empty string if not found
        details = details_match.group(1).strip() if details_match else ""

        result.append(ModuleOutline(
            index=index,
            title=title,
            word_count=word_count,
            details=details,
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
    sorted_modules = sorted(modules, key=lambda m: m.index)

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
    """Extract synthesis information using the new XML tag structure."""
    synthesis_pattern = r'<SYNTHESIS>(.*?)</SYNTHESIS>'
    syntheses_found = re.finditer(synthesis_pattern, text, re.DOTALL)

    result = []
    for match in syntheses_found:
        # Get the full synthesis content (without the tags)
        full_content = match.group(1).strip()

        # Extract module index using the new XML tags
        index_match = re.search(r'<INDEX>(.*?)</INDEX>', full_content, re.DOTALL)
        # Extract module title using the new XML tags
        title_match = re.search(r'<TITLE>(.*?)</TITLE>', full_content, re.DOTALL)
        # Extract content between <CONTENT> and </CONTENT> tags (remains the same)
        content_match = re.search(r'<CONTENT>(.*?)</CONTENT>', full_content, re.DOTALL)

        # Skip if essential information is missing
        if not (index_match and title_match and content_match):
            continue

        # Convert index to int, defaulting to 0 if conversion fails
        try:
            module_index = int(index_match.group(1).strip())
        except (ValueError, TypeError):
            module_index = 0

        module_title = title_match.group(1).strip()
        content = content_match.group(1).strip()

        # Create and add Synthesis object
        result.append(Synthesis(
            module_index=module_index,
            module_title=module_title,
            full_content=content
        ))

    # Sort by module index
    result.sort(key=lambda x: x.module_index)

    return result
