# rag_components/vector_store_update.py
import os
from typing import List
from django.conf import settings

# langchain imports (adjust to installed provider libs)
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# helpers
def _get_config(key, default=None):
    return getattr(settings, "RAG_CONFIG", {}).get(key, default)

####################
# Loading & splitting
####################
def load_file_with_metadata(file_path: str, source_name: str = None, doc_id: str = None):
    """Load file and attach metadata."""
    filename = os.path.basename(file_path)
    if filename.lower().endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif filename.lower().endswith(".txt"):
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        # unsupported -> return empty
        return []

    docs = loader.load()
    for d in docs:
        # attach helpful metadata
        d.metadata["source"] = source_name or filename
        d.metadata["doc_id"] = doc_id
        d.metadata["filename"] = filename
    return docs

def split_documents(documents: List):
    chunk_size = _get_config("CHUNK_SIZE", 1000)
    chunk_overlap = _get_config("CHUNK_OVERLAP", 200)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    return splitter.split_documents(documents)

####################
# Embeddings & Chroma
####################
def get_embeddings():
    model_name = _get_config("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    return HuggingFaceEmbeddings(model_name=model_name)

def get_vector_db_path():
    return _get_config("VECTOR_DB_PATH", os.path.join(settings.BASE_DIR, "vector_db"))

def get_vector_store():
    path = get_vector_db_path()
    os.makedirs(path, exist_ok=True)
    embeddings = get_embeddings()
    return Chroma(persist_directory=path, embedding_function=embeddings)

####################
# Incremental ops
####################
def add_file_to_vector_db(file_path: str, doc_id: str, source_name: str = None):
    """
    Load a file, split it into chunks, and add to an existing Chroma store.
    Each chunk has metadata including doc_id to allow deletes.
    """
    path = get_vector_db_path()
    os.makedirs(path, exist_ok=True)
    embeddings = get_embeddings()
    vector_store = get_vector_store()

    docs = load_file_with_metadata(file_path, source_name=source_name, doc_id=doc_id)
    if not docs:
        return vector_store

    chunks = split_documents(docs)
    if not chunks:
        return vector_store

    # add_documents will compute embeddings for only these chunks
    vector_store.add_documents(chunks)
    vector_store.persist()
    return vector_store

def delete_document_vectors_by_doc_id(doc_id: str):
    """
    Delete all vectors whose metadata.doc_id == doc_id.
    Chroma's delete interface accepts metadata filters or ids depending on version;
    we'll try to use metadata-based deletion if available.
    """
    vector_store = get_vector_store()
    # Chroma .delete supports ids or filters; using filter on metadata:
    try:
        # Some Chroma bindings allow: delete(ids=...), some: delete(filter={"doc_id": doc_id})
        vector_store.delete(filter={"doc_id": doc_id})
    except TypeError:
        # fallback: try delete(ids=[...]) if we have stored ids elsewhere (not implemented)
        # If your Chroma version doesn't support filter delete, consider upgrading or storing chunk IDs on ingestion.
        raise
    vector_store.persist()
    return vector_store

####################
# Full rebuild (management command likely)
####################
def rebuild_vector_db_from_media():
    """Rebuild entire vector DB from all files under MEDIA_ROOT/documents."""
    path = get_vector_db_path()
    os.makedirs(path, exist_ok=True)
    embeddings = get_embeddings()

    # collect all docs from media/documents
    upload_dir = os.path.join(settings.MEDIA_ROOT, "documents")
    all_docs = []
    if not os.path.exists(upload_dir):
        return Chroma(persist_directory=path, embedding_function=embeddings)

    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        # If uploaded filenames are UUIDs this filename might not contain readable title; include filename
        docs = load_file_with_metadata(file_path, source_name=filename, doc_id=None)
        all_docs.extend(docs)

    chunks = split_documents(all_docs)
    if chunks:
        return Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=path)
    else:
        return Chroma(persist_directory=path, embedding_function=embeddings)

####################
# Retriever convenience
####################
def get_retriever(k: int = None):
    vs = get_vector_store()
    search_k = k or _get_config("RETRIEVER_K", 3)
    return vs.as_retriever(search_kwargs={"k": search_k})
