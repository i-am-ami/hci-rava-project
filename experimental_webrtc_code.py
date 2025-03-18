import wave
import numpy as np
import threading
import azure.cognitiveservices.speech as speechsdk
from streamlit_webrtc import webrtc_streamer, WebRtcMode, MediaStreamConstraints, RTCConfiguration

class DualAudioStream:
    def __init__(self, rate=16000, chunk=1024):
        self.rate = rate
        self.chunk = chunk
        self.frames = []
        self.push_audio_input_stream = speechsdk.audio.PushAudioInputStream()
        self.recording = False
        self.lock = threading.Lock()
    
    def azure_callback(self, indata, frames, time, status):
        """Sounddevice audio callback to capture and push audio data."""
        if status:
            print(f"Sounddevice input status: {status}")
        # Write audio to PushAudioInputStream (required by Azure SDK)
        self.push_audio_input_stream.write(indata.tobytes())

    def mysp_callback(self, indata, frames, time, status):
        """Sounddevice audio callback to capture and push audio data."""
        if status:
            print(f"Sounddevice input status: {status}")
        # Save audio frames for WAV file
        self.frames.append(indata.copy())
    
    def audio_processor_factory(self):
        """Create a processor class for WebRTC that handles audio frames"""
        self.frames = []  # Reset frames when starting new recording
        
        class AudioProcessor:
            def __init__(self_proc, stream_ctx):
                self_proc.stream_ctx = stream_ctx
                # These are used to simulate the sounddevice callback parameters
                self_proc.time_info = {"current_time": 0}
                self_proc.status = None
            
            def recv(self_proc, frame):
                if not self.recording:
                    return frame
                
                # Get audio data as numpy array
                audio_frame = frame.to_ndarray()
                
                # Process for Azure stream (16kHz, 16-bit)
                azure_audio = self._resample_and_convert(
                    audio_frame, 
                    from_rate=48000, 
                    to_rate=self.rate,
                    to_dtype=np.int16
                )
                
                # Call the original azure_callback with data in the expected format
                self.azure_callback(
                    azure_audio,
                    len(azure_audio),
                    self_proc.time_info,
                    self_proc.status
                )
                
                # Process for MyProsody stream (48kHz, 32-bit)
                mysp_audio = audio_frame.astype(np.int32)
                
                # Call the original mysp_callback with data in the expected format
                self.mysp_callback(
                    mysp_audio,
                    len(mysp_audio), 
                    self_proc.time_info,
                    self_proc.status
                )
                
                # Increment the time estimate
                self_proc.time_info["current_time"] += len(audio_frame) / 48000  # Time in seconds
                
                return frame
        
        return AudioProcessor
    
    def _resample_and_convert(self, audio_data, from_rate=48000, to_rate=16000, to_dtype=np.int16):
        """Resample audio and convert to target data type"""
        if from_rate == to_rate:
            return audio_data.astype(to_dtype)
        
        ratio = from_rate // to_rate
        resampled = audio_data[::ratio]
        return resampled.astype(to_dtype)
    
    def start_recording(self):
        """Start streaming audio from the microphone."""
        print("Recording audio...")
        self.recording = True
        
        # WebRTC configuration
        rtc_config = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})
        
        # Request high quality audio
        audio_constraints = MediaStreamConstraints(
            audio={"sampleRate": 48000, "echoCancellation": False, "noiseSuppression": False},
            video=False
        )
        
        # Create and start WebRTC streamer
        self.webrtc_ctx = webrtc_streamer(
            key="audio-recorder",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=rtc_config,
            media_stream_constraints=audio_constraints,
            video_processor_factory=None,
            audio_processor_factory=self.audio_processor_factory,
            async_processing=True,
        )

    def stop_recording(self):
        """Stop streaming audio and close resources."""
        self.recording = False
        # Close the Azure audio stream
        self.push_audio_input_stream.close()
        print("Audio streaming stopped.")

    def save_to_wav(self, file_name):
        """Save recorded audio to a WAV file."""
        with self.lock:
            audio_data = b"".join(frame.tobytes() for frame in self.frames)
            with wave.open(file_name, "wb") as wf:
                wf.setnchannels(1)  # Mono audio
                wf.setsampwidth(4)  # 32-bit audio (4 bytes)
                wf.setframerate(48000) 
                wf.writeframes(audio_data)
            print(f"Audio saved to {file_name}.")
