# rag_components/llm_and_rag.py
from django.conf import settings
from langchain_core.prompts import PromptTemplate
# from langchain.chains import create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain_groq import ChatGroq   
from langchain_google_genai import ChatGoogleGenerativeAI
from .vector_store_update import get_retriever, get_vector_store
####################
# Prompt Template
def get_prompt_template():
    """Legacy prompt template - maintained for compatibility. 
    Active system uses enhanced prompts in agentic_rag.py"""
    template = """
You are a **Rural Health Medical Assistant** providing evidence-based health information.

## Professional Guidelines

1. **Evidence-Based Responses**
   - Use ONLY information from the provided context

2. **Accuracy Protocol**
   - If context is insufficient, respond: "I don't have enough information in my knowledge base to answer this accurately."

3. **Clear Communication**
   - Provide concise, accessible answers using plain language

4. **Structured Format**
   - Highlight critical actions in **bold**
   - Use numbered lists (1, 2, 3) or bullet points for clarity

5. **Safety Standard**
   - Always recommend: "**For proper diagnosis and treatment, consult a qualified healthcare professional.**"

6. **Professional Warmth**
   - Respond to greetings courteously while maintaining clinical professionalism

---

## Medical Knowledge Base Context
{context}

## Patient Query
{input}

---

**Professional Response:**
"""
    return PromptTemplate(input_variables=["context", "input"], template=template)


def get_llm():
    rag_config = getattr(settings, "RAG_CONFIG", {})
    model_name = rag_config.get("LLM_MODEL", "gemini-2.5-flash")
    temperature = rag_config.get("TEMPERATURE", 0.1)
    max_tokens = rag_config.get("MAX_TOKENS", 2048)
    api_key = getattr(settings, "GOOGLE_GENAI_API_KEY", None)
    if not api_key:
        # It's better to raise than to fail silently
        raise RuntimeError("GOOGLE_GENAI_API_KEY (or the configured LLM_API_KEY) is missing in settings")
    return ChatGoogleGenerativeAI(model=model_name, temperature=temperature, max_tokens=max_tokens, api_key=api_key)

from .agentic_rag import get_agentic_rag_response

def get_rag_response(question: str, chat_history: str = None, user_name: str = None, k: int = None):
    """
    Returns {"answer": ..., "sources": [ {title, content, metadata}, ... ] }
    
    Args:
        question: The user's current question
        chat_history: Formatted string of recent chat history (optional)
        user_name: User's name for personalization (optional)
        k: Number of documents to retrieve (optional, for compatibility)
    """
    # This function now delegates to the new agentic RAG with context awareness
    return get_agentic_rag_response(question, chat_history=chat_history, user_name=user_name)
    
    # # Old implementation preserved for reference (uses new chain methods)
    # """
    # Returns {"answer": ..., "sources": [ {title, content, metadata}, ... ] }
    # """
    # try:
    #     retriever = get_retriever(k=k)
    #     llm = get_llm()
    #     prompt = get_prompt_template()

    #     # Create the document chain
    #     document_chain = create_stuff_documents_chain(llm, prompt)
        
    #     # Create the retrieval chain
    #     retrieval_chain = create_retrieval_chain(retriever, document_chain)

    #     # Call chain and get both answer and source documents
    #     result = retrieval_chain.invoke({"input": question})
        
    #     # result has keys 'answer' and 'context' with the new chain
    #     answer = result.get("answer", "")
    #     raw_sources = result.get("context", [])

    #     # Build clean sources list
    #     sources = []
    #     for doc in raw_sources:
    #         sources.append({
    #             "title": doc.metadata.get("source", "Unknown"),
    #             "content": (doc.page_content[:200] + "...") if len(doc.page_content) > 200 else doc.page_content,
    #             "metadata": doc.metadata
    #         })
    #     print(f"RAG answer: {answer} Sources: {sources}")
    #     return {"answer": answer, "sources": sources}
    # except Exception as e:
    #     print(f"RAG error: {e}")
    #     return {"answer": "I don't have enough information to answer this question.", "sources": []}
