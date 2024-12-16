import azure.cognitiveservices.speech as speechsdk
import wave

# Azure Speech SDK configuration
speech_key = "YourAzureSpeechKey"
region = "YourAzureRegion"

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=region)

# Use the default microphone for audio capture
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

# Create a speech recognizer with microphone as the audio source
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

# List to store audio data chunks
audio_chunks = []

# Callback function for recognizing events
def handle_audio_event(evt):
    audio_data = evt.result.audio
    if audio_data:
        audio_chunks.append(audio_data)

# Subscribe to recognized audio events
speech_recognizer.recognized.connect(handle_audio_event)

# Start continuous recognition
print("Listening to microphone. Press Ctrl+C to stop...")
speech_recognizer.start_continuous_recognition()

try:
    while True:
        pass  # Keep listening indefinitely
except KeyboardInterrupt:
    # Stop recognition on interrupt
    speech_recognizer.stop_continuous_recognition()
    print("Stopping...")

# Combine audio chunks into a single byte stream
audio_bytes = b''.join(audio_chunks)

# Save the audio to a .wav file
output_filename = "output.wav"
with wave.open(output_filename, 'wb') as wf:
    wf.setnchannels(1)  # Mono audio
    wf.setsampwidth(2)  # 16-bit audio
    wf.setframerate(16000)  # 16 kHz sample rate
    wf.writeframes(audio_bytes)

print(f"Audio saved to {output_filename}")
