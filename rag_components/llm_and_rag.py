# rag_components/llm_and_rag.py
from django.conf import settings
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq   # or your chosen LLM wrapper
from .vector_store_update import get_retriever, get_vector_store

def get_prompt_template():
    template = """
You are a **Rural Health Assistant**, providing **friendly, professional, and accurate health guidance** based on the information in the provided context. Follow these instructions:

1. Answer strictly using the context; do NOT invent facts.
2. If context lacks the answer, respond: "I don't have enough information to answer this question."
3. Keep answers clear and simple.
4. Highlight key actions in bold.
5. Suggest consulting a healthcare professional if needed.
Context:
{context}

User question:
{question}

Answer:
"""
    return PromptTemplate(input_variables=["context", "question"], template=template)

def get_llm():
    rag_config = getattr(settings, "RAG_CONFIG", {})
    model_name = rag_config.get("LLM_MODEL", "llama-3.1-8b-instant")
    temperature = rag_config.get("TEMPERATURE", 0.1)
    max_tokens = rag_config.get("MAX_TOKENS", 2048)
    api_key = getattr(settings, "GROQ_API_KEY", None)
    if not api_key:
        # It's better to raise than to fail silently
        raise RuntimeError("GROQ_API_KEY (or the configured LLM_API_KEY) is missing in settings")
    return ChatGroq(model=model_name, temperature=temperature, max_tokens=max_tokens, groq_api_key=api_key)

def get_rag_response(question: str, k: int = None):
    """
    Returns {"answer": ..., "sources": [ {title, content, metadata}, ... ] }
    """
    try:
        retriever = get_retriever(k=k)
        llm = get_llm()
        prompt = get_prompt_template()

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )

        # Call chain and get both answer and source_documents
        result = qa_chain.invoke({"query": question})
        # result usually has keys 'result' and 'source_documents' depending on langchain version
        answer = result.get("result") or result.get("output_text") or ""
        raw_sources = result.get("source_documents", [])

        # Build clean sources list
        sources = []
        for doc in raw_sources:
            sources.append({
                "title": doc.metadata.get("source", "Unknown"),
                "content": (doc.page_content[:200] + "...") if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata
            })
        print(f"RAG answer: {answer} Sources: {sources}")
        return {"answer": answer, "sources": sources}
    except Exception as e:
        print(f"RAG error: {e}")
        return {"answer": "I don't have enough information to answer this question.", "sources": []}
