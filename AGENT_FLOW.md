# 🤖 Complete Agentic RAG Flow

Here's the **full flow** of your Rural Health Chatbot Agent:

---

## 📊 Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER SENDS QUESTION                       │
│                 (e.g., "What is diabetes?")                  │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              FETCH CHAT HISTORY (chat/views.py)             │
│  • Get last 5 conversations from database                   │
│  • Format as: "User: Q1\nAssistant: A1\n..."               │
│  • Get user's name for personalization                      │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              NODE 1: CLASSIFY QUESTION                       │
│  • Uses LLM to classify question type                       │
│  • Categories: "greeting", "health", "off_topic"            │
│  • Prompt: "Is this greeting/health/off-topic?"             │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
                    ┌─────────┴─────────┐
                    │   ROUTING LOGIC    │
                    └─────────┬─────────┘
            ┌───────────────┼───────────────┐
            ↓               ↓               ↓
    ┌──────────────┐ ┌────────────┐ ┌─────────────┐
    │  GREETING?   │ │  HEALTH?   │ │ OFF-TOPIC?  │
    └──────┬───────┘ └─────┬──────┘ └──────┬──────┘
           ↓               ↓               ↓
    ┌──────────────┐ ┌────────────┐ ┌─────────────┐
    │  HANDLE      │ │  RETRIEVE  │ │  HANDLE     │
    │  GREETING    │ │  DOCUMENTS │ │  OFF-TOPIC  │
    │              │ │  FROM RAG  │ │             │
    └──────┬───────┘ └─────┬──────┘ └──────┬──────┘
           │               ↓               │
           │      ┌────────────────┐      │
           │      │ NODE 2:        │      │
           │      │ RETRIEVE DOCS  │      │
           │      │ • ChromaDB     │      │
           │      │ • Top 3 chunks │      │
           │      └────────┬───────┘      │
           │               ↓              │
           │      ┌────────────────┐      │
           │      │ NODE 3:        │      │
           │      │ GENERATE RAG   │      │
           │      │ ANSWER         │      │
           │      │ • Context +    │      │
           │      │   History +    │      │
           │      │   Question     │      │
           │      └────────┬───────┘      │
           │               ↓              │
           │      ┌────────────────┐      │
           │      │  DECISION:     │      │
           │      │  IS ANSWER     │      │
           │      │  SUFFICIENT?   │      │
           │      └────────┬───────┘      │
           │        ┌──────┴──────┐       │
           │        │ YES?  │ NO? │       │
           │        ↓       ↓     │       │
           │       END   ┌────────┴──────┐│
           │             │ NODE 4:       ││
           │             │ WEB SEARCH    ││
           │             │ • Detect vague││
           │             │ • Reformulate ││
           │             │ • SERP API    ││
           │             └────────┬──────┘│
           │                      ↓       │
           │             ┌────────────────┤
           │             │ NODE 5:        │
           │             │ GENERATE       │
           │             │ FALLBACK       │
           │             │ ANSWER         │
           │             └────────┬───────┘
           └──────────────────────┴───────┘
                                  ↓
        ┌─────────────────────────────────────┐
        │   SAVE TO DATABASE (ChatHistory)    │
        │   • Question                        │
        │   • Answer                          │
        │   • Timestamp                       │
        │   • User ID                         │
        └─────────────────┬───────────────────┘
                          ↓
        ┌─────────────────────────────────────┐
        │      RETURN RESPONSE TO USER        │
        │      • Answer                       │
        │      • Sources                      │
        │      • Timestamp                    │
        └─────────────────────────────────────┘
```

---

## 🔄 Detailed Step-by-Step Flow

### **Phase 1: Pre-Processing** (Before Agent)

```python
# File: chat/views.py - send_message()

1. User sends message via chatbot interface
2. Fetch last 5 conversations from ChatHistory model
3. Format chat history as text:
   "User: previous Q1
    Assistant: previous A1
    User: previous Q2
    Assistant: previous A2..."
4. Get user's first name or username
5. Call get_rag_response(question, chat_history, user_name)
```

---

### **Phase 2: Agent Graph Execution**

#### **NODE 1: Classify Question**
```python
# File: agentic_rag.py - classify_question()

Input: User's question
Process: 
  - Send to LLM with classification prompt
  - Prompt: "Is this greeting/health/off_topic?"
Output: classification = "greeting" | "health" | "off_topic"
```

#### **EDGE: Route Question**
```python
# File: agentic_rag.py - route_question()

if classification == "greeting":
    → Go to handle_greeting()
elif classification == "off_topic":
    → Go to handle_off_topic()
elif classification == "health":
    → Go to retrieve_docs()
```

---

#### **PATH A: Greeting** (Simple Path)
```python
# NODE: handle_greeting()

1. Check if chat history exists
2. If yes: "Hello [Name]! Welcome back!"
3. If no: "Hello [Name]! I am your Rural Health Assistant..."
4. Return greeting → END
```

---

#### **PATH B: Off-Topic** (Simple Path)
```python
# NODE: handle_off_topic()

Return: "I am a Rural Health Assistant. I can only answer 
         questions related to health and wellness."
→ END
```

---

#### **PATH C: Health Question** (Main RAG Path)

##### **NODE 2: Retrieve Documents**
```python
# File: agentic_rag.py - retrieve_docs()

Input: User's question
Process:
  1. Get vector store (ChromaDB)
  2. Generate embeddings for question
  3. Search for top 3 similar chunks
  4. Retrieve documents with metadata
Output: documents = [doc1, doc2, doc3]
```

##### **NODE 3: Generate RAG Answer**
```python
# File: agentic_rag.py - generate_rag_answer()

Input: 
  - Question
  - Retrieved documents (context)
  - Chat history
  
Process:
  1. Build prompt with:
     - Recent conversation history
     - Retrieved document context
     - Current question
  2. Send to LLM (Gemini)
  3. LLM generates answer using context
  
Output: 
  - generation = answer text
  - sources = document metadata
```

##### **EDGE: Decide After RAG**
```python
# File: agentic_rag.py - decide_after_rag()

Check if answer contains:
  "I don't have enough information"
  
If YES:
    → Go to web_search() (Fallback)
If NO:
    → END (answer is sufficient)
```

---

##### **NODE 4: Web Search** (Fallback)
```python
# File: agentic_rag.py - web_search()

Input: User's question
Process:
  1. Check if question has vague pronouns (it, that, this)
  2. If vague:
     a. Use LLM to reformulate with chat history
     b. "How can I prevent it?" 
        → "How can I prevent diabetes?"
  3. Call SERP API with reformulated query
  4. Get web search results
  
Output: documents = [web_results]
```

##### **NODE 5: Generate Fallback Answer**
```python
# File: agentic_rag.py - generate_fallback_answer()

Input:
  - Question (reformulated)
  - Web search results
  - Chat history
  
Process:
  1. Build prompt with web results + history
  2. LLM synthesizes answer from web
  3. Add disclaimer: "Consult healthcare professional"
  
Output:
  - generation = web-based answer
  - sources = "Web Search"
  
→ END
```

---

### **Phase 3: Post-Processing** (After Agent)

```python
# File: chat/views.py - send_message()

1. Receive response from agent:
   {
     "answer": "...",
     "sources": [...]
   }

2. Save to database:
   ChatHistory.objects.create(
     user=request.user,
     question=question,
     answer=response['answer']
   )

3. Return JSON to frontend:
   {
     "success": True,
     "question": "...",
     "answer": "...",
     "timestamp": "...",
     "sources": [...]
   }

4. Frontend displays answer in chat UI
```

---

## 🎯 Key Decision Points

### **Decision 1: Question Type**
- **Greeting** → Quick response, no RAG needed
- **Off-topic** → Polite redirect
- **Health** → Full RAG pipeline

### **Decision 2: RAG Sufficiency**
- **Sufficient** → Return answer from vector DB
- **Insufficient** → Fallback to web search

### **Decision 3: Query Reformulation**
- **Clear question** → Search as-is
- **Vague pronouns** → Reformulate with context

---

## 📦 Components Involved

| Component | File | Purpose |
|-----------|------|---------|
| **View** | `chat/views.py` | Handle HTTP, fetch history, call RAG |
| **Agent Graph** | `rag_components/agentic_rag.py` | Core logic flow |
| **LLM** | `rag_components/llm_and_rag.py` | Gemini API wrapper |
| **Vector Store** | `rag_components/vector_store_update.py` | ChromaDB operations |
| **Database** | `chat/models.py` | ChatHistory model |
| **Documents** | `documents/models.py` | Document upload & indexing |

---

## 🔑 Key Features

✅ **Context-Aware**: Uses last 5 conversations  
✅ **Smart Routing**: Different paths for different questions  
✅ **Fallback System**: Web search when local knowledge insufficient  
✅ **Query Reformulation**: Makes vague questions clear  
✅ **Personalization**: Uses user's name  
✅ **Source Tracking**: Shows where answers come from  

---

## 🚀 Example Flows

### Example 1: Simple Health Question (RAG Only)
```
User: "What is malaria?"
  ↓
Classify: "health"
  ↓
Retrieve: 3 documents about malaria from ChromaDB
  ↓
Generate: "Malaria is a parasitic disease..."
  ↓
Check: Answer is sufficient
  ↓
Save to DB
  ↓
Return to user ✅
```

### Example 2: Follow-Up Question (Context-Aware)
```
User: "How can I prevent it?"
  ↓
Classify: "health"
  ↓
Load history: "User asked about malaria"
  ↓
Retrieve: Documents about malaria prevention
  ↓
Generate: "To prevent malaria (from your earlier question)..."
  ↓
Check: Answer is sufficient
  ↓
Save to DB
  ↓
Return to user ✅ (mentions malaria even though user said "it")
```

### Example 3: Insufficient Knowledge (Fallback)
```
User: "What are the side effects of drug XYZ?"
  ↓
Classify: "health"
  ↓
Retrieve: No documents about drug XYZ
  ↓
Generate: "I don't have enough information..."
  ↓
Check: Insufficient → Trigger web search
  ↓
Web search: Query SERP API for "drug XYZ side effects"
  ↓
Generate fallback: Synthesize from web results
  ↓
Save to DB
  ↓
Return to user ✅ (with web search disclaimer)
```

### Example 4: Greeting
```
User: "Hello"
  ↓
Classify: "greeting"
  ↓
Check history: User has 5 previous conversations
  ↓
Handle greeting: "Hello John! Welcome back!"
  ↓
Save to DB
  ↓
Return to user ✅
```

---

## 💡 Advanced Features

### 1. **Automatic Vector DB Cleanup**
When documents are deleted via admin:
```
Admin deletes document
  ↓
Document.delete() called
  ↓
delete_document_vectors_by_doc_id() runs
  ↓
Find all chunks with doc_id
  ↓
Delete from ChromaDB
  ↓
Clear vector store cache
  ↓
Next RAG query gets fresh data ✅
```

### 2. **Query Reformulation**
For vague follow-up questions:
```
User: "How can I prevent it?"
  ↓
Detect vague pronoun: "it"
  ↓
Load chat history: "User asked about diabetes"
  ↓
LLM reformulates: "How can I prevent diabetes?"
  ↓
Web search with clear query
  ↓
Better results ✅
```

### 3. **Personalization**
```
First visit:
  "Hello John! I am your Rural Health Assistant..."

Return visit:
  "Hello John! Welcome back! How can I help you today?"
```

---

## 📊 Performance Characteristics

| Operation | Typical Time | Notes |
|-----------|--------------|-------|
| Chat history fetch | ~10ms | Database query |
| Question classification | ~1-2s | LLM call |
| Vector search | ~100-300ms | ChromaDB similarity search |
| RAG answer generation | ~2-4s | LLM call with context |
| Web search | ~3-5s | SERP API + LLM |
| Query reformulation | ~1-2s | LLM call |
| **Total (RAG path)** | ~3-7s | Most common |
| **Total (fallback)** | ~6-12s | When RAG insufficient |

---

## 🔐 Security & Privacy

✅ **User Isolation**: Each user only sees their own chat history  
✅ **Admin Access**: Health workers can view villager conversations (for support)  
✅ **Data Retention**: Users can clear their history anytime  
✅ **Vector DB Sync**: Deleted documents removed from vector store  
✅ **API Keys**: Sensitive keys stored in environment variables  

---

**That's the complete flow!** Every user message goes through this sophisticated pipeline to deliver accurate, contextual, and personalized health information. 🚀

---

## 🎯 Query Examples & Expected Behavior

### Category 1: Simple Health Questions (RAG Path)

#### Example 1.1: Disease Information
```
User: "What is diabetes?"

Flow: Classify → Retrieve → Generate RAG Answer
Expected Response:
  "Diabetes is a chronic condition where your blood sugar levels are too high. 
   It occurs when your body cannot produce enough insulin or cannot use insulin 
   effectively. Common symptoms include increased thirst, frequent urination, 
   extreme hunger, and fatigue."
   
Sources: [diabetes.pdf, health_guide.pdf]
Path: RAG ✅
Time: ~3-5s
```

#### Example 1.2: Symptoms Query
```
User: "What are symptoms of malaria?"

Flow: Classify → Retrieve → Generate RAG Answer
Expected Response:
  "Malaria symptoms typically include:
   • High fever and chills
   • Severe headache
   • Sweating
   • Nausea and vomiting
   • Body aches
   • Fatigue
   
   If you experience these symptoms, especially after visiting a malaria-prone area,
   consult a healthcare professional immediately."
   
Sources: [malaria_guide.pdf]
Path: RAG ✅
Time: ~3-5s
```

#### Example 1.3: Treatment Information
```
User: "How to treat high blood pressure?"

Flow: Classify → Retrieve → Generate RAG Answer
Expected Response:
  "High blood pressure can be managed through:
   
   **Lifestyle Changes:**
   • Reduce salt intake
   • Exercise regularly (30 minutes daily)
   • Maintain healthy weight
   • Limit alcohol consumption
   • Quit smoking
   
   **Medical Treatment:**
   • Your doctor may prescribe medications
   • Regular monitoring is essential
   
   Always consult a healthcare professional for personalized treatment."
   
Sources: [hypertension.pdf, health_guidelines.pdf]
Path: RAG ✅
Time: ~3-5s
```

---

### Category 2: Context-Aware Follow-Ups (Memory Path)

#### Example 2.1: Basic Follow-Up
```
Conversation History:
User: "What is tuberculosis?"
Bot: "Tuberculosis (TB) is a bacterial infection that mainly affects the lungs..."

Current Query: "How can I prevent it?"

Flow: Classify → Load History → Retrieve → Generate RAG Answer (with context)
Expected Response:
  "To prevent tuberculosis, which you asked about earlier, you should:
   
   • Get vaccinated (BCG vaccine)
   • Avoid close contact with TB patients
   • Ensure good ventilation in living spaces
   • Maintain a strong immune system through proper nutrition
   • Cover your mouth when coughing
   
   If you've been exposed to TB, consult a doctor for preventive treatment."
   
Sources: [tuberculosis_prevention.pdf]
Path: Context-Aware RAG ✅
Time: ~4-6s
Note: Bot mentions "tuberculosis" even though user only said "it"
```

#### Example 2.2: Symptom Follow-Up
```
Conversation History:
User: "My child has fever and vomiting"
Bot: "These symptoms could indicate various conditions..."

Current Query: "Should I give paracetamol?"

Flow: Classify → Load History → Retrieve → Generate RAG Answer (with context)
Expected Response:
  "For your child's fever and vomiting that you mentioned earlier:
   
   **Paracetamol (Acetaminophen):**
   • Yes, paracetamol can help reduce fever
   • Dosage depends on the child's age and weight
   • For children: 10-15mg per kg body weight, every 4-6 hours
   • Maximum 4 doses in 24 hours
   
   **Important:**
   • If vomiting continues, medication may not stay down
   • Ensure adequate hydration
   • If symptoms worsen or persist beyond 48 hours, seek medical attention immediately
   
   Consult a pediatrician for proper diagnosis and treatment."
   
Sources: [pediatric_care.pdf, fever_management.pdf]
Path: Context-Aware RAG ✅
Time: ~4-6s
Note: Bot remembers "child" and "fever and vomiting" from history
```

#### Example 2.3: Multi-Turn Clarification
```
Conversation History:
User: "What is dengue?"
Bot: "Dengue is a mosquito-borne viral infection..."

User: "What are the symptoms?"
Bot: "Dengue symptoms include high fever, severe headache, pain behind eyes..."

Current Query: "How long does it last?"

Flow: Classify → Load History → Retrieve → Generate RAG Answer (with context)
Expected Response:
  "Regarding dengue, which we've been discussing:
   
   The duration of dengue typically follows this pattern:
   
   **Acute Phase (4-7 days):**
   • High fever (104°F/40°C)
   • Severe body aches
   
   **Critical Phase (24-48 hours after fever drops):**
   • Most dangerous period
   • Risk of complications
   
   **Recovery Phase (2-3 days):**
   • Gradual improvement
   
   **Total Duration:** Usually 7-10 days
   
   Complete recovery may take 2-4 weeks. Rest and hydration are crucial.
   See a doctor if symptoms worsen during the critical phase."
   
Sources: [dengue_guide.pdf]
Path: Context-Aware RAG ✅
Time: ~4-6s
Note: Bot maintains context across multiple turns
```

---

### Category 3: Vague Questions (Query Reformulation + Fallback)

#### Example 3.1: Pronoun Resolution
```
Conversation History:
User: "What causes heart attack?"
Bot: "Heart attacks are caused by blockage in coronary arteries..."

Current Query: "How can I prevent it?"

Flow: Classify → Detect vague pronoun → Reformulate → Web Search → Generate Fallback
Reformulated Query: "How can I prevent heart attack?"

Expected Response:
  "Following up on your question about heart attacks, here's how to prevent them:
   
   **Lifestyle Modifications:**
   • Quit smoking
   • Exercise regularly (150 minutes/week)
   • Maintain healthy diet (low saturated fat, high fiber)
   • Control blood pressure
   • Manage stress
   • Maintain healthy weight
   
   **Medical Management:**
   • Regular health checkups
   • Monitor cholesterol levels
   • Take prescribed medications
   
   For personalized prevention strategies, consult a healthcare professional."
   
Sources: [Web Search]
Path: Context-Aware Fallback (Reformulated) ✅
Time: ~8-12s
Note: Query was reformulated from "it" to "heart attack" before web search
```

#### Example 3.2: Implicit Reference
```
Conversation History:
User: "What is pneumonia?"
Bot: "Pneumonia is an infection that inflames air sacs in lungs..."

Current Query: "What medicines are used?"

Flow: Classify → Retrieve (insufficient) → Reformulate → Web Search → Generate Fallback
Reformulated Query: "What medicines are used for pneumonia?"

Expected Response:
  "For pneumonia treatment that you asked about:
   
   **Antibiotics (for bacterial pneumonia):**
   • Amoxicillin
   • Azithromycin
   • Doxycycline
   
   **Supportive Medications:**
   • Fever reducers (paracetamol)
   • Cough suppressants
   • Pain relievers
   
   **Important:**
   • Specific antibiotic depends on pneumonia type
   • Complete the full course of antibiotics
   • Never self-medicate
   
   Consult a healthcare professional for proper diagnosis and prescription."
   
Sources: [Web Search]
Path: Context-Aware Fallback ✅
Time: ~8-12s
```

---

### Category 4: Greetings (Quick Path)

#### Example 4.1: First Time User
```
User: "Hello"

Flow: Classify → Handle Greeting
Expected Response:
  "Hello Rajesh! I am your Rural Health Assistant. How can I help you today?"
   
Sources: []
Path: Greeting ✅
Time: ~1-2s
Note: Uses user's first name
```

#### Example 4.2: Returning User
```
Conversation History: 5 previous conversations exist

User: "Hi"

Flow: Classify → Check History → Handle Greeting
Expected Response:
  "Hello Rajesh! Welcome back! How can I help you today?"
   
Sources: []
Path: Greeting (Personalized) ✅
Time: ~1-2s
Note: Acknowledges returning user
```

#### Example 4.3: Variations
```
User inputs: "hey", "good morning", "namaste", "hello doctor"

Expected Response:
  "Hello [Name]! [Welcome back!] I am your Rural Health Assistant. 
   How can I help you today?"
   
Sources: []
Path: Greeting ✅
Time: ~1-2s
```

---

### Category 5: Off-Topic Questions (Redirect Path)

#### Example 5.1: Weather
```
User: "What's the weather today?"

Flow: Classify → Handle Off-Topic
Expected Response:
  "I am a Rural Health Assistant. I can only answer questions related to 
   health and wellness. How can I help you with a health topic?"
   
Sources: []
Path: Off-Topic ✅
Time: ~1-2s
```

#### Example 5.2: General Knowledge
```
User: "Who won the cricket match?"

Flow: Classify → Handle Off-Topic
Expected Response:
  "I am a Rural Health Assistant. I can only answer questions related to 
   health and wellness. How can I help you with a health topic?"
   
Sources: []
Path: Off-Topic ✅
Time: ~1-2s
```

#### Example 5.3: Technical Support
```
User: "How do I reset my password?"

Flow: Classify → Handle Off-Topic
Expected Response:
  "I am a Rural Health Assistant. I can only answer questions related to 
   health and wellness. How can I help you with a health topic?"
   
Sources: []
Path: Off-Topic ✅
Time: ~1-2s
```

---

### Category 6: Complex Multi-Turn Scenarios

#### Example 6.1: Diagnosis Assistance
```
Turn 1:
User: "I have headache and fever for 3 days"
Bot: "Headache and fever for 3 days could indicate several conditions like flu, 
      dengue, or malaria. Other symptoms to watch for include..."
Sources: [fever_guide.pdf, dengue.pdf]

Turn 2:
User: "I also have body aches"
Bot: "With your headache, fever, and now body aches, this could suggest:
      • Viral infection (flu)
      • Dengue fever (if in mosquito-prone area)
      • Typhoid
      
      Have you noticed any rash or unusual bleeding?"
Sources: [dengue.pdf, viral_infections.pdf]

Turn 3:
User: "No rash, but I'm very tired"
Bot: "Fatigue along with your other symptoms (headache, fever, body aches) 
      is common with viral infections. Recommendations:
      • Rest adequately
      • Stay hydrated
      • Take paracetamol for fever
      • Monitor for warning signs
      
      If fever persists beyond 5 days or worsens, consult a doctor immediately."
Sources: [viral_infections.pdf, fever_management.pdf]

Path: Context-Aware RAG (Multi-Turn) ✅
Note: Bot builds symptom profile across conversation
```

#### Example 6.2: Medication Inquiry
```
Turn 1:
User: "What is metformin?"
Bot: "Metformin is a medication commonly used to treat type 2 diabetes..."
Sources: [diabetes_medications.pdf]

Turn 2:
User: "What are the side effects?"
Bot: "Regarding metformin that you asked about, common side effects include:
      • Nausea
      • Diarrhea
      • Stomach upset
      
      These usually improve over time. Serious side effects are rare but 
      include lactic acidosis."
Sources: [diabetes_medications.pdf]

Turn 3:
User: "Can I take it with food?"
Bot: "For metformin (from our earlier discussion), yes:
      • **Recommended:** Take with meals to reduce stomach upset
      • **Timing:** Usually with breakfast and dinner
      • **Important:** Follow your doctor's specific instructions
      
      Taking it with food significantly reduces nausea and digestive issues."
Sources: [diabetes_medications.pdf]

Path: Context-Aware RAG (Multi-Turn) ✅
Note: Bot maintains medication context across questions
```

---

### Category 7: Emergency Scenarios

#### Example 7.1: Urgent Symptoms
```
User: "My father is having severe chest pain and sweating"

Flow: Classify → Retrieve → Generate RAG Answer (Priority)
Expected Response:
  "⚠️ **URGENT: These symptoms suggest a possible heart attack!**
   
   **IMMEDIATE ACTIONS:**
   1. Call emergency services (108/102) NOW
   2. Make him sit or lie down comfortably
   3. Loosen tight clothing
   4. If he has prescribed nitroglycerin, help him take it
   5. Do NOT give food or water
   6. Stay calm and monitor breathing
   
   **Do NOT delay - get medical help immediately!**
   
   Time is critical in heart attacks. Every minute counts."
   
Sources: [emergency_care.pdf, heart_attack.pdf]
Path: RAG (Emergency Priority) ✅
Time: ~3-5s
Note: Response prioritizes immediate action
```

#### Example 7.2: Severe Bleeding
```
User: "My child cut his hand badly, blood won't stop"

Flow: Classify → Retrieve → Generate RAG Answer (Emergency)
Expected Response:
  "⚠️ **EMERGENCY - Follow these steps immediately:**
   
   **STOP THE BLEEDING:**
   1. Apply firm, direct pressure with clean cloth
   2. Keep pressure for at least 10 minutes
   3. Elevate the hand above heart level
   4. Do NOT remove the cloth if it soaks through - add more on top
   
   **CALL FOR HELP:**
   5. If bleeding doesn't stop in 10 minutes, call emergency services
   6. If wound is deep or gaping, seek medical attention immediately
   
   **PREVENT SHOCK:**
   7. Keep child calm and lying down
   8. Cover with blanket to maintain warmth
   
   Get medical help if bleeding is severe or won't stop!"
   
Sources: [first_aid.pdf, emergency_care.pdf]
Path: RAG (Emergency) ✅
Time: ~3-5s
```

---

### Category 8: Preventive Care Questions

#### Example 8.1: Vaccination
```
User: "What vaccinations does my baby need?"

Flow: Classify → Retrieve → Generate RAG Answer
Expected Response:
  "Your baby needs these essential vaccinations:
   
   **Birth:**
   • BCG (Tuberculosis)
   • Hepatitis B (1st dose)
   • OPV (Polio - 0 dose)
   
   **6 weeks:**
   • DPT (Diphtheria, Pertussis, Tetanus - 1st)
   • Hepatitis B (2nd)
   • OPV (1st)
   
   **10 weeks:**
   • DPT (2nd)
   • Hepatitis B (3rd)
   • OPV (2nd)
   
   **14 weeks:**
   • DPT (3rd)
   • OPV (3rd)
   
   **9-12 months:**
   • Measles/MMR
   
   Visit your nearest health center for the immunization schedule.
   Timely vaccination protects your child from serious diseases."
   
Sources: [immunization_schedule.pdf, child_health.pdf]
Path: RAG ✅
Time: ~4-6s
```

#### Example 8.2: Nutrition
```
User: "What should I eat to stay healthy?"

Flow: Classify → Retrieve → Generate RAG Answer
Expected Response:
  "For overall health, follow a balanced diet:
   
   **Grains (6-8 servings/day):**
   • Whole wheat, rice, millets
   
   **Vegetables (4-5 servings/day):**
   • Leafy greens, carrots, beans
   • Variety of colors
   
   **Fruits (3-4 servings/day):**
   • Seasonal fruits
   • Rich in vitamins
   
   **Proteins (2-3 servings/day):**
   • Pulses, beans, eggs, fish
   • Lean meat in moderation
   
   **Dairy (2-3 servings/day):**
   • Milk, yogurt, paneer
   
   **Limit:**
   • Sugary foods
   • Fried items
   • Excessive salt
   
   Stay hydrated (8-10 glasses of water daily).
   Consult a nutritionist for personalized diet plans."
   
Sources: [nutrition_guide.pdf, healthy_eating.pdf]
Path: RAG ✅
Time: ~4-6s
```

---

### Category 9: Insufficient Knowledge (Fallback Scenarios)

#### Example 9.1: Rare Condition
```
User: "What is Wilson's disease?"

Flow: Classify → Retrieve (no results) → Web Search → Generate Fallback
Expected Response:
  "Based on web search results:
   
   Wilson's disease is a rare genetic disorder where copper accumulates 
   in the body, particularly in the liver and brain. This buildup can 
   cause serious health problems.
   
   **Symptoms:**
   • Liver problems
   • Neurological issues
   • Psychiatric symptoms
   
   **Treatment:**
   • Requires lifelong medication
   • Dietary restrictions
   • Regular monitoring
   
   This is a complex condition. For accurate diagnosis and treatment, 
   please consult a specialized healthcare professional or gastroenterologist."
   
Sources: [Web Search]
Path: Web Fallback ✅
Time: ~8-12s
Note: No documents in vector DB about this rare condition
```

#### Example 9.2: New Drug Information
```
User: "Tell me about Remdesivir"

Flow: Classify → Retrieve (limited) → Web Search → Generate Fallback
Expected Response:
  "Based on available information:
   
   Remdesivir is an antiviral medication that has been used in the 
   treatment of certain viral infections, particularly COVID-19.
   
   **Usage:**
   • Hospital-administered only
   • Intravenous infusion
   • Under medical supervision
   
   **Important:**
   • Not for self-medication
   • Requires prescription
   • Availability may be limited
   
   For current guidelines and availability, consult a healthcare 
   professional. Treatment protocols may vary based on latest 
   medical recommendations."
   
Sources: [Web Search]
Path: Web Fallback ✅
Time: ~8-12s
```

---

## 📝 Query Pattern Analysis

### ✅ Works Best With:
- Clear health-related questions
- Symptoms description
- Disease information
- Treatment inquiries
- Prevention methods
- Follow-up questions in same topic
- Emergency situations

### ⚠️ May Need Fallback For:
- Rare diseases not in documents
- New medications
- Very specific drug interactions
- Latest research findings
- Location-specific health services

### ❌ Cannot Handle:
- Non-health topics (redirects politely)
- Diagnosis without doctor consultation (recommends seeing doctor)
- Prescription requests (advises consulting healthcare professional)
- Medical emergencies (provides first aid + urgent care advice)

---

## 🎓 Tips for Best Results

1. **Be Specific:** "What causes type 2 diabetes?" > "Tell me about diabetes"
2. **Include Context:** "My 5-year-old has fever" > "There is fever"
3. **Follow Up Naturally:** Bot remembers recent context
4. **Ask One Thing:** Break complex questions into parts
5. **Describe Symptoms Clearly:** Include duration, severity, other symptoms

---

**These examples demonstrate the full capabilities of your context-aware agentic RAG system!** 🚀
