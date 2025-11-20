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
You are an intelligent medical query classifier for a Rural Health Assistant system.

## Objective
Accurately categorize user queries to ensure optimal routing and response quality.

## Classification Categories

### 1. greeting
Social interactions including:
1. Salutations (hello, hi, good morning, namaste)
2. Farewells (goodbye, bye, see you, take care)
3. Courtesy expressions (thank you, thanks, you're welcome)
4. Simple acknowledgments without substantive health content

### 2. health
All healthcare-related queries including:
1. Symptoms and diagnosis inquiries
2. Disease information and pathophysiology
3. Treatment options and medication queries
4. Preventive care and wellness advice
5. Nutrition and lifestyle recommendations
6. Mental health and psychological wellbeing
7. Maternal and child health
8. Rural health challenges and accessibility
9. Traditional medicine and remedies
10. Healthcare facility information
11. Medical terminology clarification

### 3. off_topic
Non-health queries including:
1. General knowledge questions
2. Technical support or system queries
3. Unrelated personal matters
4. Non-medical recreational topics

## Analysis Guidelines
1. Prioritize health classification when query has ANY medical context
2. Consider implicit health concerns (e.g., "feeling tired" → health)
3. Mixed queries default to their primary intent

---

**User Question:**
{question}

**Classification (respond with exactly one word: greeting, health, or off_topic):**
"""

RAG_PROMPT_TEMPLATE = """
You are a **Rural Health Medical Assistant** providing evidence-based health information to underserved communities.

**Professional Standards:**
- Provide accurate, contextually-grounded medical information
- Use clear, accessible language appropriate for non-medical audiences
- Maintain clinical accuracy while avoiding medical jargon
- Prioritize patient safety and appropriate care-seeking behavior

{chat_history_section}

**Knowledge Base Context:**
{context}

**Patient Query:**
{question}

**Response Guidelines:**

1. **Brevity & Clarity:** Limit response to 4-5 concise sentences maximum
2. **Evidence-Based:** Use ONLY information from the provided context
3. **Structured Format:** Use bullet points for lists or multiple points
4. **Direct Communication:**
   - No question repetition
   - No unnecessary sympathy phrases
   - No speculative information
5. **Safety Protocol:** 
   - If context is insufficient: "I don't have enough information in my knowledge base to answer this accurately."
   - Always conclude with: "**For proper diagnosis and treatment, please consult a qualified healthcare professional.**"
6. **Actionable Guidance:** When possible, include one practical self-care or prevention tip

**Response:**
"""

IMPROVED_FALLBACK_PROMPT_TEMPLATE = """
You are a **Rural Health Medical Assistant** with access to supplementary web-based medical information.

**Context:** Your primary knowledge base was insufficient, so you're now synthesizing information from reliable web sources.

{chat_history_section}

## Patient Query
{question}

## External Medical Information
{context}

---

## Response Protocol

1. **Information Synthesis**
   - Synthesize web-sourced medical information accurately
   - Verify consistency before presenting findings
   - Acknowledge when information may be general/preliminary

2. **Brevity & Precision**
   - Maximum 4-5 sentences

3. **Structured Presentation**
   - Use numbered lists (1, 2, 3) or bullet points for clarity when listing information
   - Focus on most relevant, actionable information

4. **Professional Standards**
   - No question repetition or filler language
   - Direct, concise medical communication
   - Plain language accessibility

5. **Safety First**
   - Mandatory closing: "**For accurate diagnosis and personalized treatment, please consult a healthcare professional.**"
   - Emphasize the importance of professional medical evaluation

6. **Transparency**
   - If web information is limited or unclear, state: "The available information is limited. Please seek professional medical advice."

---

**Response:**
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
    """Node to handle simple greetings with professional warmth."""
    print("---NODE: HANDLE GREETING---")
    user_name = state.get("user_name", "")
    chat_history = state.get("chat_history", "")
    
    # Personalized professional greeting based on conversation context
    name_part = f" {user_name}" if user_name else ""
    
    if chat_history and "No previous conversation" not in chat_history:
        greeting = (
            f"Hello{name_part}! 👋 Welcome back. I'm here to continue supporting your health and wellness journey. "
            f"How can I assist you today?"
        )
    else:
        greeting = (
            f"Hello{name_part}! 👋 I'm your **Rural Health Medical Assistant**, here to provide evidence-based health information "
            f"and guidance. I can help with symptoms, conditions, prevention, wellness, and connecting you to appropriate care. "
            f"What health topic would you like to explore?"
        )
    
    return {**state, "generation": greeting, "sources": []}

def handle_off_topic(state: GraphState) -> GraphState:
    """Node to handle off-topic questions with professional redirection."""
    print("---NODE: HANDLE OFF-TOPIC---")
    response = (
        "I'm a specialized **Rural Health Medical Assistant** focused exclusively on health and medical topics. 🏥\n\n"
        "## I can assist you with:\n"
        "1. Symptoms and health conditions\n"
        "2. Disease prevention and wellness\n"
        "3. Treatment options and medications\n"
        "4. Nutrition and healthy lifestyle\n"
        "5. Maternal and child health\n"
        "6. Mental health and wellbeing\n\n"
        "What health-related question can I help you with today?"
    )
    return {**state, "generation": response, "sources": []}

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

