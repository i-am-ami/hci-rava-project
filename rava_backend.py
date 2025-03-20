# %% [markdown]
# ## Set Up Environment
# 

# %%
from dotenv import load_dotenv
import os
from openai import AzureOpenAI

# Load .env file
load_dotenv()


# Access environment variables
speech_key = os.getenv('SPEECH_KEY')
print(f'SPEECH_KEY: {speech_key}')
speech_region = os.getenv('SPEECH_REGION')
print(f'SPEECH_REGION: {speech_region}')

model_name = "gpt-35-turbo"
deployment = "gpt-35-turbo"
api_version = "2025-01-01-preview"

client = AzureOpenAI(
    api_version=api_version,
)


llama_token = os.getenv('LLAMA_TOKEN')
print(f'LLAMA_TOKEN: {llama_token}')
	

# %% [markdown]
# ## Speech-To-Text Azure

# %%
import azure.cognitiveservices.speech as speechsdk
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)

# %% [markdown]
# ### Speech Recognition

# %%
from pydub import AudioSegment

def recognize_speech(agent_history):
    user_input_text = "";

    audio = AudioSegment.from_wav("user_input.wav")

    # Set the desired sample rate and bit depth
    desired_sample_rate = 16000  # 16 kHz
    desired_bit_depth = 16  # 16-bit

    # Resample and set bit depth
    audio = audio.set_frame_rate(desired_sample_rate).set_sample_width(desired_bit_depth // 8)

    # Export the converted audio
    audio.export("user_downsampled.wav", format="wav")
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    
    speech_config.speech_recognition_language="fr-FR"
    audio_config = speechsdk.AudioConfig(filename="user_downsampled.wav")
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # Start recognition
    print("Speak into your microphone...")
    speech_recognition_result = recognizer.recognize_once_async().get()
    # Handle recognition result
    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("You: {}".format(speech_recognition_result.text))
        print("Recognized: {}".format(speech_recognition_result.duration))
        speaker_profile = {"Speaker": "This User", "Duration": speech_recognition_result.duration, "Speaking Rate": speech_recognition_result.duration/len(speech_recognition_result.text)}
        agent_history["User Information"] += [{"Speaker Profile": speaker_profile, "Speaker Input": speech_recognition_result.text}]
        user_input_text = speech_recognition_result.text
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")
    
    copy_file('./myprosody/myprosody/dataset/audioFiles/', 'user_input.wav')

    user_sr = detect_sr('user_input')

    print("User speech rate in syl/sec :: ", user_sr)
    print("Finished.")
    # TODO: We clean up the audio files, but should we consider archiving them, and make them part of the download the user
    # give us?
    delete_file("./myprosody/myprosody/dataset/audioFiles/user_input.wav")
    delete_file("./myprosody/myprosody/dataset/audioFiles/user_input.TextGrid")
    delete_file("./user_input.wav")
    delete_file("./user_downsampled.wav")
    return (user_sr, user_input_text)

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
    # c=r"INSERT A PATH" # YOU NEED TO INSERT YOUR LOCAL PATH. Most likely will have to move the string variable to the env?
    # Here is what this line looks like for Abhi:
    c=r"/home/jayabbhi/Documents/HCI_grad_project/sts/hci-rava-project/myprosody/myprosody"
    # direct to the 2nd myprosody dir, but NO / at the end!

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

def generate_response(prompt, messages):
    messages.append({"role": "user", "content": prompt})

    """Generate a response using Azure OpenAI Service."""
    response = client.chat.completions.create(
        messages=messages,
        max_tokens=600,
        temperature=1.0,
        top_p=1.0,
        model=deployment
    )

    messages.append({"role": "system", "content": response.choices[0].message.content})
     
    return response.choices[0].message.content

# %%
min_sr_p = 1
max_sr_p = 15
def_sr_p = 5
def_myp_sr = 8


'''We are going to work in percentages of the final SpeechSynthesizer'''
def calc_new_sr(old_sr_p, user_sr):
    user_sr_p = (user_sr / def_myp_sr) * def_sr_p
    new_sr_p = int((old_sr_p + user_sr_p) / 2.0)
    new_sr_p = max(1, new_sr_p)
    new_sr_p = min(new_sr_p, 15)
    return new_sr_p




# %%
# TODO: implement the ollama version of the above code, to make testing the program easier without using too many credits

# %%
def speak_response(response):
	"""Convert text to speech using Azure Speech SDK."""
	speech_config.speech_synthesis_language="fr-FR"
	synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    # Define SSML with Speaking Rate
    # TODO: Need to set a bounds on the speech rate. 5% matches pretty nicely to 8 syllables per second 
    # like Google's own TTS service. 20% is a little two fast, so let's cap it at 15%
	rate = '5%' 
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
