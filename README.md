# Deep Knowledge

## The Problem

Current summarization tools in the market typically generate shallow, surface-level summaries that fail to capture the rich complexity of content. These summaries often:

- Miss the deeper connections between concepts
- Ignore the hierarchical structure of information
- Extract only the most obvious points
- Lack contextual understanding
- Fail to identify underlying frameworks or mental models

As a result, these tools provide little value for comprehensive learning, critical analysis, or deep content exploration.

## Our Approach: Multi-Agent Summarization

Deep Knowledge introduces a powerful multi-agent system for creating deep, comprehensive summaries of complex content. Instead of treating summarization as a single task, we break it down into a coordinated pipeline of specialized agents:

1. **Mind Map Agent**: Analyzes the structure and concepts of the content, creating both a structural and conceptual map
2. **Summary Architect**: Designs a modular summary structure with specific instructions for each component
3. **Content Synthesizer**: Generates each module following the architect's specifications

This approach ensures that summaries retain the original content's structure while revealing deeper patterns, frameworks, and connections.

## Key Features

- **Deep structured summarization**: Creates summaries that capture both structure and conceptual depth
- **Smart content handling**: Automatically processes various document types with OCR detection
- **Token-aware processing**: Intelligently manages content to work within model context limitations
- **Langchain integration**: Seamlessly works with Langchain chat models
- **Visual mind mapping**: Generates comprehensive mind maps to visualize content structure
- **Langchain Integration**: Works with all LLMs supported by Langchain

## Installation

```bash
pip install deep-knowledge
```

## Usage Example

```python
from deep_knowledge.summary import Summary

# From a file path
summary = Summary(input_path="my_book.pdf")
summary.run()
print(summary.output)

# From text content
text_content = "..."
summary = Summary(input_content=text_content)
summary.run()
print(summary.output)
```

## Streamlit Demo
We created a Streamlit demo to showcase the Deep Knowledge summarization pipeline. To run the demo, follow these steps:

```bash
export PYTHONPATH=$PYTHONPATH:"$(pwd)"
streamlit run demo/streamlit_app.py
```

## Langchain Integration

Deep Knowledge integrates smoothly with Langchain chat models. You can provide your own Langchain chat model, or use the "auto" option which intelligently selects the best available model:

```python
from langchain_openai import ChatOpenAI
from deep_knowledge.summary import Summary

# Using a specific Langchain model
llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
summary = Summary(llm=llm, input_path="article.pdf")

# Using auto mode (automatically selects from available API keys)
summary = Summary(llm="auto", input_path="article.pdf")
```

In "auto" mode, the system prioritizes:
1. Google Gemini models (if `GOOGLE_API_KEY` is available)
2. OpenAI models (if `OPENAI_API_KEY` is available)

This allows for easy experimentation with different LLM providers.

## Flexible Input Options

Deep Knowledge accepts multiple input formats:

```python
# From a file path
summary = Summary(input_path="document.pdf")

# From raw text content
summary = Summary(input_content="Your content here...")

# From Langchain Document objects
from langchain_core.documents import Document
documents = [Document(page_content="Content 1"), Document(page_content="Content 2")]
summary = Summary(input_documents=documents)
```

The library supports various file formats including PDF, DOCX, TXT, Markdown, and EPUB, with automatic OCR detection for scanned documents.

## Roadmap

### Token Management Optimization
Current implementation can be expensive as it sends the full content to each module creation step. Future improvements will include:
- Having the Summary Architect return metadata about specific content sections for each module

However, using Google Gemini Flash models allows for free/low-cost experimentation

### Interactive Refinement and Follow-ups
The current pipeline operates as a single-pass process, but users often need to refine outputs based on initial results.
- Enabling conversational interactions to shape the summarization process
- Allowing targeted refinement of specific modules without regenerating the entire summary

### Adding possibility to configure LLM based on step
Now, there's only one LLM that works for all steps.
But it would be a good feature to allow experimentation with different LLMs for different steps. E.g.:
- gpt-4o for the Mind Map Agent
- o1 for the Summary Architect
- gemini-2.0-flash for the Content Synthesizer

### Improved Reproducibility
We're working on enhancing the system's reliability when LLMs don't precisely follow the expected output format, including:
- More robust output parsing
- Fallback strategies for format deviations
- Better error handling and recovery

### Enhanced OCR Capabilities
Plans to expand OCR options include:
- Supporting additional OCR providers
- Implementing local OCR processing options
- Improving detection of scanned content

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.
