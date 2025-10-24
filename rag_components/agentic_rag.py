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
        chat_history: Recent chat history for context-aware responses.
        user_name: User's name for personalization.
    """
    question: str
    classification: str
    generation: str
    documents: List[Document]
    sources: List[dict]
    chat_history: str
    user_name: str

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
You are a helpful health assistant. Give a clear, short answer.

{chat_history_section}

Context: {context}

Question: {question}

Instructions:
- Keep your answer SHORT - maximum 4-5 sentences
- Get straight to the point
- Use 2-3 bullet points if listing things
- Don't repeat the question back
- Don't say "I'm sorry to hear" or give long sympathy statements
- If context is not enough, say: "I don't have enough details to answer this properly."
- End with: "For proper diagnosis, consult a healthcare professional."
- No extra fluff or unnecessary explanations

Answer:
"""

IMPROVED_FALLBACK_PROMPT_TEMPLATE = """
You are a helpful health assistant. Give a clear, short answer.

{chat_history_section}

Question: {question}

Information available:
{context}

Instructions:
- Keep your answer SHORT - maximum 4-5 sentences
- Get straight to the point
- Use 2-3 bullet points if listing things
- Don't repeat the question back
- Don't say "I'm sorry to hear" or give long sympathy statements
- End with: "For proper diagnosis, consult a healthcare professional."
- No extra fluff or unnecessary explanations

Answer:
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
    chat_history = state.get("chat_history", "No previous conversation.")
    
    # Format chat history section only if there's actual history
    chat_history_section = ""
    if chat_history and "No previous conversation" not in chat_history:
        chat_history_section = f"**Previous conversation context:**\n{chat_history}\n"
    
    prompt = PromptTemplate(
        input_variables=["context", "question", "chat_history_section"], 
        template=RAG_PROMPT_TEMPLATE
    )
    llm = get_llm()
    rag_chain = prompt | llm
    
    generation = rag_chain.invoke({
        "context": documents, 
        "question": question,
        "chat_history_section": chat_history_section
    }).content
    
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
    chat_history = state.get("chat_history", "No previous conversation.")
    
    # If we have chat history, reformulate vague questions for better web search
    reformulated_query = question
    if chat_history and "No previous conversation" not in chat_history:
        # Check if question has vague pronouns (it, that, this, them, etc.)
        vague_pronouns = ["it", "that", "this", "these", "those", "them"]
        question_lower = question.lower()
        if any(f" {pronoun} " in f" {question_lower} " or question_lower.startswith(pronoun + " ") for pronoun in vague_pronouns):
            print(f"Detected vague question: '{question}', reformulating with context...")
            
            # Use LLM to reformulate the question with context
            reformulation_prompt = f"""You are reformulating a vague question into a clear search query.

Previous conversation:
{chat_history}

Current vague question: "{question}"

Task: Rewrite this as a clear, standalone search query that Google can understand.
Output ONLY the reformulated question, nothing else. No explanations.

Reformulated question:"""
            
            try:
                llm = get_llm()
                reformulated_query = llm.invoke(reformulation_prompt).content.strip()
                # Remove quotes if LLM added them
                reformulated_query = reformulated_query.strip('"\'')
                print(f"Reformulated query: '{reformulated_query}'")
            except Exception as e:
                print(f"Reformulation failed: {e}, using original question")
                reformulated_query = question
    
    search = SerpAPIWrapper()
    try:
        search_results = search.run(reformulated_query)
        documents = [Document(page_content=search_results)]
        print(f"Performed web search for: '{reformulated_query}'")
        return {**state, "documents": documents}
    except Exception as e:
        print(f"Web search failed: {e}")
        return {**state, "documents": [Document(page_content="Search failed.")]}

def generate_fallback_answer(state: GraphState) -> GraphState:
    """Node to generate an answer using web search results."""
    print("---NODE: GENERATE FALLBACK ANSWER---")
    question = state["question"]
    documents = state["documents"]
    chat_history = state.get("chat_history", "No previous conversation.")

    # Format chat history section only if there's actual history
    chat_history_section = ""
    if chat_history and "No previous conversation" not in chat_history:
        chat_history_section = f"**Previous conversation context:**\n{chat_history}\n"

    prompt = PromptTemplate(
        input_variables=["context", "question", "chat_history_section"], 
        template=IMPROVED_FALLBACK_PROMPT_TEMPLATE
    )
    llm = get_llm()
    fallback_chain = prompt | llm
    
    generation = fallback_chain.invoke({
        "context": documents, 
        "question": question,
        "chat_history_section": chat_history_section
    }).content
    print("Generated answer from web search.")
    return {**state, "generation": generation, "sources": [{"title": "Web Search", "content": "Answer generated from web search results."}]}

def handle_greeting(state: GraphState) -> GraphState:
    """Node to handle simple greetings."""
    print("---NODE: HANDLE GREETING---")
    user_name = state.get("user_name", "")
    chat_history = state.get("chat_history", "")
    
    # Personalized greeting based on history
    if chat_history and "No previous conversation" not in chat_history:
        greeting = f"Hello{' ' + user_name if user_name else ''}! 👋 Good to see you again! I'm here to help with any health questions you have. What would you like to know?"
    else:
        greeting = f"Hello{' ' + user_name if user_name else ''}! 👋 I'm your Rural Health Assistant. I'm here to answer your health questions and provide helpful information. What can I help you with today?"
    
    return {**state, "generation": greeting, "sources": []}

def handle_off_topic(state: GraphState) -> GraphState:
    """Node to handle off-topic questions."""
    print("---NODE: HANDLE OFF-TOPIC---")
    return {**state, "generation": "I specialize in health and wellness topics. 😊 I'd love to help you with questions about symptoms, treatments, prevention, or any health concerns. What health topic are you curious about?", "sources": []}

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
    
    # Check if no documents were retrieved
    if not state.get("documents") or len(state.get("documents", [])) == 0:
        print("Decision: No documents retrieved, falling back to web search.")
        return "web_search"
    
    # Check if LLM says it doesn't have enough information
    generation_lower = state["generation"].lower()
    if any(phrase in generation_lower for phrase in [
        "don't have enough", 
        "don't have sufficient",
        "insufficient information",
        "not enough information",
        "don't have details",
        "unable to answer",
        "cannot answer"
    ]):
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
def get_agentic_rag_response(question: str, chat_history: str = None, user_name: str = None, config: RunnableConfig = None):
    """
    The main entry point for the agentic RAG.
    
    Args:
        question: The user's current question
        chat_history: Formatted string of recent chat history (optional)
        user_name: User's name for personalization (optional)
        config: LangGraph configuration (optional)
    
    Returns:
        dict with 'answer' and 'sources' keys
    """
    try:
        app = build_agent_graph()
        initial_state = {
            "question": question, 
            "classification": "", 
            "documents": [], 
            "generation": "", 
            "sources": [],
            "chat_history": chat_history or "No previous conversation.",
            "user_name": user_name or ""
        }
        final_state = app.invoke(initial_state, config=config)
        
        return {
            "answer": final_state.get("generation", "I was unable to find an answer."),
            "sources": final_state.get("sources", [])
        }
    except Exception as e:
        print(f"Agentic RAG error: {e}")
        import traceback
        traceback.print_exc()
        return {"answer": "An error occurred while processing your request.", "sources": []}

