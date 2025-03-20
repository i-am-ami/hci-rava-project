import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv

load_dotenv()
speech_key = os.getenv('SPEECH_KEY')
speech_region = os.getenv('SPEECH_REGION')

def synthesize_speech_to_wav(filename):
    # Create a speech configuration instance
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_synthesis_voice_name = "fr-FR-VivienneMultilingualNeural"
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm)

    rate = '20%'
    ssml_string = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
        xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="fr-FR">
        <voice name="fr-FR-VivienneMultilingualNeural">
            <prosody rate="{rate}">{"Voilà une réponse"}.</prosody>
        </voice>
    </speak>"""

    # Set up audio configuration to output to a .wav file
    audio_config = speechsdk.audio.AudioOutputConfig(filename=filename)

    # Create a speech synthesizer
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # Synthesize the provided SSML to the .wav file
    result = synthesizer.speak_ssml_async(ssml_string).get()

    # Check the result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"Successfully synthesized the text to {filename}")
    else:
        print(f"Speech synthesis failed: {result.error_details}")

# Example usage
output_filename = "output_audio.wav"
synthesize_speech_to_wav(output_filename)
