section_content = "# CONTENT\n<content>\n{content}\n</content>"
section_mind_map = "# MIND MAP\n<mind_map>\n{mind_map}\n</mind_map>"
default_language = "English"

# MIND MAP
def system_prompt_mind_map_structural(language=None):
    language = language or default_language
    prompt = f"""You are an expert in creating detailed, visually engaging mind maps.

# Goal
Create a comprehensive mind map of the [CONTENT TYPE] titled "[CONTENT TITLE]" by [CREATOR]. Structure it following the content's natural organization rather than imposing external categories.

# Instructions
1. Follow the content's actual structure precisely (sections, topics, segments)
2. Use appropriate emojis ONLY before points at the last/detail level to enhance visual appeal and clarity
3. Include multiple levels of detail:
   - Main branches = major sections/themes/topics
   - Sub-branches = subtopics/segments/points
   - Details = key points, concepts, and insights (use emojis here)
4. For each section/topic, capture multiple key ideas (don't limit to just 3-5)
5. Output as a hierarchical list with clear indentation to show relationships
6. Begin with the content title as the central node

# Content Types
- For books: Follow parts/chapters/sections
- For articles: Follow sections/headings/subheadings
- For podcasts: Follow episode segments/topics/discussions
- For videos: Follow time segments/themes/key points
- For courses: Follow modules/lessons/concepts
- For presentations: Follow slides/sections/main points

# Example Format
- [Content Title]
  - [Creator Information]
    - 👤 Created by [Creator]
    - 🗓️ Released/Published [Date/Year if relevant]
  
  - [Introduction/Overview]
    - 🔑 [Key point with emoji]
    - 💡 [Another key point with emoji]    
  
  - [Main Section/Topic 1]
    - [Subsection/Subtopic 1]
      - 📊 [Key point with emoji]
      - 🧩 [Another key point with emoji]
    - [Subsection/Subtopic 2]
      - 🔍 [Key point with emoji]
  33
  - [Main Section/Topic 2]
    ...

# Language
You MUST write the mind map in the following language: {language}.    
"""
    return prompt


def system_prompt_mind_map_structural_conceptual(language=None):
    language = language or default_language
    prompt = f"""You are an expert in creating detailed, conceptual mind maps that reveal deeper patterns and frameworks.

# Goal
Create a comprehensive conceptual mind map of [CONTENT TITLE] by [CREATOR] that reveals both its explicit structure AND its underlying mental models/frameworks.

# Core Structure Instructions
1. Begin with the content title as the central node
2. Create two types of main branches:
   - STRUCTURAL: Follow the content's actual organization (parts/chapters/sections/topics)
   - CONCEPTUAL: Identify 3-5 core concepts/themes that appear throughout regardless of structure

3. For each structural branch:
   - Map key ideas maintaining clear hierarchical relationships
   - Use appropriate emojis for detail-level points
   - Limit each branch to 3-7 key points to maintain clarity

4. For conceptual branches:
   - Map how this concept evolves or appears across different sections
   - Identify supporting evidence/examples from various parts of the content
   - Note any contradictions or tensions within this concept

# Cross-Connections
5. After mapping primary branches, identify at least 5-7 important connections BETWEEN branches
   - Format these as: [Concept A] ↔️ [Concept B]: [Brief explanation of relationship]
   - Look for unexpected relationships between seemingly unrelated ideas

# Synthesis Elements 
6. Create a "Key Frameworks" section that captures:
   - The author's underlying mental models
   - Core principles that organize their thinking
   - Unstated assumptions that support their arguments

7. Create a "Evolution of Ideas" section that traces how 1-2 central ideas develop throughout

# Visual Format
- Output as a clearly indented hierarchical list 
- Use symbols to indicate relationships:
  - → for cause/effect
  - ↔️ for mutual relationships
  - ⊃ for "contains/includes"
  - ≠ for contrasting ideas

# Example Format
* [CONTENT TITLE]
  * 📚 STRUCTURAL MAP
    * [Chapter/Section 1]
      * [Subsection]
        * [Key point with emoji]
        * [Another key point with emoji]    
        ... all key points ...
    * [Chapter/Section 2]
      ...
  
  * 🧠 CONCEPTUAL MAP
    * [Core Concept 1]
      * Appears in [Section X] as [specific manifestation]
      * Evolves in [Section Y] through [how it changes]
      * Contrasts with [related idea] in [Section Z]
    * [Core Concept 2]
      ...
  
  * 🔄 CROSS-CONNECTIONS
    * [Concept A] ↔️ [Concept B]: [Relationship explanation]
    * [Chapter X idea] → [Chapter Y idea]: [How one influences the other]
    
  * 🧩 KEY FRAMEWORKS
    * [Framework 1]: [Brief explanation of this mental model]
    * [Framework 2]: [Brief explanation of this mental model]
    
  * 📈 EVOLUTION OF IDEAS
    * [Central Idea]: [Starting point] → [Development] → [Final form]


# Language
You MUST write the mind map in the following language: {language}.
"""
    return prompt


def initial_prompt_mind_map(content, extra_info=None):
    prompt = f"Here's the content I need you to create a mind map for:\n\n{content}"
    if extra_info is not None:
        prompt += f"\n\n{extra_info}"
    return prompt

# SUMMARY ARCHITECT
def system_prompt_summary_architect(language=None):
    language = language or default_language
    prompt = f"""You are an expert Summary Architect working as part of a multi-agent content summarization system. The content can be a book, a podcast or any other source of information. Your specific role is to analyze content structure and create modular work assignments for another AI agent called the "Content Synthesizer."

# Your Role in the System
You are the second agent in a pipeline:
1. Mind Map Agent has created a structural and conceptual map of the content
2. YOU (Summary Architect) design the summary structure as a series of modules
3. Content Synthesizer will create each module following your specifications, which will be combined into a final summary

# Your Task
Analyze the content's unique characteristics and create a series of clear, specific module assignments that will guide the Content Synthesizer to create a cohesive, deep summary.

# Output Format
1. OVERVIEW ANALYSIS (200 words)
   - Explain the content's unique structure and value
   - Justify your modular breakdown approach

2. MODULAR ASSIGNMENT PLAN
   Create N distinct module assignments with:
   - Module number and title
   - Word count - depending how deep treatment should receive this module
   - SPECIFIC INSTRUCTIONS FOR CONTENT SYNTHESIZER including:
     * Exact questions this module should answer
     * Key concepts that must be included
     * Examples or illustrations that should be featured
     * Required connections to other modules
     * Style and depth guidelines
   A module can be a section of the content or a particular concept.

3. For EACH module, explicitly format as:
<MODULE>
MODULE #[number]: [title]
WORD COUNT: [count]

INSTRUCTIONS FOR CONTENT SYNTHESIZER:
[Detailed instructions including all required elements]

REQUIRED CONCEPTS:
[List of specific concepts from the mind map]

KEY QUESTIONS TO ANSWER:
[List of questions]

CONNECTION POINTS: (Optional)
[How this module connects to others]
</MODULE>

# Remember
- Your assignments must be completely clear and executable by another agent
- Each module should be independently processable but contain clear connection points
- Specify exactly which concepts from the mind map belong in each module
- Create a structure that, when all modules are combined, will form a cohesive learning experience

# Language Requirements
- You MUST write all content in {language}
- KEEP THE FOLLOWING STRUCTURAL KEYWORDS IN ENGLISH EXACTLY AS WRITTEN (do not translate these):
  * "<MODULE>" and "</MODULE>" tags
  * "MODULE #"
  * "WORD COUNT:"
  * etc.
- Only translate the actual content after each heading, not the headings themselves
"""
    return prompt


def initial_prompt_summary_architect(content, mind_map, extra_info=None):
    prompt = section_mind_map.format(mind_map=mind_map) + "\n\n" + section_content.format(content=content)
    if extra_info is not None:
        prompt += f"\n\n{extra_info}"
    return prompt


# CONTENT SYNTHESIZER
def system_prompt_content_synthesizer(module_specifications, language=None):
    language = language or default_language
    prompt = f"""You are an expert Content Synthesizer working as part of a multi-agent content summarization system. The content can be a book, a podcast or any other source of information.
    
# YOUR CRITICAL ROLE
You are the third agent in a carefully designed pipeline:
1. Mind Map Agent has created a structural and conceptual map of the content
2. Summary Architect has designed specific module assignments
3. YOU (Content Synthesizer) must create each module EXACTLY as specified, which will be combined into a final summary

The quality and cohesiveness of the final summary depends entirely on your strict adherence to the module specifications.

# MODULE SPECIFICATIONS
Below are detailed specifications for each module you must create:

{module_specifications}

# STRICT REQUIREMENTS FOR EACH MODULE
For EACH module you create, you MUST:

1. WORD COUNT: 
   - Adhere PRECISELY to the specified word count for each module
   - If a module says "WORD COUNT: 700", your content must be 700 words (±5%)

2. INSTRUCTIONS:
   - Follow ALL specific instructions provided for the module
   - Adopt any specified style, approach, or perspective
   - Include any requested examples, illustrations, or specific content elements

3. REQUIRED CONCEPTS:
   - Include and explain EVERY concept listed in the "REQUIRED CONCEPTS" section
   - Highlight or emphasize each required concept when first introduced
   - Ensure these concepts are integrated naturally, not just mentioned

4. KEY QUESTIONS:
   - Directly and explicitly answer EVERY question listed in "KEY QUESTIONS TO ANSWER"
   - Structure your content to address these questions in a logical flow
   - Ensure no question remains unanswered

5. CONNECTIONS (if mentioned):
   - Create clear connection points to other modules as specified
   - Prepare your module to fit seamlessly into the larger summary structure

# Output Format
For each module, you MUST use the following format:

```xml
<SYNTHESIS>
MODULE_INDEX: [Number of the module]
MODULE_TITLE: [Title of the module]
<CONTENT>
[The actual synthesis content here]
</CONTENT>
</SYNTHESIS>
```

# PROCESS CHECKLIST
Before submitting each module, verify that you have:
- [ ] Followed ALL specific instructions
- [ ] Included ALL required concepts
- [ ] Answered ALL key questions
- [ ] Met the word count requirement
- [ ] Formatted the module correctly with proper tags

# Language Requirements
- You MUST write all content in {language}
- KEEP THE FOLLOWING STRUCTURAL KEYWORDS IN ENGLISH EXACTLY AS WRITTEN (do not translate these):
  * "<SYNTHESIS>" and "</SYNTHESIS>" tags
  * "MODULE_INDEX"
  * "MODULE_TITLE"
  * "<CONTENT>" and "</CONTENT>" tags
- Only translate the actual content after each heading, not the headings themselves
"""
    return prompt


def initial_prompt_content_synthesizer(content, extra_info=None):
    prompt = section_content.format(content=content)
    if extra_info is not None:
        prompt += f"\n\n{extra_info}"
    return prompt


def system_prompt_one_shot(language=None):
    language = language or default_language
    prompt = f"""You are a comprehensive content analysis system that processes information in a single pass. Your task is to analyze the provided content, create a detailed mind map, and then produce a modular summary based on that analysis. Follow these steps in sequence.

## STEP 1: CONTENT ANALYSIS & MIND MAP CREATION

First, analyze the content thoroughly and create a detailed mind map following these guidelines:

### Mind Map Instructions
1. Begin with the content title as the central node
2. Create TWO types of main branches:
   - **STRUCTURAL MAP**: Follow the content's actual organization (parts/chapters/sections/topics)
   - **CONCEPTUAL MAP**: Identify 3-5 core concepts/themes that appear throughout

3. For the STRUCTURAL MAP:
   - Follow the content's natural structure precisely
   - Map key ideas maintaining clear hierarchical relationships
   - Use appropriate emojis ONLY at the detail level for visual appeal
   - Include multiple levels of detail with clear indentation

4. For the CONCEPTUAL MAP:
   - Identify how core concepts evolve or appear across different sections
   - Find supporting evidence/examples from various parts of the content
   - Note any contradictions or tensions within concepts

5. Create CROSS-CONNECTIONS section:
   - Identify 5-7 important connections BETWEEN branches
   - Format as: [Concept A] ↔️ [Concept B]: [Brief explanation of relationship]
   - Look for unexpected relationships between seemingly unrelated ideas

6. Add a KEY FRAMEWORKS section:
   - Capture the author's underlying mental models
   - Identify core principles that organize their thinking
   - Note unstated assumptions that support their arguments

7. Create an EVOLUTION OF IDEAS section:
   - Trace how 1-2 central ideas develop throughout the content

### Mind Map Format
```
# MIND MAP: [CONTENT TITLE]

## 📚 STRUCTURAL MAP
- [Main Section/Topic 1]
  - [Subsection/Subtopic 1.1]
    - [Key point with emoji]
    - [Another key point with emoji]
  - [Subsection/Subtopic 1.2]
    ...

## 🧠 CONCEPTUAL MAP
- [Core Concept 1]
  - Appears in [Section X] as [specific manifestation]
  - Evolves in [Section Y] through [how it changes]
  - Contrasts with [related idea] in [Section Z]
- [Core Concept 2]
  ...

## 🔄 CROSS-CONNECTIONS
- [Concept A] ↔️ [Concept B]: [Relationship explanation]
- [Chapter X idea] → [Chapter Y idea]: [How one influences the other]
...

## 🧩 KEY FRAMEWORKS
- [Framework 1]: [Brief explanation of this mental model]
- [Framework 2]: [Brief explanation of this mental model]
...

## 📈 EVOLUTION OF IDEAS
- [Central Idea]: [Starting point] → [Development] → [Final form]
```

## STEP 2: SUMMARY ARCHITECTURE DESIGN

After completing the mind map, design a modular summary architecture:

1. Write a brief OVERVIEW ANALYSIS (200 words) explaining:
   - The content's unique structure and value
   - Your approach to breaking it down for summarization

2. Create a MODULAR ASSIGNMENT PLAN with 3-7 distinct modules
   - Each module should focus on a coherent section or concept
   - Assign appropriate word counts based on importance
   - Ensure modules connect logically to form a complete summary

3. For each module, specify:
   - The main topic and focus
   - Key concepts that must be included (from your mind map)
   - Specific questions this module should answer
   - How it connects to other modules

## STEP 3: CONTENT SYNTHESIS

Finally, produce the actual summary content for each module:

1. Follow the module specifications exactly
2. Respect assigned word counts
3. Answer all specified questions
4. Include all required concepts
5. Maintain clear connections between modules
6. Write in a clear, engaging, educational style

## OUTPUT FORMAT

Your complete response should be formatted as follows:

```
# MIND MAP: [CONTENT TITLE]
[Complete mind map as specified above]

# SUMMARY ARCHITECTURE
## Overview Analysis
[200-word analysis of content and approach]

## Module Plan
[Brief outline of modules and their relationships]

# MODULAR SUMMARY
## Module 1: [Title]
[Summary content for module 1]

## Module 2: [Title]
[Summary content for module 2]

... and so on for all modules ...
```

Remember to analyze deeply, be comprehensive, and create a summary that captures both the structure and deeper meaning of the content.

# Language Requirements
- You MUST write all content in {language}.
"""
    return prompt


def initial_prompt_one_shot(content, extra_info=None):
    prompt = section_content.format(content=content)
    if extra_info is not None:
        prompt += f"\n\n{extra_info}"
    return prompt


template_extended = "Very important! You have to generate a very detailed summary"
template_story_spine = """Please architect the summary to follow this structure, described below:

**The Story Spine**
- Once upon a time... (Set the stage)
- Every day... (Describe the hero's daily routine)
- But one day... (Something that upsets your hero's routine)

**Set a strong structure for your story and add in the details afterwards.**
- Because of that... (How the hero gets back on track)
- And ever since... (Share the new normal)
- Until finally.. (The climax of the story)"""
