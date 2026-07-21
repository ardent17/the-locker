import hashlib
import json
import os
import tempfile
import uuid
import base64
from datetime import datetime

import streamlit as st
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredExcelLoader,
)
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

def set_locker_background():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(base_dir, "assets", "locker.jpg")

    if not os.path.exists(image_path):
        return

    with open(image_path, "rb") as image_file:
        locker_bg = base64.b64encode(image_file.read()).decode()

    background_css = f"""
    <style>
    .stApp {{
        background-image:
            linear-gradient(rgba(14, 25, 31, 0.45), rgba(14, 25, 31, 0.70)),
            url("data:image/jpeg;base64,{locker_bg}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(background_css, unsafe_allow_html=True)

st.set_page_config(
    page_title="The Locker",
    page_icon="🔒",
    layout="wide",
)

set_locker_background()


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --locker-blue: #5f7f92;
    --locker-dark: #1d2b34;
    --locker-shadow: #10191f;
    --locker-line: rgba(220, 238, 244, 0.38);
    --paper: #f5efce;
    --ink: #172126;
    --sticker-red: #c5483e;
    --status-green: #bbff76;
}

.stApp {
    color: #eff8fa;
    font-family: "IBM Plex Mono", monospace;
}

.block-container {
    max-width: 1060px;
    padding-top: 3.5rem;
    padding-bottom: 4rem;
}

h1 {
    color: #f8f6e8 !important;
    font-family: "Space Grotesk", sans-serif;
    font-size: clamp(2.6rem, 7vw, 5.7rem) !important;
    font-weight: 700 !important;
    letter-spacing: -0.08em;
    line-height: 0.86;
    text-shadow: 4px 4px 0 var(--locker-shadow);
    margin-bottom: 0.65rem !important;
}

[data-testid="stCaptionContainer"] {
    color: #d7ecf1 !important;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
}

[data-testid="stFileUploader"] {
    background: rgba(20, 34, 42, 0.83);
    border: 2px solid var(--locker-line);
    border-radius: 8px;
    box-shadow: 7px 7px 0 var(--locker-shadow);
    padding: 1.1rem;
}

[data-testid="stFileUploader"] section {
    border: 2px dashed rgba(211, 239, 246, 0.55) !important;
    border-radius: 4px !important;
    background: rgba(122, 160, 178, 0.12) !important;
}

[data-testid="stFileUploaderFile"] {
    color: #eff8fa !important;
}

[data-testid="stFileUploaderFileName"] {
    color: #f8f6e8 !important;
}

[data-testid="stFileUploaderDropzone"] {
    color: #eff8fa;
}

[data-testid="stFileUploaderDropzone"] button {
    background: #f5efce !important;
    color: var(--ink) !important;
    border: 2px solid #c5b57d !important;
    font-family: "IBM Plex Mono", monospace !important;
    font-weight: 600;
}

[data-testid="stFileUploaderDropzoneInstructions"] div,
[data-testid="stFileUploaderDropzoneInstructions"] span {
    color: #d7ecf1 !important;
}

.stButton > button, .stDownloadButton > button {
    background: var(--sticker-red);
    border: 2px solid #f7c0aa;
    border-radius: 4px;
    box-shadow: 3px 3px 0 #5f1d1c;
    color: white;
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    background: #e35d4f;
    border-color: #fff0dc;
    transform: translate(1px, 1px);
    box-shadow: 2px 2px 0 #5f1d1c;
}

.stButton > button:disabled,
.stButton > button:disabled:hover,
.stDownloadButton > button:disabled,
.stDownloadButton > button:disabled:hover {
    background: rgba(197, 72, 62, 0.35) !important;
    color: #f8e8e5 !important;
    border: 2px solid rgba(247, 192, 170, 0.4) !important;
    opacity: 1 !important;
}            

[data-testid="stChatMessage"] {
    background: var(--paper);
    border: 2px solid #c5b57d;
    border-radius: 3px;
    box-shadow: 5px 5px 0 rgba(18, 29, 35, 0.58);
    color: var(--ink);
    margin-bottom: 1rem;
}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] div {
    color: var(--ink);
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: #e7f2f4;
    border-color: #a5c9d3;
}

[data-testid="stExpander"] {
    background: rgba(16, 28, 35, 0.82);
    border: 1px solid var(--locker-line);
    border-radius: 4px;
}

[data-testid="stExpander"] summary {
    color: #f5f4e5;
    font-weight: 600;
    letter-spacing: 0.04em;
}

[data-testid="stCodeBlock"] {
    border: 1px solid rgba(202, 225, 229, 0.4);
}

[data-testid="stChatInput"] textarea {
    background: #f5efce !important;
    border: 2px solid #c5b57d !important;
    border-radius: 3px !important;
    color: var(--ink) !important;
    font-family: "IBM Plex Mono", monospace !important;
}

textarea, .stTextInput input {
    background: #f5efce !important;
    border: 2px solid #c5b57d !important;
    border-radius: 3px !important;
    color: var(--ink) !important;
    font-family: "IBM Plex Mono", monospace !important;
}

[data-testid="stAlert"] {
    border-radius: 4px;
    font-family: "IBM Plex Mono", monospace;
    background: rgba(16, 28, 35, 0.88) !important;
    border: 1px solid var(--locker-line);
}

[data-testid="stAlert"] p {
    color: #eff8fa !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(20, 34, 42, 0.83);
    border: 2px solid var(--locker-line);
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    color: #eff8fa;
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.78rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.stTabs [aria-selected="true"] {
    background: rgba(122, 160, 178, 0.22) !important;
    color: #f8f6e8 !important;
}
</style>
""", unsafe_allow_html=True)


def initialize_state():
    defaults = {
        "chat_history": [],
        "chat_log": [],
        "file_id": None,
        "active_filename": None,
        "rag_chain": None,
        "vector_store": None,
        "collection_name": None,
        "uploader_key": 0,
        "paste_key": 0,
        "chunk_count": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def empty_locker():
    vector_store = st.session_state.get("vector_store")

    if vector_store is not None:
        try:
            vector_store.delete_collection()
        except Exception:
            pass

    st.session_state.chat_history = []
    st.session_state.chat_log = []
    st.session_state.file_id = None
    st.session_state.active_filename = None
    st.session_state.rag_chain = None
    st.session_state.vector_store = None
    st.session_state.collection_name = None
    st.session_state.chunk_count = 0

    # Changing these keys clears the visible uploader / paste box.
    st.session_state.uploader_key += 1
    st.session_state.paste_key += 1


def load_json_documents(file_path: str):
    """Split JSON into one Document per top-level item instead of
    stringifying the entire structure into a single blob. This keeps
    chunks (and therefore receipts) meaningful for arrays/objects of
    any real size."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = []

    def add_doc(content, path_label):
        if isinstance(content, (dict, list)):
            text = json.dumps(content, indent=2, ensure_ascii=False)
        else:
            text = str(content)
        if text.strip():
            documents.append(
                Document(page_content=text, metadata={"json_path": path_label})
            )

    if isinstance(data, list):
        for i, item in enumerate(data):
            add_doc(item, f"[{i}]")
    elif isinstance(data, dict):
        for key, value in data.items():
            add_doc(value, str(key))
    else:
        add_doc(data, "root")

    if not documents:
        # Fall back to a single document rather than failing outright.
        add_doc(data, "root")

    return documents


def load_documents(file_path: str, extension: str):
    if extension == "pdf":
        return PyPDFLoader(file_path).load()

    if extension == "json":
        return load_json_documents(file_path)

    if extension == "docx":
        return Docx2txtLoader(file_path).load()

    if extension == "xlsx":
        return UnstructuredExcelLoader(
            file_path,
            mode="elements",
        ).load()

    if extension == "txt":
        return TextLoader(
            file_path,
            encoding="utf-8",
        ).load()

    raise ValueError(f"Unsupported file type: {extension}")


def build_rag_chain(docs, filename: str, file_id: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(docs)

    if not chunks:
        raise ValueError("No readable text was extracted from this source.")

    # Add provenance before vectors are created. Only set source_file if
    # the loader didn't already tag one (paste-text documents set it
    # up front so every chunk inherits the label).
    for index, chunk in enumerate(chunks):
        chunk.metadata.setdefault("source_file", filename)
        chunk.metadata["file_id"] = file_id
        chunk.metadata["chunk_number"] = index + 1

    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # Every upload receives a completely new collection.
    collection_name = f"locker_{uuid.uuid4().hex}"

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
    )

    retriever = vector_store.as_retriever(
        search_kwargs={"k": 3},
    )

    llm = ChatOllama(
        model="llama3.2",
        temperature=0,
    )

    contextualize_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Rewrite the latest user question as a standalone document-search "
            "query using conversation history only to resolve references. "
            "Do not answer it and do not add facts."
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    history_aware_retriever = create_history_aware_retriever(
        llm,
        retriever,
        contextualize_prompt,
    )

    qa_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
        "Answer the user's question using only the retrieved document excerpts "
        "below. You can count, summarize, compare, and combine information from "
        "multiple excerpts when the answer is present in them.\n\n"
        "If the excerpts do not contain the answer, say: "
        "\"“I couldn't verify that from the retrieved excerpts.”\"\n\n"
        "Retrieved excerpts:\n{context}"
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(
        llm,
        qa_prompt,
    )

    rag_chain = create_retrieval_chain(
        history_aware_retriever,
        question_answer_chain,
    )

    return rag_chain, vector_store, collection_name, len(chunks)


def format_source(document):
    metadata = document.metadata
    filename = metadata.get("source_file", "Unknown file")
    page = metadata.get("page")
    json_path = metadata.get("json_path")
    chunk_number = metadata.get("chunk_number", "?")

    location_bits = []
    if page is not None:
        location_bits.append(f"page {page + 1}")
    if json_path is not None:
        location_bits.append(f"path {json_path}")
    location_bits.append(f"chunk {chunk_number}")

    return f"{filename} · " + " · ".join(location_bits)


def process_new_source(docs, filename: str, file_id: str):
    """Reset the locker and index a new source (uploaded file or
    pasted text). Single active source at a time, by design."""

    if st.session_state.vector_store is not None:
        try:
            st.session_state.vector_store.delete_collection()
        except Exception:
            pass

    st.session_state.chat_history = []
    st.session_state.chat_log = []
    st.session_state.file_id = file_id
    st.session_state.active_filename = filename
    st.session_state.rag_chain = None
    st.session_state.vector_store = None
    st.session_state.collection_name = None

    with st.spinner("Putting it in the locker and indexing it..."):
        try:
            (
                rag_chain,
                vector_store,
                collection_name,
                chunk_count,
            ) = build_rag_chain(
                docs=docs,
                filename=filename,
                file_id=file_id,
            )

            st.session_state.rag_chain = rag_chain
            st.session_state.vector_store = vector_store
            st.session_state.collection_name = collection_name
            st.session_state.chunk_count = chunk_count

        except Exception as exc:
            empty_locker()
            st.error(f"Could not process this source: {exc}")
            st.stop()

    st.success(f"STORED: {filename} ({st.session_state.chunk_count} chunks)")
    st.rerun()


def build_export_markdown():
    lines = [
        "# The Locker — chat export",
        f"Active file: {st.session_state.active_filename}",
        f"Exported: {datetime.now().isoformat(timespec='seconds')}",
        f"Chunks indexed: {st.session_state.chunk_count}",
        "",
        "---",
        "",
    ]

    for i, turn in enumerate(st.session_state.chat_log, start=1):
        lines.append(f"## Q{i}")
        lines.append("")
        lines.append(f"**Question:** {turn['query']}")
        lines.append("")
        lines.append(f"**Answer:** {turn['answer']}")
        lines.append("")

        if turn["sources"]:
            lines.append("**Receipts:**")
            lines.append("")
            for j, src in enumerate(turn["sources"], start=1):
                lines.append(f"- Receipt {j}: {src['label']}")
                lines.append("")
                lines.append("  ```")
                for excerpt_line in src["excerpt"].splitlines():
                    lines.append(f"  {excerpt_line}")
                lines.append("  ```")
                lines.append("")
        else:
            lines.append("_No receipts retrieved for this answer._")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


initialize_state()

st.title("THE LOCKER 🔒")
st.caption("PRIVATE FILES. PRIVATE ANSWERS. NO OLD RECEIPTS.")

header_left, header_mid, header_right = st.columns([3, 1, 1])

with header_left:
    if st.session_state.active_filename:
        st.success(f"ACTIVE FILE: {st.session_state.active_filename}")
    else:
        st.info("LOCKER EMPTY")

with header_mid:
    st.download_button(
        "Export chat",
        data=build_export_markdown() if st.session_state.chat_log else "",
        file_name=f"locker_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
        use_container_width=True,
        disabled=not st.session_state.chat_log,
    )

with header_right:
    if st.button(
        "Empty locker",
        use_container_width=True,
        disabled=st.session_state.file_id is None,
    ):
        empty_locker()
        st.rerun()

st.divider()

tab_upload, tab_paste = st.tabs(["📁 Upload file", "📝 Paste text"])

with tab_upload:
    uploaded_file = st.file_uploader(
        "Drop a file in the locker",
        type=["pdf", "json", "docx", "xlsx", "txt"],
        key=f"locker_uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        current_file_id = hashlib.sha256(file_bytes).hexdigest()

        if st.session_state.file_id != current_file_id:
            extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
            temp_path = None

            try:
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=f".{extension}",
                    prefix="the_locker_",
                ) as temp_file:
                    temp_file.write(file_bytes)
                    temp_path = temp_file.name

                docs = load_documents(temp_path, extension)

            except Exception as exc:
                st.error(f"Could not read this file: {exc}")
                st.stop()

            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

            process_new_source(docs, uploaded_file.name, current_file_id)

with tab_paste:
    pasted_label = st.text_input(
        "Label (optional)",
        placeholder="e.g. meeting-notes",
        key=f"locker_paste_label_{st.session_state.paste_key}",
    )
    pasted_text = st.text_area(
        "Paste text to store in the locker",
        height=220,
        key=f"locker_paste_text_{st.session_state.paste_key}",
        label_visibility="collapsed",
        placeholder="Paste text here — notes, a transcript, an email thread, anything.",
    )

    if st.button("Store text in locker"):
        if not pasted_text.strip():
            st.warning("Paste some text first.")
        else:
            current_file_id = hashlib.sha256(pasted_text.encode("utf-8")).hexdigest()

            if st.session_state.file_id == current_file_id:
                st.info("This text is already the active locker content.")
            else:
                filename = (
                    pasted_label.strip()
                    or f"pasted_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                )
                if not filename.lower().endswith(".txt"):
                    filename = f"{filename}.txt"

                docs = [
                    Document(
                        page_content=pasted_text,
                        metadata={"source_file": filename},
                    )
                ]
                process_new_source(docs, filename, current_file_id)

if st.session_state.file_id is None:
    st.markdown(
        """
        ### Locker empty

        Drop in a PDF, JSON export, DOCX, XLSX, or TXT file — or paste
        text directly above.

        The Locker indexes one active source at a time. Storing a new
        file or paste clears the old conversation and deletes its
        vector collection.
        """
    )
    st.stop()

st.divider()

with st.expander("Locker status", expanded=False):
    st.code(
        "\n".join([
            f"active_file: {st.session_state.active_filename}",
            f"file_hash: {st.session_state.file_id[:12]}...",
            f"collection: {st.session_state.collection_name}",
            f"chunks: {st.session_state.get('chunk_count', 0)}",
            "mode: local only",
        ])
    )

for message in st.session_state.chat_history:
    role = "user" if isinstance(message, HumanMessage) else "assistant"

    with st.chat_message(role):
        st.write(message.content)

if user_query := st.chat_input("Ask something about the file..."):
    with st.chat_message("user"):
        st.write(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Checking the locker..."):
            try:
                response = st.session_state.rag_chain.invoke({
                    "input": user_query,
                    "chat_history": st.session_state.chat_history,
                })

                answer = response["answer"]
                retrieved_docs = response.get("context", [])

                st.write(answer)

                if retrieved_docs:
                    source_labels = []
                    for doc in retrieved_docs:
                        label = format_source(doc)
                        if label not in source_labels:
                            source_labels.append(label)

                    st.caption("Receipts: " + " | ".join(source_labels))

                    with st.expander("Behind the locker door"):
                        st.caption(
                            "These are the chunks retrieved for this answer. "
                            "They are evidence, not necessarily proof."
                        )

                        for index, doc in enumerate(retrieved_docs, start=1):
                            st.markdown(f"**Receipt {index}: {format_source(doc)}**")
                            st.code(doc.page_content[:1500])

                else:
                    st.caption("No retrieved receipts returned.")

            except Exception as exc:
                answer = f"Locker error: {exc}"
                retrieved_docs = []
                st.error(answer)

    st.session_state.chat_history.extend([
        HumanMessage(content=user_query),
        AIMessage(content=answer),
    ])

    st.session_state.chat_log.append({
        "query": user_query,
        "answer": answer,
        "sources": [
            {"label": format_source(doc), "excerpt": doc.page_content[:1500]}
            for doc in retrieved_docs
        ],
    })