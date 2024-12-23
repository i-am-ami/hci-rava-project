# %% [markdown]
# ## Set Up Environment
# 

# %%
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()


# Access environment variables
speech_key = os.getenv('SPEECH_KEY')
print(f'SPEECH_KEY: {speech_key}')
speech_endpoint = os.getenv('SPEECH_ENDPOINT')
print(f'SPEECH_ENDPOINT: {speech_endpoint}')
speech_region = os.getenv('SPEECH_REGION')
print(f'REGION: {speech_region}')

gpt_key = os.getenv('GPT_KEY')
print(f'GPT_KEY: {gpt_key}')
gpt_endpoint = os.getenv('GPT_ENDPOINT')
print(f'GPT_ENDPOINT: {gpt_endpoint}')
gpt_region = os.getenv('OPENAI_REGION')
print(f'REGION: {gpt_region}')

llama_token = os.getenv('LLAMA_TOKEN')
print(f'LLAMA_TOKEN: {llama_token}')
	

# %% [markdown]
# ## Speech-To-Text Azure

# %%
import azure.cognitiveservices.speech as speechsdk
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)

# %% [markdown]
# ### Dual Audio Detection Code

# %%
import sounddevice as sd
import wave
import azure.cognitiveservices.speech as speechsdk

class DualAudioStream:
    def __init__(self, rate=16000, chunk=1024):
        self.rate = rate
        self.chunk = chunk
        self.frames = []
        self.push_audio_input_stream = speechsdk.audio.PushAudioInputStream()

    def callback(self, indata, frames, time, status):
        """Sounddevice audio callback to capture and push audio data."""
        if status:
            print(f"Sounddevice input status: {status}")
        # Save audio frames for WAV file
        self.frames.append(indata.copy())
        # Write audio to PushAudioInputStream (required by Azure SDK)
        self.push_audio_input_stream.write(indata.tobytes())

    def start_recording(self):
        """Start streaming audio from the microphone."""
        print("Recording audio...")
        self.stream = sd.InputStream(
            samplerate=self.rate,
            channels=1,
            dtype='int16',
            blocksize=self.chunk,
            callback=self.callback,
        )
        self.stream.start()

    def stop_recording(self):
        """Stop streaming audio and close resources."""
        self.stream.stop()
        self.stream.close()
        print("Audio streaming stopped.")

    def save_to_wav(self, file_name):
        """Save recorded audio to a WAV file."""
        audio_data = b"".join(frame.tobytes() for frame in self.frames)
        with wave.open(file_name, "wb") as wf:
            wf.setnchannels(1)  # Mono audio
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(self.rate)
            wf.writeframes(audio_data)
        print(f"Audio saved to {file_name}.")


# %% [markdown]
# ### Speech Recognition

# %%
def recognize_speech(convo_history):
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    
    speech_config.speech_recognition_language="fr-FR"

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # Create an instance of the DualAudioStream
    dual_audio = DualAudioStream()

    try:
        # Start recording audio from the microphone
        dual_audio.start_recording()

        # Configure Azure SpeechRecognizer with PushAudioInputStream
        audio_config = speechsdk.audio.AudioConfig(stream=dual_audio.push_audio_input_stream)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # Start recognition
        print("Speak into your microphone...")
        speech_recognition_result = recognizer.recognize_once_async().get()
        dual_audio.stop_recording()
        # Handle recognition result
        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("You: {}".format(speech_recognition_result.text))
            print("Recognized: {}".format(speech_recognition_result.duration))
            speaker_profile = {"Speaker": "This User", "Duration": speech_recognition_result.duration, "Speaking Rate": speech_recognition_result.duration/len(speech_recognition_result.text)}
            convo_history["User Information"] += [{"Speaker Profile": speaker_profile, "Speaker Input": speech_recognition_result.text}]
            return speech_recognition_result.text
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_recognition_result.cancellation_details
            print("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")
    finally:
        dual_audio.stop_recording()
        if len(dual_audio.frames) > 0 and speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
              dual_audio.save_to_wav("output.wav")
			
        print("Finished.")
    return None

# %% [markdown]
# ## MyProsody Speech Rate Detection
# 
# We need to clone the myprosody repository, I chose to do so locally within the repo, but added it to the gitignore
# 

# %%
import myprosody as mysp
import io
import sys

def detect_sr(src: str) -> int:
    # Create a StringIO object to capture the output
    p=src
    c=r"./myprosody/myprosody"

    captured_output = io.StringIO()
    sys.stdout = captured_output  # Redirect sys.stdout to the StringIO object
    try:
        # Call the function whose output you want to capture
        mysp.myspsr(p,c)
    finally:
        sys.stdout = sys.__stdout__  # Restore the original sys.stdout
        
    # Get the captured output as a string
    output = captured_output.getvalue()
    captured_output.close()  # Close the StringIO object
    
    final_syl_sec = 8
    try:
        final_syl_sec = int(output.split(" ")[1].strip())
    except Exception as e:
        print(output)
    
    return final_syl_sec

# %% [markdown]
# ## Language Model

# %% [markdown]
# ### OpenAI GPT

# %%
def generate_response(prompt):
    """Generate a response using Azure OpenAI Service."""
    response = openai_client.chat_completions.create(
        deployment_id=deployment_id,
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message["content"]

# %% [markdown]
# ### LLama (test)

# %%
import subprocess


# Run the huggingface-cli login command
subprocess.run(["huggingface-cli", "login", "--token", llama_token])


# %%
!huggingface-cli download meta-llama/Meta-Llama-3-8B-Instruct --include "original/*" --local-dir Meta-Llama-3-8B-Instruct

# %%
import transformers
import torch

model_id = "meta-llama/Llama-3.1-8B"

pipeline = transformers.pipeline(
    "text-generation", model=model_id, model_kwargs={"torch_dtype": torch.bfloat16}, device_map="auto", use_auth_token=True
)


# %%

pipeline("Hey how are you doing today?")

# %% [markdown]
# ## Text-to-Speech

# %%
def speak_response(response):
	"""Convert text to speech using Azure Speech SDK."""
	speech_config.speech_synthesis_language="fr-FR"
	synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    # Define SSML with Speaking Rate
	rate = '20%'
	# speech_config.voice_name = "fr-FR-Julie-Apollo"
	speech_config.speech_synthesis_voice_name = "fr-FR-VivienneMultilingualNeural"
	ssml_string = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
    xmlns:mstts="http://www.w3.org/2001/mstts" 
    	xml:lang="en-US">
    		<voice name="fr-FR-VivienneMultilingualNeural">
        <prosody rate="{rate}">{response}.</prosody>
    </voice>
    </speak>"""
	result = synthesizer.speak_ssml_async(ssml_string).get()
	if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
		print("Speech synthesized successfully.")
		return result.audio_data
	elif result.reason == speechsdk.ResultReason.Canceled:
		cancellation_details = result.cancellation_details
		print(f"Speech synthesis canceled: {cancellation_details.reason}")
		if cancellation_details.reason == speechsdk.CancellationReason.Error:
			print(f"Error details: {cancellation_details.error_details}")

# Synthesize Speech
	# synthesizer.speak_text_async(response)


# %%
speak_response("Moi? Je vais bien, merci!")

# %%
def main():
    convo_history ={"User Information":[], "Agent Information":[]}

    """Main voice agent loop."""
    user_input = recognize_speech(convo_history)
    return convo_history
        # if user_input:
        #     # Generate a response using Azure OpenAI Service
        #     response = generate_response(user_input)
        #     print(f"Agent: {response}")
        #     # Speak the response
        #     speak_response(response)
        # else:
        #     print("Could not understand input. Please try again.")


# %%
if __name__ == "__main__":
    main()


