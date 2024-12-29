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
import azure.cognitiveservices.speech as speechsdk
import time
import numpy as np
def record_audio(stop_event, data_queue, pai_stream):
    """Start streaming audio from the microphone."""
    print("Recording audio...")

    def callback(indata, frames, time, status):
        """Sounddevice audio callback to capture and push audio data."""
        if status:
            print(f"Sounddevice input status: {status}")
        # Save audio frames for WAV file
        # Write audio to PushAudioInputStream (required by Azure SDK)
        data_queue.put(bytes(indata))
        print(type(indata))
        pai_stream.write(indata.tobytes())

    with sd.RawInputStream(samplerate=44100, dtype="int32", channels=1, callback=callback):
        while not stop_event.is_set():
            time.sleep(0.1)


# %% [markdown]
# ### Speech Recognition

# %%
from scipy.io import wavfile
from queue import Queue
import threading
def recognize_speech(convo_history):
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    
    speech_config.speech_recognition_language="fr-FR"

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # Create instances of the necessary audio stream (as per AzureSDK reqs) and recording thread variables.

    audio_stream = speechsdk.audio.PushAudioInputStream()
    data_queue = Queue()  # type: ignore[var-annotated]
    stop_event = threading.Event()
    recording_thread = threading.Thread(
        target=record_audio,
        args=(stop_event, data_queue, audio_stream),
    )

    
    try:
        # Start recording audio from the microphone
        recording_thread.start()

        # Configure Azure SpeechRecognizer with PushAudioInputStream
        audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # Start recognition
        print("Speak into your microphone...")
        speech_recognition_result = recognizer.recognize_once_async().get()

        # Stop audio recording, recognizer will have automatically stopped beforehand.
        stop_event.set()
        recording_thread.join()

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
        stop_event.set()
        recording_thread.join()
        audio_data = b"".join(list(data_queue.queue))
        audio_np = (np.frombuffer(audio_data, dtype=np.int32))

        if len(audio_np) > 0 and speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            wavfile.write("output.wav", 44100, audio_np)

        # # Current audio file is stuck at 16-bit, 256kbps, which is not enough for myprosody to be used.
        # # So let's upscale the audio 
        # upscale_wav("output.wav", "output_upscaled.wav", target_sample_rate=32000)
        
        # copy_file('./myprosody/myprosody/dataset/audioFiles/', 'output_upscaled.wav')
        # user_sr = detect_sr('output_upscaled')
        
        # user_sr = detect_sr('output')
        # print("User speech rate in syl/sec :: ", user_sr)

        print("Finished.")
    return None

# %% [markdown]
# ## Misc. functions
# 
# There is some compatibility issues we needed to work around to get Myprosody to work, so here are some methods 
# to handle the audio files.
# 
# %%  
# Code to copy the files, since myprosody doesn't take file paths.
import shutil
import os
def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"File {file_path} deleted successfully.")
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except PermissionError:
        print(f"Permission denied: {file_path}.")
    except Exception as e:
        print(f"Error occurred while deleting file {file_path}: {e}")

def copy_file (dst: str, src: str) :
    try:
        shutil.copy(src, dst)  # Preserves metadata like timestamps
        print(f"File copied successfully from {src} to {dst}")
    except Exception as e:
        print(f"An error occurred: {e}")

# %%  
# Code to upscale Microsoft's 16-bit 256kbps audio quality to 24-bit, 32khz audio to meet myprosody's requirements.      

from pydub import AudioSegment
import numpy as np
from scipy.signal import resample_poly

def upscale_wav(input_file, output_file, target_sample_rate=44100, target_bit_depth=24):
    # Load the .wav file
    audio = AudioSegment.from_wav(input_file)
    
    # Resample to target sample rate (32 kHz)
    original_sample_rate = audio.frame_rate
    audio_resampled = audio.set_frame_rate(target_sample_rate)
    
    # Convert to 24-bit by adjusting the sample width
    if target_bit_depth == 24:
        audio_resampled = audio_resampled.set_sample_width(3)  # 24-bit = 3 bytes per sample

    # Export the processed file
    audio_resampled.export(output_file, format="wav")


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

# # %%
# def generate_response(prompt):
#     """Generate a response using Azure OpenAI Service."""
#     response = openai_client.chat_completions.create(
#         deployment_id=deployment_id,
#         messages=[
#             {"role": "system", "content": "You are a helpful AI assistant."},
#             {"role": "user", "content": prompt},
#         ],
#     )
#     return response.choices[0].message["content"]

# # %% [markdown]
# # ### LLama (test)

# # %%
# import subprocess


# # Run the huggingface-cli login command
# subprocess.run(["huggingface-cli", "login", "--token", llama_token])


# # %%
# !huggingface-cli download meta-llama/Meta-Llama-3-8B-Instruct --include "original/*" --local-dir Meta-Llama-3-8B-Instruct

# # %%
# import transformers
# import torch

# model_id = "meta-llama/Llama-3.1-8B"

# pipeline = transformers.pipeline(
#     "text-generation", model=model_id, model_kwargs={"torch_dtype": torch.bfloat16}, device_map="auto", use_auth_token=True
# )


# %%

# pipeline("Hey how are you doing today?")

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
# speak_response("Moi? Je vais bien, merci!")

# %%




# %%
# if __name__ == "__main__":
#     main()


