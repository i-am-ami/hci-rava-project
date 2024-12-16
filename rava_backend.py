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
convo_history ={"User Information":[{}], "Agent Information":[{}]}

# %% [markdown]
# ## Speech-To-Text Azure

# %%
import os
import azure.cognitiveservices.speech as speechsdk
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
def recognize_speech():
    # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
    
    speech_config.speech_recognition_language="fr-FR"

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    
    print("Speak into your microphone.")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()
    speaker_profile = speech_recognition_result.properties.get(speechsdk.PropertyId.SPEAKER_ID)
    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("You: {}".format(speech_recognition_result.text))
        return {"Speaker Profile": speaker_profile, "Speaker Input:": speech_recognition_result.text}
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")
    return None

# %% [markdown]
# ## Language Model

# %% [markdown]
# ### OpenAI GPT

# %%
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
def rava_loop():
    """Main voice agent loop."""
    while True:
        asr_output = recognize_speech()
        user_input = asr_output["Speaker Input:"]
        convo_history["User Information"].append(asr_output)
        if user_input:
            # Generate a response using Azure OpenAI Service
            # response = generate_response(user_input)
            response = "Voila! Une recette du gateau au chocolat pour vous : Ingrédients : 200g de chocolat noir, 100g de beurre, 100g de sucre, 50g de farine, 3 oeufs. Préparation : Faites fondre le chocolat et le beurre au bain-marie. Ajoutez le sucre et les oeufs. Incorporez la farine. Versez la pâte dans un moule beurré et fariné. Enfournez 20 minutes à 180°C. Bon appétit!"
            print(f"Agent: {response}")

            # Speak the response
            speak_response(response)
            return 
        else:
            print("Could not understand input. Please try again.")

# if __name__ == "__main__":
#     main()


