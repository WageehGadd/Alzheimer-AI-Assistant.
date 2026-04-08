import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain_cohere import CohereEmbeddings, ChatCohere
from langchain_chroma import Chroma
from langchain_mongodb import MongoDBChatMessageHistory
from langchain_community.tools import DuckDuckGoSearchRun
from app.schemas.chat import ChatMessageResponse
from app.services.reminder_service import create_reminder, ReminderCreate

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
api_key = os.getenv("COHERE_API_KEY")
embeddings = CohereEmbeddings(model="embed-multilingual-v3.0", cohere_api_key=api_key)
persist_directory = str(_PROJECT_ROOT / "chroma_db")
vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
llm = ChatCohere(model="command-r-08-2024", cohere_api_key=api_key, temperature=0.3)

# --- DB CONFIG (single source of truth) ---
_MONGO_URI       = os.getenv("MONGO_URI")
_DB_NAME         = "alzheimer_app"
_COLLECTION_NAME = "chat_history"

# --- AGENT PERSONA PROMPT ---
_AGENT_SYSTEM_PROMPT = (
    "أنت مساعد شخصي دافئ ومتعاطف لمريض الزهايمر في مصر. "
    "هدفك هو دعمهم والإجابة على أسئلتهم باستخدام الأدوات المتاحة. "
    "مهم جداً: استجب دائماً باللهجة المصرية العامية البسيطة. "
    "استخدم عبارات مثل 'يا حبيبي'، 'يا والدي'، 'يا ست الكل' بطريقة طبيعية. "
    "اجعل الإجابات قصيرة جداً (جملة أو جملتين). "
    "استخدم الأدوات المتاحة للإجابة على أسئلة المريض."
)

# --- LANGCHAIN TOOLS ---

@tool
def personal_memory_search(query: str) -> str:
    """ابحث في ذكريات المريض الشخصية ومعلومات العائلة. استخدم هذا الأداة عندما يسأل المريض عن نفسه أو عائلته أو ماضيه."""
    try:
        docs = retriever.invoke(query)
        if not docs:
            return "معذرة، ما لقيتش معلومات عن السؤال ده."
        context_text = "\n".join([d.page_content for d in docs])
        return f"المعلومات الموجودة: {context_text}"
    except Exception as e:
        return f"حصلت مشكلة في البحث: {str(e)}"

@tool 
def medicine_search(medicine_name: str) -> str:
    """ابحث عن معلومات الدواء باستخدام الإنترنت. استخدم هذا الأداة عندما يسأل المريض عن دواء معين."""
    try:
        search = DuckDuckGoSearchRun()
        result = search.run(f"What is {medicine_name} medicine used for? dosage side effects")
        return f"معلومات الدواء: {result}"
    except Exception as e:
        return f"معذرة، مقدرش أبحث عن الدواء: {str(e)}"

@tool
def medicine_ocr_analysis(raw_ocr_text: str) -> str:
    """حلل نص OCR من صورة الدواء واستخرج اسم الدواء والتعليمات. استخدم هذا الأداة عند معالجة صور الأدوية."""
    try:
        # Clean OCR text to extract medicine name
        clean_name = " ".join(re.findall(r'[a-zA-Z0-9]{3,}', raw_ocr_text))
        if not clean_name:
            return "معذرة، مقدرش أقرأ اسم الدواء من الصورة."
        
        # Search for medicine info
        search = DuckDuckGoSearchRun()
        search_result = search.run(f"What is {clean_name} medicine used for?")
        
        return f"اسم الدواء المحتمل: {clean_name}\nمعلومات الدواء: {search_result}"
    except Exception as e:
        return f"حصلت مشكلة في تحليل صورة الدواء: {str(e)}"

@tool
def manage_reminders_tool(patient_id: str, reminder_message: str) -> str:
    """إضافة تنبيه جديد للمريض. استخدم هذا الأداة عندما يطلب المريض تذكيره بشيء (مثل 'فكرني آخد دوا')."""
    try:
        # Use LLM to extract task and time from natural language
        extraction_prompt = f"""
        استخرج من الجملة دي: المهمة والوقت.
        الجملة: "{reminder_message}"
        
        رجع كمان JSON بالصيغة دي:
        {{"task": "المهمة المطلوبة", "time": "الوقت بالصيغة 24 ساعة"}}
        
        لو الوقت نسبي (مثل "كمان ساعة" أو "الساعة 9 بالليل")، حوّله لوقت مطلق بناءً على الوقت الحالي: {datetime.now().strftime('%H:%M')}
        """
        
        extraction_response = llm.invoke(extraction_prompt)
        
        # Parse the LLM response to get task and time
        import json
        try:
            extracted_data = json.loads(extraction_response.content)
            task = extracted_data.get("task", reminder_message)
            time_str = extracted_data.get("time", "")
        except:
            # Fallback: simple parsing
            task = reminder_message
            time_str = datetime.now().strftime('%H:%M')
        
        # Convert time string to datetime
        if ":" in time_str:
            today = datetime.now().date()
            remind_time = datetime.combine(today, datetime.strptime(time_str, '%H:%M').time())
        else:
            # Default to 1 hour from now
            remind_time = datetime.now() + timedelta(hours=1)
        
        # Create reminder in database
        reminder_data = ReminderCreate(
            patient_id=patient_id,
            task_description=task,
            remind_time=remind_time
        )
        
        created_reminder = create_reminder(reminder_data)
        
        return f"حاضر يا حبيبي، هفكرك بـ '{task}' الساعة {remind_time.strftime('%I:%M %p')}"
        
    except Exception as e:
        return f"معذرة، مقدرش أضيف التنبيه: {str(e)}"

# --- AGENT SETUP ---

def get_session_history(session_id: str) -> MongoDBChatMessageHistory:
    """Used internally by RunnableWithMessageHistory to persist chat turns."""
    return MongoDBChatMessageHistory(
        connection_string=_MONGO_URI,
        session_id=session_id,
        database_name=_DB_NAME,
        collection_name=_COLLECTION_NAME,
    )

# Simplified approach: Create a tool-based chain instead of complex agent
def build_chat_chain():
    """Build a simple chain that can use tools based on context."""
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
    
    # Create a prompt that includes tool usage instructions
    system_prompt = _AGENT_SYSTEM_PROMPT + "\n\n" + (
        "لديك الأدوات التالية المتاحة:\n"
        "1. البحث في الذكريات الشخصية (للأسئلة عن المريض أو عائلته)\n"
        "2. البحث عن معلومات الأدوية (للأسئلة عن الأدوية)\n"
        "3. تحليل نص OCR (لتحليل صور الأدوية)\n"
        "4. إدارة التنبيهات (لإضافة تنبيهات جديدة للمريض)\n\n"
        "استخدم السياق المقدم من الأدوات للإجابة على سؤال المريض."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Context: {context}\n\nPatient Question: {input}")
    ])
    
    chain = (
        {
            "context": lambda x: get_context_for_input(x["input"]),
            "input": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain

def get_context_for_input(user_input: str) -> str:
    """Determine which tool to use based on input and get context."""
    user_input_lower = user_input.lower()
    
    # Check if it's about reminders
    if any(word in user_input_lower for word in ["فكرني", "تنبيه", "تذكير", " remind", "reminder"]):
        try:
            # Use the manage_reminders_tool directly
            return "تنبيه: المستخدم يريد إضافة تنبيه جديد"
        except:
            return "تنبيه: طلب إضافة تنبيه جديد"
    
    # Check if it's about medicine
    elif any(word in user_input_lower for word in ["دواء", "medicine", "علاج", "pill", "tablet"]):
        try:
            search = DuckDuckGoSearchRun()
            result = search.run(f"What is {user_input} medicine used for?")
            return f"معلومات الدواء: {result}"
        except:
            return "معذرة، مقدرش أبحث عن معلومات الدواء."
    
    # Check if it's about personal information
    elif any(word in user_input_lower for word in ["أنا", "عن", "ذكريات", "عائلتي", "ماضي"]):
        try:
            docs = retriever.invoke(user_input)
            if docs:
                context_text = "\n".join([d.page_content for d in docs])
                return f"المعلومات الشخصية: {context_text}"
            else:
                return "معذرة، ما لقيتش معلومات شخصية عن السؤال ده."
        except:
            return "معذرة، حصلت مشكلة في البحث عن المعلومات الشخصية."
    
    # Check if it contains OCR text
    elif "ocr" in user_input_lower or len(re.findall(r'[a-zA-Z0-9]{3,}', user_input)) > 2:
        try:
            clean_name = " ".join(re.findall(r'[a-zA-Z0-9]{3,}', user_input))
            if clean_name:
                search = DuckDuckGoSearchRun()
                result = search.run(f"What is {clean_name} medicine used for?")
                return f"تحليل OCR: اسم الدواء المحتمل: {clean_name}\nمعلومات: {result}"
            else:
                return "معذرة، مقدرش أقرأ اسم الدواء من النص."
        except:
            return "معذرة، حصلت مشكلة في تحليل النص."
    
    # Default: no specific context
    return ""

# Create global chain
chat_chain = build_chat_chain()

# Wrap with memory
chain_with_memory = RunnableWithMessageHistory(
    chat_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

def get_patient_history(patient_id: str) -> list[dict]:
    """
    Fetches chat history for a patient using LangChain's MongoDBChatMessageHistory,
    then converts the message objects into {sender, text, timestamp} dicts.
    """
    history_obj = get_session_history(patient_id.strip())
    messages = history_obj.messages

    result = []
    for msg in messages:
        sender = "user" if msg.type == "human" else "bot"
        timestamp = msg.additional_kwargs.get("timestamp", "")
        result.append({
            "sender": sender,
            "text": msg.content,
            "timestamp": timestamp,
        })

    return result[::-1]

def generate_chat_response(patient_id: str, message: str) -> ChatMessageResponse:
    """Generate chat response using the tool-enhanced chain with memory."""
    p_id_clean = patient_id.strip()
    try:
        config = {"configurable": {"session_id": p_id_clean}}
        
        response = chain_with_memory.invoke(
            {"input": message},
            config=config,
        )
        
        return ChatMessageResponse(
            patient_id=p_id_clean,
            response_message=response if isinstance(response, str) else str(response),
        )
    except Exception as e:
        print(f"[Chain Error]: {e}")
        return ChatMessageResponse(
            patient_id=p_id_clean,
            response_message="حصل مشكلة بسيطة، ممكن تعيد كلامك تاني؟",
        )

def search_medicine_online(raw_ocr_text: str) -> str:
    """Legacy function - use medicine_ocr_analysis tool instead."""
    clean_name = " ".join(re.findall(r'[a-zA-Z0-9]{3,}', raw_ocr_text))
    if not clean_name:
        return "No medicine found."
    search = DuckDuckGoSearchRun()
    return search.run(f"What is {clean_name} medicine used for?")