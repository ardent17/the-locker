# The Locker 🔒

**Put one file in. Ask questions. Keep your stuff private.**

![The Locker UI](assets/locker-screenshot.png)

If you want to query your own documents without handing them to somebody else's cloud, this is for you. The Locker runs entirely on your machine with local models: teeny weeny environmental footprint, no API key, no upload leaving your computer. It's got a cute locker-themed UI, and a built-in hallucination guardrail, so if the file doesn't actually support an answer, it says so instead of making something up. 

It handles one active document at a time. It shows you what it found and roughly where it came from. It tells you when there's not enough evidence to answer.

> One locker. One active file. No old receipts.

## What this is

A small RAG app built around these principles:

- Keeping documents local
- Keeping one upload from bleeding into the next
- Checking what retrieval actually found
- Admitting when there is not enough evidence to answer
- Making the state of the app visible instead of magical

It only answers from the file you gave it, right now. Nothing is saved, nothing is inherited from past documents.

## What it does

- Takes one PDF, JSON, DOCX, XLSX, or TXT file at a time
- Parses it, chunks it, and embeds it locally
- Uses Ollama for local embeddings and chat
- Creates a fresh Chroma collection for every new upload
- Clears old chat state when the active file changes
- Answers from retrieved document context only
- Lets you inspect retrieved chunks and metadata
- Gives you a normal, explicit refusal when the file does not contain the answer
- Deletes the temporary upload copy after it finishes indexing

## The rule

If The Locker can't find enough evidence in the active file, it should say:

```text
NO RECEIPTS IN THIS LOCKER.

I couldn't verify that from the active file.
```

## Privacy

The point is that this runs on your machine.

- Ollama runs locally
- No cloud LLM API key required
- Each upload is fingerprinted with a local SHA-256 hash — used only to detect when the active file has changed, never transmitted or logged
- Uploads are only written to a temporary local file while they are parsed
- That temporary file is deleted after indexing
- Vector data stays **in memory only** — there's no `persist_directory` set, so every collection is gone the moment the Streamlit process restarts, not just when you hit "Empty Locker"
- Clearing the locker deletes the active collection and chat history

*caveat* That does not mean "secure in every imaginable deployment." Please don't tunnel this onto the public internet (ngrok, port forwarding, etc.) without adding auth in front of it. I believe in you, but still.

## Setup

**Requires Python 3.9+**

### 1. Install Ollama

Install [Ollama](https://ollama.com), then pull the two models this app uses:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

If Ollama is not already running:

```bash
ollama serve
```

### 2. Clone the repo

```bash
git clone https://github.com/ardent17/the-locker.git
cd the-locker
```

### 3. Make a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run it

```bash
streamlit run app.py
```

Streamlit will print a local URL, usually:

```text
http://localhost:8501
```

## Supported files

| File | Extension | Parser |
|---|---|---|
| PDF | `.pdf` | PyPDFLoader |
| JSON | `.json` | JSONLoader |
| Word document | `.docx` | Docx2txtLoader |
| Excel workbook | `.xlsx` | UnstructuredExcelLoader |
| Plain text | `.txt` | TextLoader |

## Test file isolation

This only matters if you've modified `app.py`. On a fresh clone this will always pass — use it to confirm you haven't broken document isolation while changing the upload logic.

Make two files with conflicting information.

`test-a.txt`

```text
The locker combination is 17-04-89.
```

`test-b.txt`

```text
The locker combination is 03-11-02.
```

Then:

1. Upload `test-a.txt`
2. Ask: `What is the locker combination?` or some variation thereof
3. Upload `test-b.txt`
4. Ask the same question
5. Confirm the answer is `03-11-02`
6. Ask for a fact found only in `test-a.txt`
7. The app should refuse, not pull an answer out of the old file

If step 7 fails, isolation's broken: the app answered from a file it should've deleted. How to fix: in `app.py`, find the `if st.session_state.file_id != current_file_id:` block. Right before it builds the new vector store, it should call `st.session_state.vector_store.delete_collection()` and reset `chat_history` to `[]`. If either of those is missing, or happens after the new file is indexed instead of before, that's the bug.

## Stack

- [Streamlit](https://streamlit.io/) for the UI
- [Ollama](https://ollama.com/) for local models
- [LangChain](https://www.langchain.com/) for document loading and retrieval
- [Chroma](https://www.trychroma.com/) for vector search
- `llama3.2` for answers
- `nomic-embed-text` for embeddings

## Project layout

```text
the-locker/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── assets/
```

## V1 checklist

- [x] Local models through Ollama
- [x] One active upload at a time
- [x] PDF, JSON, DOCX, XLSX, and TXT support
- [x] Fresh vector collection per file
- [x] Chat history scoped to the active file
- [x] Temporary-file cleanup
- [x] Source/page metadata beneath answers
- [x] "Behind the locker door" retrieval inspector
- [x] Empty Locker button
- [x] Locker UI skin

## V2

- [ ] Multi-file uploads with synthesis across documents
- [ ] Fix the JSON loader edge case — `jq_schema="."` currently stringifies entire nested JSON blobs into a single chunk instead of splitting sensibly
- [ ] User-selected multi-file collections
- [ ] OCR preprocessing for scanned PDFs
- [ ] Page-level PDF citations
- [ ] Retrieval test suite
- [ ] Export answers with their receipts

## License

MIT