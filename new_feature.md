Skill: Transcript Breakdown & Glossing
1. Skill Overview
Skill Name: transcript_breakdown_and_pinyin

Description: Takes a raw Chinese text transcript or input passage, segments it logically, and outputs a formatted, multi-layered breakdown containing standard Pinyin (with tone marks), an accurate contextual English translation, and key vocabulary notes.

2. Input & Output Schema
Input Requirements
transcript_text (String, Required): The target Chinese text passage or transcript.

granularity (String, Optional): sentence (default) or paragraph. Controls how granularly the text is split.

include_vocab_notes (Boolean, Optional): true (default). Toggles vocabulary annotations.

3. Formatting & Output Rules
For every segmented block, the system MUST output four distinct elements formatted as follows:

Markdown
### [Section Header or Chunk Number]

**Chinese:**
[Original Chinese sentence/clause]

**Pinyin:**
[Full Pinyin with tone marks. Use hyphens for compound words where applicable, e.g., Ōu-Měi]

**Translation:**
[Natural, contextually accurate English translation]

* **[Key Vocabulary]** (*[Pinyin]*): [English Gloss / Meaning in Context]
* **[Grammar Pattern]** (*[Pinyin]*): [Explanation / Usage Note]
Core Execution Rules
Segmentation: Split long transcripts into short, logical chunks (1–2 sentences max per block) to maintain readability.

Pinyin Accuracy:

Use proper Tone Marks (e.g., ā, á, ǎ, à).

Handle polyphonic characters (dōuzì / 多音字) dynamically according to sentence context (e.g., 数 = shǔ for verb "to count", shù for noun "number").

Proper nouns (names, places) should be capitalized in Pinyin (e.g., Zǔ Shān, Qínhuángdǎo).

Vocabulary Selection: Extract 2–4 high-value vocabulary items per block. Prioritize:

Idioms (chengyu) or set phrases (e.g., 说走就走, 一口气).

Slang, homophones, or cultural references (e.g., 1314 / 谐音).

HSK 4–6 / intermediate-to-advanced terms.

Domain-specific terms (e.g., 接驳车, 木栈道).

4. Prompt Template / System Prompt Snippet
If you are wiring this directly into a LangChain PromptTemplate or agent system message, use the following block:

Plaintext
You are an expert Chinese Language Tutor Skill. Your task is to process input text and generate an annotated learning breakdown.

Input Text:
{transcript_text}

Instructions:
1. Divide the input text into short, natural chunks (1-2 sentences).
2. For each chunk, provide:
   - Chinese text
   - Accurately toned Pinyin (capitalizing proper nouns, resolving polyphonic characters like 多音字)
   - Clear, idiomatic English translation
   - Key vocabulary/grammar notes (focusing on useful idioms, colloquialisms, and HSK 4+ words)

Output Formatter:
Use markdown formatting with bold labels and bulleted lists for vocabulary notes. Keep the layout scannable and easy to digest.
5. Python Integration Example (LangChain Tool)
Here is how you can implement this as a python function for a custom LangChain agent setup:

Python
from langchain.core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

@tool
def breakdown_chinese_transcript(transcript_text: str) -> str:
    """
    Parses a Chinese text transcript and returns a segmented breakdown with 
    Pinyin, English translation, and key vocabulary notes for learners.
    """
    system_prompt = """
    You are a Chinese Language Tutor module. Process the provided Chinese text into a structured breakdown.
    For each sentence/chunk, output:
    1. Original Chinese text
    2. Contextually accurate Pinyin with tone marks
    3. Idiomatic English translation
    4. Bulleted list of key vocabulary/idioms with pinyin and definitions.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{text}")
    ])
    
    # Assuming 'llm' is already initialized in your framework (e.g., Ollama, OpenAI)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"text": transcript_text})

6. User Story & Acceptance Criteria

User Story (P0): As a language learner, I want a tool that breaks down Chinese transcripts into short, annotated chunks with accurate tone-marked Pinyin, idiomatic English translations, and 2–4 high-value vocabulary notes per chunk so I can study pronunciation, meaning, and usage efficiently.

Acceptance Criteria:
- The tool accepts `transcript_text` and optional `granularity` and `include_vocab_notes` parameters.
- Output is Markdown containing for each chunk: a header, **Chinese:**, **Pinyin:**, **Translation:**, and a bulleted list of 2–4 vocabulary/grammar notes.
- Pinyin uses tone marks (e.g., ā, á, ǎ, à) and capitalizes proper nouns in Pinyin.
- Polyphonic characters (`多音字`) are resolved according to sentence context (basic heuristics acceptable for MVP).
- When `include_vocab_notes` is false, no vocabulary bullets are present.
- Unit tests mock any external LLM calls and assert output structure and basic Pinyin correctness.

Implementation notes:
- Reuse `utils.chinese_to_pinyin` for base pinyin conversion and extend with a small polyphone resolver.
- Provide a LangChain `@tool` wrapper `breakdown_chinese_transcript` and register it with the agent.
- Add `tests/test_transcript_breakdown.py` with mocked LLM responses to validate formatting and options.

7. Usage Examples

- Quick Python call:

```python
from skills.transcript_breakdown import breakdown_chinese_transcript

text = "你好，我叫王明。很高兴认识你。"
print(breakdown_chinese_transcript(text))
```

- Chainlit action example (simple):

```python
from chainlit import on_message
from skills.transcript_breakdown import breakdown_chinese_transcript

@on_message
async def handler(message):
    result = breakdown_chinese_transcript(message.content)
    await message.send(result)
```

8. Developer Notes

- Files to review: `skills/transcript_breakdown.py`, `utils.py`, `dictionary.py`, `agent.py`, `tests/test_transcript_breakdown.py`.
- Tests: run `uv run pytest`. The project includes a minimal test that asserts Markdown structure and pinyin tone marks; expand tests for polyphone cases and HSK vocab extraction.
- Polyphone resolver: current heuristics cover a small set (e.g., 数, 行, 重, 长). For improved accuracy replace heuristics with context-aware rules or an LLM disambiguator.
- Translation: the current implementation returns dictionary-definition fallbacks. For idiomatic translations, add an LLM prompt chain that returns a `Translation:` string while preserving the Markdown structure.