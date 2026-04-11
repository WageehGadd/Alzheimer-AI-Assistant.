# Alzheimer's Smart Assistant

> **Empowering Alzheimer's patients with compassionate AI care in Egyptian Arabic**

## Project Overview

Alzheimer's Smart Assistant is an innovative AI-powered platform designed to support patients with Alzheimer's disease through intelligent memory assistance, medication management, and proactive care. The system leverages cutting-edge AI technologies to provide personalized, empathetic interactions in Egyptian Arabic, helping patients maintain independence while ensuring their safety and well-being.

## Core Features

### **Autonomous AI Agent** 
- Intelligent tool routing with LangChain
- Context-aware decision making
- Natural language understanding for Egyptian Arabic

### **Agentic RAG (Retrieval-Augmented Generation)**
- Personal memory retrieval via ChromaDB vector store
- Family history and patient-specific context integration
- Semantic search for relevant information

### **Voice Engine** 
- **Text-to-Speech**: Microsoft Edge TTS with Egyptian Arabic voices (`ar-EG-SalmaNeural`, `ar-EG-ShakirNeural`)
- **Speech-to-Text**: OpenAI Whisper for audio transcription
- Compassionate audio responses with natural Egyptian dialect

### **Smart Reminders**
- Natural language task extraction using LLM
- Intelligent scheduling with relative time understanding
- Background job processing with APScheduler
- MongoDB-based reminder persistence

### **Medication OCR**
- Real-time drug identification from medicine images
- EasyOCR integration for Arabic and English text extraction
- AI-powered medication information analysis
- Safety alerts and dosage guidance

## Tech Stack

### Backend
- **Python 3.14+**
- **FastAPI** - RESTful API framework
- **LangChain** - AI agent orchestration
- **APScheduler** - Background task scheduling

### AI/LLM
- **Cohere** - Command-r-08-2024 model for reasoning
- **OpenAI Whisper** - Speech-to-text transcription
- **Microsoft Edge TTS** - Text-to-speech synthesis
- **EasyOCR** - Optical character recognition

### Database
- **MongoDB** - Primary data storage
- **ChromaDB** - Vector store for semantic search
- **Cohere Embeddings** - Multilingual text embeddings

### Frontend
- **Streamlit** - Family dashboard interface
- **Streamlit Mic Recorder** - Voice input component

## Architecture

```
Frontend (Streamlit Dashboard)
    |
    v
FastAPI Backend
    |
    v
LangChain Agent
    |
    v
Tools (RAG | Voice | Reminders | OCR)
    |
    v
Databases (MongoDB | ChromaDB)
```

The system follows an agent-based architecture where:

1. **User Input** (text/voice) enters through the Streamlit dashboard
2. **FastAPI** routes requests to the appropriate endpoints
3. **LangChain Agent** analyzes the input and selects relevant tools
4. **Tools** execute specific tasks (memory search, voice synthesis, reminder creation, OCR analysis)
5. **Databases** provide persistent storage and retrieval
6. **Response** flows back through the chain with optional audio output

## Installation & Usage

### Prerequisites
- Python 3.14 or higher
- MongoDB instance (local or cloud)
- FFmpeg (for audio processing)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/alzheimer-smart-assistant.git
   cd alzheimer-smart-assistant
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   MONGO_URI=mongodb://localhost:27017/alzheimer_app
   COHERE_API_KEY=your_cohere_api_key_here
   APP_NAME=Alzheimer Assistant Backend
   APP_VERSION=1.0.0
   ```

5. **Initialize the system**
   ```bash
   # Build vector store with patient data
   python -m app.services.rag_builder
   ```

6. **Run the application**
   ```bash
   # Start FastAPI backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

   # In another terminal, start Streamlit dashboard
   streamlit run dashboard.py --server.port 8501
   ```

7. **Access the applications**
   - **API Documentation**: http://localhost:8000/docs
   - **Family Dashboard**: http://localhost:8501

### Docker Deployment (Optional)

```bash
# Build and run with Docker Compose
docker-compose up --build
```

## API Endpoints

### Core Chat
- `POST /chat` - Text-based conversation with optional TTS
- `POST /chat/voice` - Voice input with text/audio response
- `GET /chat/history/{patient_id}` - Conversation history

### Voice Services
- `POST /voice-to-text` - Audio transcription
- `GET /text-to-speech` - Text-to-speech synthesis
- `GET /voices` - Available Arabic voices

### Reminders
- `POST /reminders` - Create new reminder
- `GET /reminders/{patient_id}` - Get pending reminders
- `PUT /reminders/{id}/complete` - Mark reminder complete

### Medication
- `POST /scan-medicine` - OCR medicine analysis
- `GET /medication/reminders/check` - Medication reminders

## Configuration

### Voice Settings
- Default voice: `ar-EG-SalmaNeural` (Egyptian Arabic female)
- Alternative: `ar-EG-ShakirNeural` (Egyptian Arabic male)
- Audio format: MP3, 16kHz sample rate

### Memory System
- Vector store: ChromaDB with Cohere embeddings
- Chunk size: 150 characters with 30-character overlap
- Search results: Top 2 most relevant chunks

### Reminder System
- Background checks: Every minute
- Time format: 24-hour with Egyptian Arabic localization
- Natural language processing for time extraction

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Wageeh Hussain**

- **LinkedIn**: [linkedin.com/in/wageehhussain](https://linkedin.com/in/wageehhussain)
- **GitHub**: [github.com/wageehhussain](https://github.com/wageehhussain)

---

> *Built with compassion for Alzheimer's patients and their families. Every interaction is designed to provide comfort, independence, and dignity through intelligent technology.*
