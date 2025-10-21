# rag_components/agentic_rag.py
import os
from typing import List, TypedDict
from django.conf import settings
from langchain_core.documents import Document
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities import SerpAPIWrapper
from langgraph.graph import StateGraph, END
from .llm_and_rag import get_llm, get_retriever

# --- Environment and Settings ---
os.environ["SERPAPI_API_KEY"] = getattr(settings, "SERPAPI_API_KEY", "")

# --- Graph State Definition ---
class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: The user's question.
        classification: The category of the user's question ("health", "greeting", "off_topic").
        generation: The LLM's generated answer.
        documents: A list of retrieved documents.
        sources: A list of source information for the answer.
    """
    question: str
    classification: str
    generation: str
    documents: List[Document]
    sources: List[dict]

# --- Prompt Templates ---
CLASSIFICATION_PROMPT_TEMPLATE = """
You are a question classifier. Your task is to determine the category of the user's question.
The categories are: "greeting", "health", or "off_topic".

- "greeting": For simple hellos, goodbyes, or salutations.
- "health": For any question related to health, medical advice, symptoms, treatments, wellness, or rural health topics so that the Rural Health Assistant can provide relevant information based on its knowledge base.
- "off_topic": For any question that is not a greeting and not related to health.

User Question:
{question}

Based on the question, what is the single most appropriate category? (greeting, health, or off_topic)
Category:
"""

RAG_PROMPT_TEMPLATE = """
You are the Rural Health Assistant.
Answer the user's health-related question using only the information in the Context below. Do not add outside knowledge or make assumptions.

Decision rule:
- If the Context clearly answers the question, give a short, direct answer.
- If the Context is missing, ambiguous, or contradictory, respond exactly: I don't have enough information to answer this question.

Output rules:
- Start with a concise answer (1–3 sentences).
- Use plain language; define medical terms only if essential.
- Prefer brief bullet points for steps or options.
- Include a small Markdown table only if it clearly improves readability.
- Do not mention the context, documents, or sources in the answer.
- Do not fabricate any facts.

Context (may include multiple documents; use only their content):
{context}

User question:
{question}

Answer:
"""

IMPROVED_FALLBACK_PROMPT_TEMPLATE = """
You are a Rural Health Assistant, a helpful AI.
You were unable to find an answer in your local documents and have performed a web search.
Your task is to answer the user's health-related question based on the provided web search results.

**Instructions:**
1.  Synthesize the information from the search results into a clear, concise, and simple answer.
2.  Focus ONLY on the information directly present in the search results. Do not add external knowledge.
3.  If the search results are ambiguous, contradictory, or do not contain a clear answer to the question, you MUST respond with: "I was unable to find a clear answer from the web search results. For reliable medical information, please consult a healthcare professional."
4.  Always conclude your answer by recommending the user consult a qualified healthcare professional for personal medical advice.

**Web Search Results:**
{context}

**User Question:**
{question}

**Answer:**
"""

# --- Nodes ---
def classify_question(state: GraphState) -> GraphState:
    """Node to classify the user's question."""
    print("---NODE: CLASSIFY QUESTION---")
    question = state["question"]
    
    prompt = PromptTemplate(input_variables=["question"], template=CLASSIFICATION_PROMPT_TEMPLATE)
    llm = get_llm()
    classification_chain = prompt | llm
    
    classification = classification_chain.invoke({"question": question}).content.strip().lower()
    print(f"Question classified as: {classification}")
    return {**state, "classification": classification}

def retrieve_docs(state: GraphState) -> GraphState:
    """Node to retrieve documents from the vector store."""
    print("---NODE: RETRIEVE DOCUMENTS---")
    question = state["question"]
    retriever = get_retriever()
    documents = retriever.invoke(question)
    print(f"Retrieved {len(documents)} documents.")
    return {**state, "documents": documents}

def generate_rag_answer(state: GraphState) -> GraphState:
    """Node to generate an answer using the RAG pipeline."""
    print("---NODE: GENERATE RAG ANSWER---")
    question = state["question"]
    documents = state["documents"]
    
    prompt = PromptTemplate(input_variables=["context", "question"], template=RAG_PROMPT_TEMPLATE)
    llm = get_llm()
    rag_chain = prompt | llm
    
    generation = rag_chain.invoke({"context": documents, "question": question}).content
    
    sources = []
    for doc in documents:
        sources.append({
            "title": doc.metadata.get("source", "Unknown"),
            "content": (doc.page_content[:200] + "...") if len(doc.page_content) > 200 else doc.page_content,
            "metadata": doc.metadata
        })
        
    print("Generated answer from RAG.")
    return {**state, "generation": generation, "sources": sources}

def web_search(state: GraphState) -> GraphState:
    """Node to perform a web search as a fallback."""
    print("---NODE: WEB SEARCH---")
    question = state["question"]
    search = SerpAPIWrapper()
    try:
        search_results = search.run(question)
        documents = [Document(page_content=search_results)]
        print("Performed web search.")
        return {**state, "documents": documents}
    except Exception as e:
        print(f"Web search failed: {e}")
        return {**state, "documents": [Document(page_content="Search failed.")]}

def generate_fallback_answer(state: GraphState) -> GraphState:
    """Node to generate an answer using web search results."""
    print("---NODE: GENERATE FALLBACK ANSWER---")
    question = state["question"]
    documents = state["documents"]

    prompt = PromptTemplate(input_variables=["context", "question"], template=IMPROVED_FALLBACK_PROMPT_TEMPLATE)
    llm = get_llm()
    fallback_chain = prompt | llm
    
    generation = fallback_chain.invoke({"context": documents, "question": question}).content
    print("Generated answer from web search.")
    return {**state, "generation": generation, "sources": [{"title": "Web Search", "content": "Answer generated from web search results."}]}

def handle_greeting(state: GraphState) -> GraphState:
    """Node to handle simple greetings."""
    print("---NODE: HANDLE GREETING---")
    return {**state, "generation": "Hello! I am your Rural Health Assistant. How can I help you today?", "sources": []}

def handle_off_topic(state: GraphState) -> GraphState:
    """Node to handle off-topic questions."""
    print("---NODE: HANDLE OFF-TOPIC---")
    return {**state, "generation": "I am a Rural Health Assistant. I can only answer questions related to health and wellness. How can I help you with a health topic?", "sources": []}

# --- Conditional Edges ---
def route_question(state: GraphState) -> str:
    """Edge to route the question after classification."""
    print("---EDGE: ROUTE QUESTION---")
    classification = state["classification"]
    if "greeting" in classification:
        print("Decision: Greeting detected.")
        return "handle_greeting"
    if "off_topic" in classification:
        print("Decision: Off-topic question detected.")
        return "handle_off_topic"
    print("Decision: Health question, proceeding to RAG.")
    return "retrieve_docs"

def decide_after_rag(state: GraphState) -> str:
    """Edge to decide whether the RAG answer is sufficient or if a fallback is needed."""
    print("---EDGE: DECIDE AFTER RAG---")
    if "i don't have enough information" in state["generation"].lower():
        print("Decision: RAG answer is insufficient, falling back to web search.")
        return "web_search"
    print("Decision: RAG answer is sufficient.")
    return END

# --- Build the Graph ---
def build_agent_graph() -> Runnable:
    """Builds and compiles the LangGraph agent."""
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("classify_question", classify_question)
    workflow.add_node("retrieve_docs", retrieve_docs)
    workflow.add_node("generate_rag_answer", generate_rag_answer)
    workflow.add_node("web_search", web_search)
    workflow.add_node("generate_fallback_answer", generate_fallback_answer)
    workflow.add_node("handle_greeting", handle_greeting)
    workflow.add_node("handle_off_topic", handle_off_topic)

    # Define the graph's flow
    workflow.set_entry_point("classify_question")
    workflow.add_conditional_edges(
        "classify_question",
        route_question,
        {
            "handle_greeting": "handle_greeting",
            "handle_off_topic": "handle_off_topic",
            "retrieve_docs": "retrieve_docs",
        }
    )
    workflow.add_edge("retrieve_docs", "generate_rag_answer")
    workflow.add_conditional_edges("generate_rag_answer", decide_after_rag, {END: END, "web_search": "web_search"})
    workflow.add_edge("web_search", "generate_fallback_answer")
    workflow.add_edge("generate_fallback_answer", END)
    workflow.add_edge("handle_greeting", END)
    workflow.add_edge("handle_off_topic", END)

    return workflow.compile()

# --- Main Entry Point ---
def get_agentic_rag_response(question: str, config: RunnableConfig = None):
    """The main entry point for the agentic RAG."""
    try:
        app = build_agent_graph()
        initial_state = {"question": question, "classification": "", "documents": [], "generation": "", "sources": []}
        final_state = app.invoke(initial_state, config=config)
        
        return {
            "answer": final_state.get("generation", "I was unable to find an answer."),
            "sources": final_state.get("sources", [])
        }
    except Exception as e:
        print(f"Agentic RAG error: {e}")
        return {"answer": "An error occurred while processing your request.", "sources": []}

