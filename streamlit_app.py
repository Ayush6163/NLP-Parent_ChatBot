# streamlit_app.py
import streamlit as st
from transformers import pipeline
import speech_recognition as sr
from pydub import AudioSegment
import os, tempfile, subprocess
from gtts import gTTS

# Use deep-translator instead of googletrans (works on Python 3.13+)
from deep_translator import GoogleTranslator

# -------------------------
# FFmpeg detection
# -------------------------
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

ffmpeg_ok = check_ffmpeg()
if not ffmpeg_ok:
    st.warning(
        "⚠️ FFmpeg not detected! Please install it from https://www.gyan.dev/ffmpeg/builds/ "
        "and add it to your PATH. Audio conversion (mp3 → wav) may not work without it."
    )

# -------------------------
# App config
# -------------------------
st.set_page_config(page_title="NLP Chatbot: Parent–Teacher Communication", layout="wide")
st.title("🗣️ NLP Chatbot for Parent–Teacher Communication (Prototype)")

st.sidebar.header("⚙️ Settings")
interface_lang = st.sidebar.selectbox("Select Language", ["auto", "en", "hi", "bn", "mr", "ta", "te"])
enable_tts = st.sidebar.checkbox("Enable Text-to-Speech (gTTS)", value=True)
model_name = st.sidebar.text_input("Hugging Face Model", value="microsoft/DialoGPT-small")

# -------------------------
# Model loader (tries conversational -> fallback to text-generation)
# Returns a dict: {'pipe': pipeline_obj, 'task': 'conversational'|'text-generation'}
# -------------------------
@st.cache_resource
def load_model(name):
    # try conversational first
    try:
        p = pipeline("conversational", model=name)
        return {"pipe": p, "task": "conversational"}
    except Exception as e:
        # try text-generation fallback
        try:
            p2 = pipeline("text-generation", model=name)
            return {"pipe": p2, "task": "text-generation"}
        except Exception as e2:
            st.error(f"Model load failed for both conversational and text-generation.\n"
                     f"conversational error: {e}\ntext-generation error: {e2}")
            return {"pipe": None, "task": None}

model_bundle = load_model(model_name)
conv_pipe = model_bundle["pipe"]
model_task = model_bundle["task"]

# translation helper (wraps deep-translator to mimic .translate(...).text)
class SimpleTranslator:
    def translate(self, text, src="auto", dest="en"):
        # deep-translator requires explicit source/target codes; it will attempt autodetect if source='auto'
        # GoogleTranslator's constructor uses source and target as strings; for 'auto' we'll use source='auto'
        try:
            translated = GoogleTranslator(source=src, target=dest).translate(text)
            # return object with .text attribute to match previous code pattern
            return type("T", (), {"text": translated})
        except Exception as e:
            # fallback: return original
            return type("T", (), {"text": text})

translator = SimpleTranslator()

# -------------------------
# Helper functions: audio convert, stt, tts
# -------------------------
def convert_to_wav(src_path):
    if src_path.lower().endswith(".wav"):
        return src_path
    wav_path = src_path + ".wav"
    sound = AudioSegment.from_file(src_path)
    sound.export(wav_path, format="wav")
    return wav_path

def stt_from_file(uploaded_file):
    if not uploaded_file:
        return ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    try:
        wav_path = convert_to_wav(tmp_path)
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
        text = r.recognize_google(audio)
    except sr.UnknownValueError:
        text = ""
    except Exception as e:
        st.warning(f"Speech Recognition error: {e}")
        text = ""
    finally:
        try:
            os.remove(tmp_path)
            if wav_path != tmp_path and os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception:
            pass
    return text

def generate_tts_audio(text, lang="en"):
    try:
        tts = gTTS(text=text, lang=lang if lang != "auto" else "en")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            with open(fp.name, "rb") as f:
                data = f.read()
        os.remove(fp.name)
        return data
    except Exception as e:
        st.warning(f"TTS generation failed: {e}")
        return None

# -------------------------
# Conversation state
# -------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# -------------------------
# UI
# -------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Conversation")
    for role, text in st.session_state.history:
        if role == "user":
            st.markdown(f"**👤 You:** {text}")
        else:
            st.markdown(f"**🤖 Bot:** {text}")

    st.divider()
    st.subheader("Send Message")

    uploaded_audio = st.file_uploader("🎤 Upload voice message (wav/mp3/m4a/ogg)", type=["wav", "mp3", "m4a", "ogg"])
    typed = st.text_input("Or type your message here:")
    send = st.button("Send")

    recognized_text = ""
    if uploaded_audio:
        with st.spinner("Processing voice input..."):
            recognized_text = stt_from_file(uploaded_audio)
        if recognized_text:
            st.success(f"Recognized: {recognized_text}")
        else:
            st.warning("Could not detect speech. Try again or type manually.")

    if send:
        user_text = (recognized_text if recognized_text else typed).strip()
        if not user_text:
            st.warning("No input provided.")
        else:
            st.session_state.history.append(("user", user_text))

            # translate to en if needed
            try:
                if interface_lang != "auto" and interface_lang != "en":
                    user_input_en = translator.translate(user_text, src=interface_lang, dest="en").text
                else:
                    user_input_en = user_text
            except Exception:
                user_input_en = user_text

            # Generate response depending on available pipeline
            bot_reply = "Sorry, model not available."
            if conv_pipe is None:
                bot_reply = "Model not loaded. Check model choice and internet connection."
            else:
                try:
                    if model_task == "conversational":
                        # conv pipeline usually returns a Conversation object or list
                        out = conv_pipe(user_input_en)
                        conv_obj = out[0] if isinstance(out, (list, tuple)) else out
                        if hasattr(conv_obj, "generated_responses") and conv_obj.generated_responses:
                            bot_reply = conv_obj.generated_responses[-1]
                        else:
                            # fallback if structure differs
                            bot_reply = getattr(conv_obj, "text", None) or getattr(conv_obj, "generated_text", None) or "Sorry, no reply."
                    else:
                        # text-generation path
                        gen = conv_pipe(user_input_en, max_length=150, do_sample=True, top_p=0.9, top_k=50)
                        # gen is a list of dicts with 'generated_text'
                        bot_reply = gen[0].get("generated_text", "Sorry, no reply.")
                except Exception as e:
                    st.warning(f"Primary model inference error: {e}")
                    # Try a second fallback: text-generation pipeline explicitly
                    try:
                        text_pipe = pipeline("text-generation", model=model_name)
                        gen = text_pipe(user_input_en, max_length=120, do_sample=True, top_p=0.9, top_k=50)
                        bot_reply = gen[0].get("generated_text", "Sorry, no reply.")
                    except Exception as e2:
                        bot_reply = f"Error generating response: {e2}"

            # translate reply back if needed
            try:
                if interface_lang != "auto" and interface_lang != "en":
                    bot_reply_disp = translator.translate(bot_reply, src="en", dest=interface_lang).text
                else:
                    bot_reply_disp = bot_reply
            except Exception:
                bot_reply_disp = bot_reply

            st.session_state.history.append(("bot", bot_reply_disp))

            # TTS playback
            if enable_tts:
                with st.spinner("Generating voice reply..."):
                    audio_bytes = generate_tts_audio(bot_reply_disp, lang=(interface_lang if interface_lang != "auto" else "en"))
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")

with col2:
    st.header("📘 Project Info")
    st.markdown(
        """
- **Goal:** Simplify parent–teacher communication in low-literacy regions.
- **Features:** Multilingual voice input/output using NLP + Speech AI.
- **Built with:** Streamlit, Transformers, SpeechRecognition, deep-translator, and gTTS.
"""
    )
    if st.button("🧹 Clear Chat"):
        st.session_state.history = []
        st.experimental_rerun()

st.caption("Prototype – For production, replace local model with an API-backed LLM (OpenAI or HF Inference) for reliable performance.")
