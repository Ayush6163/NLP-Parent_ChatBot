# 🗣️ NLP Chatbot for Parent–Teacher Communication (Prototype)

A **Streamlit-based multilingual voice chatbot** designed to simplify parent–teacher communication in **low-literacy regions**.  
The system uses **NLP, Speech Recognition, and Text-to-Speech (TTS)** technologies to enable parents and teachers to interact naturally in their own vernacular languages.

---

## 🚀 Features

✅ **Multilingual support:** Communicate in English, Hindi, Bengali, Marathi, Tamil, or Telugu.  
✅ **Speech-to-Text (STT):** Converts uploaded voice messages to text using `speechrecognition`.  
✅ **Text-to-Speech (TTS):** Converts chatbot replies to audio using `gTTS`.  
✅ **Translation Engine:** Uses `deep-translator` for real-time language translation.  
✅ **Conversational AI:** Powered by a Hugging Face conversational/text-generation model (e.g., `microsoft/DialoGPT-small`).  
✅ **Streamlit UI:** Clean, responsive web interface for interactive communication.  

---

## 🧠 Objective

To create an **AI-driven communication bridge** between teachers and parents in underserved communities by:
- Providing a simple **voice-enabled chatbot** for low-literacy users.
- Promoting **parental engagement** in children’s education.
- Reducing communication gaps that lead to school dropouts.

---

## 🧩 Tech Stack

| Category | Tools & Libraries |
|-----------|------------------|
| **Frontend / UI** | [Streamlit](https://streamlit.io) |
| **NLP / ML** | [Transformers](https://huggingface.co/transformers/), [Torch](https://pytorch.org) |
| **Speech Processing** | `SpeechRecognition`, `pydub`, `gTTS` |
| **Translation** | `deep-translator` |
| **Audio Handling** | `ffmpeg` backend (for file conversion) |

---

## 🛠️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Ayush6163/NLP-Parent_ChatBot.git
cd NLP-Parent_ChatBot
