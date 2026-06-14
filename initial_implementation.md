Chinese Learning AI Tutor MVP

You are a senior full-stack developer and LangChain expert. Your task is to build a production-ready, text-based conversational Chinese language learning AI tutor for English speakers using LangChain and Chainlit.

## 1. Project Structure & Tech Stack
Implement the project using Python 3.11+ with the following structure:
chinese-tutor/
├── .env.example
├── requirements.txt   # langchain, langchain-openai, langchain-community, pypinyin, chainlit, python-dotenv
├── dictionary.py     # CEDICT parser & lookup logic
├── utils.py          # Pinyin conversion utility
├── agent.py          # LangChain agent, tools, and memory configuration
└── chainlit_app.py   # Chainlit UI interface

## 2. Core Requirements & Component Guidelines

### A. System Prompt (`agent.py`)
Define a `SYSTEM_PROMPT` string constant enforcing that the agent:
- Acts as a patient, encouraging Chinese language tutor for English speakers.
- Always mixes English explanations with Chinese examples.
- **Strict Rule:** Every Chinese character output MUST include pinyin with tone marks immediately following it in this format: `你好 (nǐ hǎo)`.
- Provides a word-by-word breakdown when asked "how do I say X".
- Corrects user mistakes gently, explaining grammar in English.

### B. Custom Tools
1. **Pinyin Converter (`utils.py`):** Use `pypinyin` (specifically `Style.TONE` or `Style.TONE3` formatted cleanly) to convert arbitrary Chinese text strings into tone-marked pinyin. Wrap this as a LangChain `@tool`.
2. **Dictionary Lookup (`dictionary.py`):** - Parse the standard offline CC-CEDICT file (`cedict_ts.u8`) handling comments (`#`) and extracting simplified characters, traditional characters, pinyin, and definitions.
   - Wrap this lookup as a LangChain `@tool` named `lookup_word` so the agent can pull accurate definitions instead of hallucinating translations.

### C. Agent & Memory Architecture (`agent.py`)
- Use the latest LangChain tool-calling pattern via `create_tool_calling_agent`.
- Use `ChatOpenAI` initialized with model `gpt-4o` and a temperature of `0.5`.
- Equip the agent with `to_pinyin` and `lookup_word`.
- Maintain conversational state via `ConversationBufferMemory` integrated into an `AgentExecutor` wrapper, matching keys with a `MessagesPlaceholder(variable_name="chat_history")` inside a `ChatPromptTemplate`.

### D. User Interface (`chainlit_app.py`)
- Initialize a clean Chainlit chat interface.
- Provide a friendly greeting message on `@cl.on_chat_start`.
- On `@cl.on_message`, asynchronously invoke the LangChain `agent_executor` using the incoming text, routing the final output back to the user.

## 3. Output Expectations
- Generate clean, production-ready, and well-commented code for all 6 files.
- Ensure all modular imports match across files perfectly (e.g., importing tools into `agent.py`).
- Provide a brief `README.md` at the end with terminal setup commands and direct download instructions for the `cedict_ts.u8` file.