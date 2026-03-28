# rag_components/agentic_rag.py
import os
import re
import logging
from typing import List, TypedDict
from django.conf import settings
from langchain_core.documents import Document
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities import SerpAPIWrapper
from langgraph.graph import StateGraph, END
from .llm_and_rag import (
    get_llm,
    get_retriever,
    is_rate_limit_error,
    is_connection_error,
    get_resilient_error_answer,
)

# --- Environment and Settings ---
os.environ["SERPAPI_API_KEY"] = getattr(settings, "SERPAPI_API_KEY", "")
logger = logging.getLogger(__name__)


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
4. If uncertain between categories, default to "health"
5. Any query about symptoms, disease, treatment, medication, nutrition, mental health, reports, tests, doctors, hospitals, appointments, pregnancy, child health, or prevention must be "health"

---

**User Question:**
{question}

**Classification (respond with exactly one word: greeting, health, or off_topic):**
"""

RAG_PROMPT_TEMPLATE = """
You are a **Rural Health Medical Assistant** providing evidence-based health information to underserved communities.

**Professional Standards:**
- Provide accurate, contextually-grounded medical information
- Use clear, simple, and accessible language appropriate for non-medical audiences (villager-friendly)
- Maintain clinical accuracy while strictly avoiding complex medical jargon
- Prioritize patient safety and appropriate care-seeking behavior
- Respond in the exactly SAME language that the user used to ask the question (English or Nepali). Do NOT mix languages unless necessary.

{chat_history_section}

**Knowledge Base Context:**
{context}

**Patient Query:**
{question}

**Response Guidelines:**

1. **Brevity & Clarity:** Limit response to 4-5 concise sentences maximum. Use very simple words.
2. **Evidence-Based:** Use ONLY information from the provided context
3. **Structured Format:** Use bullet points for lists or multiple points
4. **Direct Communication:**
   - No question repetition
   - No unnecessary sympathy phrases
   - No speculative information
5. **Safety Protocol:** 
   - If context is insufficient: "I don't have enough information in my knowledge base to answer this accurately." (Translate this to the user's language if needed).
   - Always conclude with: "**For proper diagnosis and treatment, please consult a qualified healthcare professional.**" (Translate this to the user's language).
6. **Actionable Guidance:** When possible, include one practical self-care or prevention tip
7. **Language Rule:**
    - Match the user's language perfectly. If they ask in English, answer in English. If they ask in Nepali, answer in Nepali.
    - Keep all terms understandable for uneducated rural users.

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
   - Maximum 4-5 sentences. Very simple, villager-friendly language.

3. **Structured Presentation**
   - Use numbered lists (1, 2, 3) or bullet points for clarity when listing information
   - Focus on most relevant, actionable information

4. **Professional Standards**
   - No question repetition or filler language
   - Direct, concise medical communication
   - Plain language accessibility, avoiding complex medical words
   - Respond in the exactly SAME language that the user used to ask the question (English or Nepali).

5. **Safety First**
   - Mandatory closing: "**For accurate diagnosis and personalized treatment, please consult a healthcare professional.**" (Translate to the user's language).
   - Emphasize the importance of professional medical evaluation

6. **Transparency**
   - If web information is limited or unclear, state: "The available information is limited. Please seek professional medical advice."

7. **Language Rule:**
    - Match the user's language perfectly. If they ask in English, answer in English. If they ask in Nepali, answer in Nepali.
    - Keep all terms understandable for uneducated rural users.

---

**Response:**
"""


# --- Nodes ---
def _looks_health_related(question: str) -> bool:
    """Lightweight keyword guard to avoid rejecting valid health questions."""
    q = (question or "").lower()
    health_terms = [
        "symptom",
        "pain",
        "fever",
        "cough",
        "cold",
        "headache",
        "dizzy",
        "vomit",
        "nausea",
        "diarrhea",
        "infection",
        "disease",
        "diabetes",
        "bp",
        "blood pressure",
        "sugar",
        "cholesterol",
        "asthma",
        "allergy",
        "treatment",
        "medicine",
        "tablet",
        "drug",
        "dose",
        "side effect",
        "doctor",
        "hospital",
        "clinic",
        "health worker",
        "appointment",
        "report",
        "test",
        "lab",
        "scan",
        "xray",
        "x-ray",
        "ecg",
        "pregnan",
        "baby",
        "child",
        "maternal",
        "nutrition",
        "diet",
        "mental",
        "stress",
        "anxiety",
        "depress",
        "wellness",
        "prevent",
        "vaccine",
        "immun",
        "wound",
        "injury",
        "first aid",
        # Nepali / localized maternal-health and medical terms
        "garbhawati",
        "garbhavati",
        "garbha",
        "गर्भवती",
        "जाँच",
        "जांच",
        "jancha",
        "janch",
        "pregnancy",
        "pregnant",
        "antenatal",
        "anc",
        "prasuti",
        "sutaune",
        "mahina",
        "baccha",
        "bacha",
        "bacha",
    ]
    return any(term in q for term in health_terms)


def _looks_like_greeting(question: str) -> bool:
    """Detect simple greetings/courtesies without spending an LLM call."""
    q = (question or "").strip().lower()
    if not q:
        return False

    # Normalize punctuation/spacing and then match whole words to avoid
    # false positives like "kahile" accidentally matching "hi".
    normalized = re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", q)).strip()
    words = set(normalized.split())

    single_word_greetings = {
        "hello",
        "hi",
        "hey",
        "namaste",
        "thanks",
        "bye",
        "goodbye",
    }
    phrase_greetings = {
        "good morning",
        "good afternoon",
        "good evening",
        "thank you",
    }

    return bool(words.intersection(single_word_greetings)) or any(
        phrase in normalized for phrase in phrase_greetings
    )


def _heuristic_classification(question: str) -> str:
    if _looks_like_greeting(question):
        return "greeting"
    if _looks_health_related(question):
        return "health"
    return "off_topic"


def _normalize_classification(raw_output: str, question: str) -> str:
    classification = (raw_output or "").strip().lower()
    if "greeting" in classification:
        return "greeting"
    if "off_topic" in classification or "off-topic" in classification:
        return "off_topic"
    if "health" in classification:
        return "health"
    return _heuristic_classification(question)


def _classify_with_llm(question: str) -> str:
    prompt = PromptTemplate(
        input_variables=["question"], template=CLASSIFICATION_PROMPT_TEMPLATE
    )
    llm = get_llm()
    classification_chain = prompt | llm
    raw = classification_chain.invoke({"question": question}).content
    return _normalize_classification(raw, question)


def _get_classifier_mode() -> str:
    mode = getattr(settings, "RAG_CONFIG", {}).get("CLASSIFIER_MODE", "hybrid").lower()
    if mode in {"llm", "heuristic", "hybrid"}:
        return mode
    return "hybrid"


def classify_question(state: GraphState) -> GraphState:
    """Node to classify the user's question."""
    logger.debug("NODE: CLASSIFY QUESTION")
    question = state["question"]

    mode = _get_classifier_mode()
    try:
        # Hybrid keeps cost low while still leveraging LLM for ambiguous queries.
        if mode == "heuristic":
            classification = _heuristic_classification(question)
        elif mode == "llm":
            classification = _classify_with_llm(question)
        else:
            if _looks_like_greeting(question):
                classification = "greeting"
            else:
                classification = _classify_with_llm(question)
    except Exception as e:
        logger.warning("Classifier failure; using heuristic fallback: %s", e)
        classification = _heuristic_classification(question)

    logger.info("Question classified as: %s (mode=%s)", classification, mode)
    return {**state, "classification": classification}


def retrieve_docs(state: GraphState) -> GraphState:
    """Node to retrieve documents from the vector store."""
    logger.debug("NODE: RETRIEVE DOCUMENTS")
    question = state["question"]
    retriever = get_retriever()
    documents = retriever.invoke(question)
    logger.info("Retrieved %s documents.", len(documents))
    return {**state, "documents": documents}


def generate_rag_answer(state: GraphState) -> GraphState:
    """Node to generate an answer using the RAG pipeline."""
    logger.debug("NODE: GENERATE RAG ANSWER")
    question = state["question"]
    documents = state["documents"]
    chat_history = state.get("chat_history", "No previous conversation.")

    # Format chat history section only if there's actual history
    chat_history_section = ""
    if chat_history and "No previous conversation" not in chat_history:
        chat_history_section = f"**Previous conversation context:**\n{chat_history}\n"

    prompt = PromptTemplate(
        input_variables=["context", "question", "chat_history_section"],
        template=RAG_PROMPT_TEMPLATE,
    )
    llm = get_llm()
    rag_chain = prompt | llm

    generation = rag_chain.invoke(
        {
            "context": documents,
            "question": question,
            "chat_history_section": chat_history_section,
        }
    ).content

    sources = []
    for doc in documents:
        sources.append(
            {
                "title": doc.metadata.get("source", "Unknown"),
                "content": (
                    (doc.page_content[:200] + "...")
                    if len(doc.page_content) > 200
                    else doc.page_content
                ),
                "metadata": doc.metadata,
            }
        )

    logger.info("Generated answer from RAG.")
    return {**state, "generation": generation, "sources": sources}


def web_search(state: GraphState) -> GraphState:
    """Node to perform a web search as a fallback."""
    logger.debug("NODE: WEB SEARCH")
    question = state["question"]
    chat_history = state.get("chat_history", "No previous conversation.")

    # Keep fallback lightweight: avoid extra LLM reformulation calls under quota limits.
    reformulated_query = question
    if chat_history and "No previous conversation" not in chat_history:
        history_lines = [
            line.strip() for line in chat_history.splitlines() if line.strip()
        ]
        if history_lines:
            reformulated_query = f"{question} {history_lines[-1]}"

    search = SerpAPIWrapper()
    try:
        search_results = search.run(reformulated_query)
        documents = [Document(page_content=search_results)]
        logger.info("Performed web search for query.")
        return {**state, "documents": documents}
    except Exception as e:
        logger.warning("Web search failed: %s", e)
        return {**state, "documents": [Document(page_content="Search failed.")]}


def generate_fallback_answer(state: GraphState) -> GraphState:
    """Node to generate an answer using web search results."""
    logger.debug("NODE: GENERATE FALLBACK ANSWER")
    question = state["question"]
    documents = state["documents"]
    chat_history = state.get("chat_history", "No previous conversation.")

    # Format chat history section only if there's actual history
    chat_history_section = ""
    if chat_history and "No previous conversation" not in chat_history:
        chat_history_section = f"**Previous conversation context:**\n{chat_history}\n"

    prompt = PromptTemplate(
        input_variables=["context", "question", "chat_history_section"],
        template=IMPROVED_FALLBACK_PROMPT_TEMPLATE,
    )
    llm = get_llm()
    fallback_chain = prompt | llm

    generation = fallback_chain.invoke(
        {
            "context": documents,
            "question": question,
            "chat_history_section": chat_history_section,
        }
    ).content
    logger.info("Generated answer from web search.")
    return {
        **state,
        "generation": generation,
        "sources": [
            {
                "title": "Web Search",
                "content": "Answer generated from web search results.",
            }
        ],
    }


def handle_greeting(state: GraphState) -> GraphState:
    """Node to handle simple greetings with professional warmth."""
    logger.debug("NODE: HANDLE GREETING")
    user_name = state.get("user_name", "")
    chat_history = state.get("chat_history", "")

    # Personalized professional greeting based on conversation context
    name_part = f" {user_name}" if user_name else ""

    if chat_history and "No previous conversation" not in chat_history:
        greeting = (
            f"Hello{name_part}! / नमस्ते{name_part}! 👋 Welcome back. I am here to help with your health and wellness needs. / पुनः स्वागत छ। म तपाईंको स्वास्थ्य र कल्याणसम्बन्धी सहायताका लागि यहाँ छु।\n\n"
            f"How can I help you today? / आज तपाईंलाई के विषयमा सहयोग चाहिन्छ?"
        )
    else:
        greeting = (
            f"Hello{name_part}! / नमस्ते{name_part}! 👋 I am your **Rural Health Medical Assistant**. I provide simple, evidence-based health information. / म तपाईंको **ग्रामीण स्वास्थ्य मेडिकल सहायक** हुँ। म साधारण र प्रमाणमा आधारित स्वास्थ्य जानकारी दिन्छु।\n\n"
            f"I can help with symptoms, diseases, prevention, nutrition, and mental health. / म लक्षण, रोग, रोकथाम, पोषण, र मानसिक स्वास्थ्य बारे मद्दत गर्न सक्छु।\n\n"
            f"What health topic would you like to know about? / तपाईं कुन स्वास्थ्य विषयमा जानकारी चाहनुहुन्छ?"
        )

    return {**state, "generation": greeting, "sources": []}


def handle_off_topic(state: GraphState) -> GraphState:
    """Node to handle off-topic questions with professional redirection."""
    logger.debug("NODE: HANDLE OFF-TOPIC")
    response = (
        "I am a **Rural Health Medical Assistant** and can only help with health/medical-related topics. / म **ग्रामीण स्वास्थ्य मेडिकल सहायक** हुँ र स्वास्थ्य/चिकित्सा सम्बन्धित विषयमा मात्र सहयोग गर्छु। 🏥\n\n"
        "## Here is what I can help with / म यी विषयमा सहयोग गर्न सक्छु:\n"
        "1. Symptoms & health issues / लक्षण र स्वास्थ्य समस्याहरू\n"
        "2. Disease prevention & healthy habits / रोग रोकथाम र स्वास्थ्यकर बानी\n"
        "3. Treatment options & medicine info / उपचार विकल्प र औषधि जानकारी\n"
        "4. Nutrition & lifestyle / पोषण र जीवनशैली\n"
        "5. Pregnancy, maternal & child health / गर्भावस्था, आमा तथा बाल स्वास्थ्य\n"
        "6. Mental health & wellbeing / मानसिक स्वास्थ्य र कल्याण\n\n"
        "Please ask your health-related question. / कृपया आफ्नो स्वास्थ्यसम्बन्धी प्रश्न सोध्नुहोस्।"
    )
    return {**state, "generation": response, "sources": []}


# --- Conditional Edges ---
def route_question(state: GraphState) -> str:
    """Edge to route the question after classification."""
    logger.debug("EDGE: ROUTE QUESTION")
    classification = (state.get("classification") or "").strip().lower()

    # Safety net: if classifier is noisy, still route medical-looking questions to health pipeline.
    if classification not in {"greeting", "health", "off_topic"}:
        classification = (
            "health"
            if _looks_health_related(state.get("question", ""))
            else "off_topic"
        )

    if "greeting" in classification:
        logger.info("Decision: Greeting detected.")
        return "handle_greeting"
    if "off_topic" in classification:
        logger.info("Decision: Off-topic question detected.")
        return "handle_off_topic"
    logger.info("Decision: Health question, proceeding to RAG.")
    return "retrieve_docs"


def _is_insufficient_answer(answer_text: str) -> bool:
    """Detect low-confidence/insufficient responses across common local languages."""
    text = (answer_text or "").strip().lower()
    if not text:
        return True

    insufficient_markers = [
        # English
        "don't have enough",
        "don't have sufficient",
        "insufficient information",
        "not enough information",
        "don't have details",
        "unable to answer",
        "cannot answer",
        "i don't know",
        # Nepali (Roman/Devanagari variants)
        "paryapt jankari chaina",
        "paryapt jankari chhaina",
        "paryapt jaankari chaina",
        "पर्याप्त जानकारी छैन",
        "पर्याप्त जानकारी छैन।",
        "मेरो ज्ञानको आधारमा पर्याप्त जानकारी छैन",
        "ज्ञानको आधारमा पर्याप्त जानकारी छैन",
        "मसँग पर्याप्त जानकारी छैन",
        # Hindi variants that often appear in multilingual output
        "पर्याप्त जानकारी नहीं है",
        "मेरे ज्ञान के आधार पर पर्याप्त जानकारी नहीं है",
    ]
    return any(marker in text for marker in insufficient_markers)


def decide_after_rag(state: GraphState) -> str:
    """Edge to decide whether the RAG answer is sufficient or if a fallback is needed."""
    logger.debug("EDGE: DECIDE AFTER RAG")

    # Check if no documents were retrieved
    if not state.get("documents") or len(state.get("documents", [])) == 0:
        logger.info("Decision: No documents retrieved, falling back to web search.")
        return "web_search"

    # Check if LLM says it doesn't have enough information (multilingual)
    if _is_insufficient_answer(state.get("generation", "")):
        logger.info("Decision: RAG answer is insufficient, falling back to web search.")
        return "web_search"

    logger.info("Decision: RAG answer is sufficient.")
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
        },
    )
    workflow.add_edge("retrieve_docs", "generate_rag_answer")
    workflow.add_conditional_edges(
        "generate_rag_answer", decide_after_rag, {END: END, "web_search": "web_search"}
    )
    workflow.add_edge("web_search", "generate_fallback_answer")
    workflow.add_edge("generate_fallback_answer", END)
    workflow.add_edge("handle_greeting", END)
    workflow.add_edge("handle_off_topic", END)

    return workflow.compile()


_AGENT_APP: Runnable | None = None


def _get_agent_app() -> Runnable:
    """Return a cached compiled graph for production performance."""
    global _AGENT_APP
    if _AGENT_APP is None:
        _AGENT_APP = build_agent_graph()
    return _AGENT_APP


# --- Main Entry Point ---
def get_agentic_rag_response(
    question: str,
    chat_history: str = None,
    user_name: str = None,
    config: RunnableConfig = None,
):
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
        app = _get_agent_app()
        initial_state = {
            "question": question,
            "classification": "",
            "documents": [],
            "generation": "",
            "sources": [],
            "chat_history": chat_history or "No previous conversation.",
            "user_name": user_name or "",
        }
        final_state = app.invoke(initial_state, config=config)

        return {
            "answer": final_state.get("generation", "I was unable to find an answer."),
            "sources": final_state.get("sources", []),
        }
    except Exception as e:
        logger.exception("Agentic RAG error: %s", e)

        if is_rate_limit_error(e) or is_connection_error(e):
            return {"answer": get_resilient_error_answer(e), "sources": []}

        return {
            "answer": "An error occurred while processing your request.",
            "sources": [],
        }
