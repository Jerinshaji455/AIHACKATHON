import streamlit as st
import google.generativeai as genai
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import speech_recognition as sr
from gtts import gTTS
import os

# Configure Google Gemini API key
genai.configure(api_key='AIzaSyDA4tluJJPc_o-EnpJIwwJ6qVpmqbE8oEU')

# CSS to add a background image
page_bg_img = f"""
<style>
.stApp {{
    background-image: url("https://atroposjs.com/images/header/atropos-forest-front.svg");
    background-size: cover;
    background-repeat: no-repeat;
  
    background-attachment: fixed;
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# Initialize the recognizer for speech recognition
recognizer = sr.Recognizer()

class HealthChatbot:
    def __init__(self):
        # Initialize Google Gemini model
        model = genai.GenerativeModel("tunedModels/filteredtrainingdata-7veyyqnh8okr")
        self.chat = model.start_chat()

        # Set the chatbot's context as a health assistant
        self.get_response(" You are Aura, a friendly and knowledgeable health assistant. "
    "Respond to health-related questions with short, clear, and informative answers. "
    "Your tone should be empathetic, supportive, and professional. "
    "Focus on providing helpful advice and guidance in a conversational way.")

    def get_response(self, prompt):
        # Get a response from the chatbot model
        try:
            response = self.chat.send_message(prompt)
            print(response)
            print(prompt)
            return response.text
        except Exception as e:
            st.error(f"Error getting response from chatbot: {e}")
            return None

# Initialize the chatbot
chatbot = HealthChatbot()

# Streamlit UI
st.title("Aura- Your Personal Health Assistant")
st.write("Ask me anything related to health, and I'll do my best to help! Type 'bye' to exit.")

# Initialize session state for user input history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Audio input function using sounddevice
def record_audio(duration=5, fs=44100):
    st.write("Recording...")
    try:
        audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()  # Wait until the recording is finished
        st.write("Recording complete.")

        # Save the audio data as a WAV file
        wav.write("temp_audio.wav", fs, audio_data)
        return "temp_audio.wav"
    except Exception as e:
        st.error(f"Error recording audio: {e}")
        return None

# Function to recognize speech from the recorded audio
def get_audio_input():
    audio_file_path = record_audio()
    if audio_file_path is None:
        return None  # Return if recording failed

    try:
        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)
            user_input = recognizer.recognize_google(audio_data)
            st.write("You said: ", user_input)
            return user_input
    except sr.UnknownValueError:
        st.error("Sorry, I didn't catch that. Please try again.")
        return None
    except sr.RequestError as e:
        st.error(f"Error with the speech recognition service: {e}")
        return None
    finally:
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)  # Clean up temporary file

# Option to input via text or microphone
col1, col2 = st.columns([1, 0.1])
user_input = col1.text_input("You:", placeholder="Type your health-related question here...")
mic_clicked = col2.button("🎤")

if mic_clicked:
    user_input = get_audio_input()

# Check for exit condition
if user_input and user_input.lower() == 'bye':
    st.write("Health Assistant: Goodbye! Take care.")
else:
    # Store the input in the session state
    if user_input:
        st.session_state.chat_history.append(user_input)
        response = chatbot.get_response(user_input)
        
        if response:
            st.write(f"Health Assistant: {response}")
            
            # Convert response text to speech
            try:
                tts = gTTS(response, lang='en')
                tts.save("response.mp3")

                # Play audio response
                with open("response.mp3", "rb") as audio_file:
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format="audio/mp3")
                os.remove("response.mp3")
            except Exception as e:
                st.error(f"Error generating or playing audio response: {e}")
        else:
            st.write("Health Assistant: I'm sorry, I couldn't provide a response. Please try again.")

# Display chat history
if st.session_state.chat_history:
    st.write("### Chat History")
    for chat in st.session_state.chat_history:
        st.write(f"You: {chat}")

# Option to clear input and reset chat
if st.button("Clear"):
    st.session_state.chat_history = []
    st.experimental_rerun()
