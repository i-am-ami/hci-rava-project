import streamlit as st
from audiorecorder import audiorecorder

st.title("Audio Recorder")
audio = audiorecorder("Click to record, ", "Recording...")

if len(audio) > 0:
    print(audio)
    # To play audio in frontend:
    audio.export(out_f = "test_recording.wav", format = "wav")