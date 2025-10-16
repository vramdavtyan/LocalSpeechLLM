import streamlit as st
from ollama import chat
from faster_whisper import WhisperModel
from kokoro import KPipeline
import soundfile as sf
import numpy as np
import tempfile
import os

# Set up page
st.set_page_config(page_title="Ollama Speech Chatbot", page_icon="")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None

if "from_audio" not in st.session_state:
    st.session_state.from_audio = False

# Show chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Audio input
audio_value = st.audio_input("Tap to record", sample_rate=16000)

if audio_value:
    st.audio(audio_value)
    current_audio_bytes = audio_value.getvalue()

    if current_audio_bytes != st.session_state.last_audio_bytes:
        st.session_state.from_audio = True
        st.info("Transcribing audio...")

        # Save audio to temp WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(current_audio_bytes)
            tmp_path = tmp_file.name

        # Transcribe audio
        model = WhisperModel("base", device="cpu")
        segments, _ = model.transcribe(tmp_path)
        transcription = " ".join([seg.text for seg in segments])
        os.remove(tmp_path)

        # Add user's message
        # Show transcribed user message
        with st.chat_message("user"):
            st.markdown(transcription)

        # Add to chat history
        st.session_state.messages.append({"role": "user", "content": transcription})

        # Get assistant reply
        response = chat(
            model="llama3.2:3b",
            messages=st.session_state.messages,
        )
        reply = response["message"]["content"]
        # st.session_state.messages.append({"role": "assistant", "content": reply})

        # Generate and play audio reply
        pipeline = KPipeline(lang_code="a")
        generator = pipeline(reply, voice="af_heart", speed=1.0, split_pattern=r"\n+")

        audio_segments = [audio for _, _, audio in generator]

        if audio_segments:
            full_audio = np.concatenate(audio_segments)
            output_path = "output.wav"
            sf.write(output_path, full_audio, 24000)

            # Display reply + audio playback
            with st.chat_message("assistant"):
                st.markdown(reply)
                st.audio(output_path)

            # Save the reply and audio
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.session_state.last_audio_bytes = current_audio_bytes

# Text input — moved this ABOVE the st.stop() to ensure it's visible
prompt = st.chat_input("Ask something...")
if prompt:
    st.session_state.from_audio = False
    st.session_state.messages.append({"role": "user", "content": prompt})

    response = chat(
        model="llama3.2:3b",
        messages=st.session_state.messages,
    )
    reply = response["message"]["content"]
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# Prevent rerun until user hears the audio
if audio_value and current_audio_bytes != st.session_state.last_audio_bytes:
    st.stop()
