import streamlit as st
from audiorecorder import audiorecorder

st.title("Audio Recorder")

audio = audiorecorder(
    "Click to record",
    "Click to stop recording",
    "Click to pause",
    custom_style={
        "display": "flex",
        "justifyContent": "center",
        "alignItems": "center",
        "margin": "0 auto",
        "width": "160px",
        "height": "80px",
        "fontSize": "20px",
        "backgroundColor": "#007BFF",  # Change to match your button color
        "color": "white",  # Text color
        "border": "none",
        "cursor": "pointer"
    },
    start_style={
        "backgroundColor": "red",
        "color": "white",
        "width": "160px",
        "height": "80px",
        "fontSize": "20px",
        "margin": "0 auto",
    },
    pause_style={
        "backgroundColor": "orange",
        "color": "white",
        "width": "160px",
        "height": "80px",
        "fontSize": "20px",
        "margin": "0 auto",
    },
    stop_style={
        "backgroundColor": "purple",
        "color": "white",
        "width": "160px",
        "height": "80px",
        "margin-top": "10px",
        "fontSize": "20px",
        "margin": "0 auto",
    },
    key="audio",
)

if len(audio) > 0:
    # To play audio in frontend:
    audio.export(out_f = "test_recording.wav", format = "wav")


