import streamlit as st
import requests
import os
import base64
from pathlib import Path
from streamlit_mic_recorder import mic_recorder

API_BASE_URL = "http://127.0.0.1:8000"
st.set_page_config(page_title="Alzheimer Assistant - Family Portal", layout="wide")

st.title("🧠 Alzheimer Assistant: Family Dashboard")
st.markdown("Manage your patient's data, memories, and medication schedules.")

st.sidebar.header("System Status")
if st.sidebar.button("Check Backend Connection"):
    try:
        response = requests.get(f"{API_BASE_URL}/docs")
        if response.status_code == 200:
            st.sidebar.success("Backend is Online! ✅")
    except:
        st.sidebar.error("Backend is Offline! ❌")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📁 Update Patient Data", "💊 Medication Logs", "💬 Chat History", "⏰ التنبيهات القادمة", "🎤 المحادثة الصوتية"])

with tab1:
    st.header("Upload New Knowledge")
    st.write("Upload text files (.txt) containing family stories or schedules to update the assistant's memory.")
    
    uploaded_file = st.file_uploader("Choose a file", type=['txt'])
    
    if uploaded_file is not None:
        if st.button("Update Assistant Memory"):
            save_path = Path("data") / "patient_info.txt"
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success("File uploaded successfully! Now building Vector Store...")
            try:
                from app.services.rag_builder import build_vector_store
                build_vector_store()
                st.success("Memory updated! The assistant now knows the new info. 🚀")
            except Exception as e:
                st.error(f"Error rebuilding memory: {e}")

with tab2:
    st.header("Medicine Scanning Activity")
    st.info("This section will show the list of medicines the patient scanned today.")


with tab3:
    st.header("💬 Recent Conversations")
    patient_id = st.text_input("Enter Patient ID:", value="101")
    
    if st.button("Fetch History"):
        with st.spinner("Fetching logs from MongoDB..."):
            try:
                response = requests.get(f"{API_BASE_URL}/chat/history/{patient_id}")
                if response.status_code == 200:
                    history = response.json()
                    if not history:
                        st.info("No conversations found for this patient yet.")
                    for msg in history:
                  
                        with st.chat_message("user" if msg['sender'] == 'patient' else "assistant"):
                            st.write(f"**{msg['sender'].capitalize()}:** {msg['text']}")
                            st.caption(f"Time: {msg['timestamp']}")
                else:
                    st.error("Could not fetch history. Check if Backend is running.")
            except Exception as e:
                st.error(f"Connection Error: {e}")

with tab4:
    st.header("⏰ التنبيهات القادمة")
    patient_id = st.text_input("Enter Patient ID:", value="101")
    
    if st.button("Fetch Reminders"):
        with st.spinner("Fetching reminders from MongoDB..."):
            try:
                response = requests.get(f"{API_BASE_URL}/reminders/{patient_id}")
                if response.status_code == 200:
                    reminders = response.json()
                    if not reminders:
                        st.info("")
                    else:
                        for reminder in reminders:
                            remind_time = reminder.get('remind_time', '')
                            if remind_time:
                                from datetime import datetime
                                if isinstance(remind_time, str):
                                    dt = datetime.fromisoformat(remind_time.replace('Z', '+00:00'))
                                else:
                                    dt = remind_time
                                
                                time_str = dt.strftime('%I:%M %p - %d/%m/%Y')
                            else:
                                time_str = " "
                            
                            status = " " if reminder.get('is_completed', False) else " "
                            
                            st.markdown(f"""
                            **{reminder.get('task_description', ' ')}**
                            
                            : {time_str}
                            : {status}
                            ---
                            """)
                else:
                    st.error("Could not fetch reminders. Check if Backend is running.")
            except Exception as e:
                st.error(f"Connection Error: {e}")
    
    st.markdown("---")
    st.subheader(" ")
    st.write(" ")
    
    with st.form("new_reminder_form"):
        new_task = st.text_input("", placeholder="")
        new_time = st.time_input("")
        
        if st.form_submit_button(" "):
            if new_task and new_time:
                try:
                    from datetime import datetime, date
                    today = date.today()
                    remind_datetime = datetime.combine(today, new_time)
                    
                    reminder_data = {
                        "patient_id": patient_id,
                        "message": f"{new_task} {new_time.strftime('%I:%M %p')}"
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/reminders",
                        json=reminder_data
                    )
                    
                    if response.status_code == 200:
                        st.success(" ")
                        st.rerun()
                    else:
                        st.error("")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning(" ")

with tab5:
    st.header(" ")
    st.write(" ")
    
    patient_id = st.text_input("", value="101", key="voice_patient_id")
    
    st.subheader(" ")
    audio_bytes = mic_recorder(
        start_prompt="Click to record",
        stop_prompt="Stop recording",
        just_once=False,
        use_container_width=False,
        callback=None,
        args=None,
        kwargs=None,
        key="mic_recorder"
    )
    
    audio_file = st.file_uploader(
        "Or upload audio file (WAV, MP3, M4A)", 
        type=['wav', 'mp3', 'm4a'],
        key="voice_file_upload"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        include_audio = st.checkbox("", value=True, key="include_audio_response")
    with col2:
        selected_voice = st.selectbox(
            " ",
            ["ar-EG-SalmaNeural", "ar-EG-ShakirNeural"],
            index=0,
            key="voice_selection"
        )
    
    if audio_bytes is not None:
        if st.button("", key="send_mic"):
            with st.spinner("Processing audio..."):
                try:
                    files = {"audio_file": ("recording.wav", audio_bytes, "audio/wav")}
                    data = {
                        "patient_id": patient_id,
                        "include_audio_response": include_audio
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/chat/voice",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("")
                        st.markdown(f"**You said:** {result['transcription']}")
                        
                        response_data = result['response']
                        st.markdown(f"**Assistant response:** {response_data['response_message']}")
                        
                        if response_data.get('audio_response') and include_audio:
                            audio_base64 = response_data['audio_response']
                            audio_bytes_response = base64.b64decode(audio_base64)
                            st.audio(audio_bytes_response, format='audio/mp3')
                            st.success("")
                        
                    else:
                        st.error(f"Processing failed: {response.text}")
                        
                except Exception as e:
                    st.error(f"Connection error: {e}")
    
    if audio_file is not None:
        if st.button("", key="send_file"):
            with st.spinner("Processing audio..."):
                try:
                    files = {"audio_file": (audio_file.name, audio_file.read(), audio_file.type)}
                    data = {
                        "patient_id": patient_id,
                        "include_audio_response": include_audio
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/chat/voice",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Show transcription
                        st.success("🎤 Audio received successfully!")
                        st.markdown(f"**You said:** {result['transcription']}")
                        
                        # Show response
                        response_data = result['response']
                        st.markdown(f"**Assistant response:** {response_data['response_message']}")
                        
                        # Play audio response if available
                        if response_data.get('audio_response') and include_audio:
                            audio_base64 = response_data['audio_response']
                            audio_bytes_response = base64.b64decode(audio_base64)
                            st.audio(audio_bytes_response, format='audio/mp3')
                            st.success("🔊 Playing audio response")
                        
                    else:
                        st.error(f"Processing failed: {response.text}")
                        
                except Exception as e:
                    st.error(f"Connection error: {e}")
    
    st.markdown("---")
    
    # Text chat with voice response option
    st.subheader("💬 محادثة نصية باستجابة صوتية")
    
    text_message = st.text_area(
        "اكتب رسالتك هنا:",
        placeholder="مثال: كيف حالك اليوم؟",
        key="text_message"
    )
    
    if st.button("📤 إرسال مع استجابة صوتية", key="send_text_with_voice"):
        if text_message.strip():
            with st.spinner("جاري توليد الاستجابة..."):
                try:
                    chat_data = {
                        "patient_id": patient_id,
                        "message": text_message,
                        "include_audio_response": include_audio
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/chat",
                        json=chat_data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Show response
                        st.markdown(f"**رد المساعد:** {result['response_message']}")
                        
                        # Play audio response if available
                        if result.get('audio_response') and include_audio:
                            audio_base64 = result['audio_response']
                            audio_bytes = base64.b64decode(audio_base64)
                            st.audio(audio_bytes, format='audio/mp3')
                            st.success("🔊 جاري تشغيل الاستجابة الصوتية")
                        
                    else:
                        st.error(f"فشل في المعالجة: {response.text}")
                        
                except Exception as e:
                    st.error(f"خطأ في الاتصال: {e}")
    
    st.markdown("---")
    
    # Voice system info
    st.subheader("ℹ️ معلومات النظام الصوتي")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("نظام تحويل الصوت", "OpenAI Whisper")
        st.metric("نظام توليد الصوت", "Microsoft Edge TTS")
    
    with col2:
        # Test voice system
        if st.button("🧪 اختبار الأصوات", key="test_voices"):
            with st.spinner("جاري اختبار الأصوات..."):
                try:
                    test_response = requests.get(f"{API_BASE_URL}/voices")
                    if test_response.status_code == 200:
                        voices = test_response.json()['voices']
                        st.info(f"تم العثور على {len(voices)} صوت عربي متاح")
                        for voice in voices[:3]:  # Show first 3 voices
                            st.write(f"• {voice['friendly_name']} ({voice['locale']})")
                    else:
                        st.error("فشل في اختبار الأصوات")
                except Exception as e:
                    st.error(f"خطأ في الاختبار: {e}")
        
        if st.button("🔊 اختبار TTS", key="test_tts"):
            with st.spinner("جاري اختبار تحويل النص لصوت..."):
                try:
                    test_text = "مرحباً، أنا مساعدك الشخصي لمريض الزهايمر. كيف يمكنني مساعدتك اليوم؟"
                    tts_response = requests.get(
                        f"{API_BASE_URL}/text-to-speech",
                        params={
                            "text": test_text,
                            "voice": selected_voice,
                            "return_base64": True
                        }
                    )
                    
                    if tts_response.status_code == 200:
                        result = tts_response.json()
                        audio_base64 = result['audio_base64']
                        audio_bytes = base64.b64decode(audio_base64)
                        st.audio(audio_bytes, format='audio/mp3')
                        st.success("🔊 تم تشغيل عينة صوتية بنجاح!")
                    else:
                        st.error("فشل في اختبار تحويل النص لصوت")
                        
                except Exception as e:
                    st.error(f"خطأ في الاختبار: {e}")