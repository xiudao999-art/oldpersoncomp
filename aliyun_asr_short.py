import time
import nls
import os
import json
from dotenv import load_dotenv

load_dotenv()

URL = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
TOKEN = os.getenv("ALIYUN_TOKEN")
APPKEY = os.getenv("ALIYUN_APPKEY")

class AliyunASRShort:
    def __init__(self):
        self.transcribed_text = ""
        self.is_completed = False
        self.error_msg = None

    def on_start(self, message, *args):
        # print("test_on_start:{}".format(message))
        pass

    def on_error(self, message, *args):
        # print("on_error args=>{}".format(args))
        self.error_msg = message
        self.is_completed = True

    def on_close(self, *args):
        # print("on_close: args=>{}".format(args))
        pass

    def on_result_chg(self, message, *args):
        # print("test_on_chg:{}".format(message))
        pass

    def on_completed(self, message, *args):
        # print("on_completed:args=>{} message=>{}".format(args, message))
        try:
            if isinstance(message, str):
                message = json.loads(message)
            
            if 'payload' in message and 'result' in message['payload']:
                self.transcribed_text = message['payload']['result']
        except Exception as e:
            print(f"Error parsing on_completed message: {e}")
            self.error_msg = f"Parse Error: {e}"
            
        self.is_completed = True

    def transcribe(self, audio_data):
        if not TOKEN or not APPKEY:
            return "Configuration Error: ALIYUN_TOKEN or ALIYUN_APPKEY is missing in .env. Please check your credentials."

        try:
            sr = nls.NlsSpeechRecognizer(
                url=URL,
                token=TOKEN,
                appkey=APPKEY,
                on_start=self.on_start,
                on_result_changed=self.on_result_chg,
                on_completed=self.on_completed,
                on_error=self.on_error,
                on_close=self.on_close,
            )

            # Start recognition
            print(f"DEBUG: Starting ASR with Token={TOKEN[:5]}... AppKey={APPKEY}")
            try:
                r = sr.start(aformat="pcm",
                            enable_intermediate_result=False,
                            enable_punctuation_prediction=True,
                            enable_inverse_text_normalization=True)
            except Exception as start_e:
                return f"ASR Start Failed: {start_e}"
            
            print(f"DEBUG: ASR Start Result: {r}")

            # Send audio data in chunks
            # audio_data should be bytes (PCM)
            chunk_size = 640
            slices = [audio_data[i:i+chunk_size] for i in range(0, len(audio_data), chunk_size)]
            
            print(f"DEBUG: Sending {len(slices)} chunks of audio data...")
            for i, s in enumerate(slices):
                sr.send_audio(bytes(s))
                if i % 100 == 0:
                    print(f"DEBUG: Sent chunk {i}/{len(slices)}")
                time.sleep(0.001)

            print("DEBUG: Stopping ASR...")
            sr.stop()
            print("DEBUG: ASR Stopped. Waiting for completion...")
            
            # Wait for completion
            start_time = time.time()
            while not self.is_completed and time.time() - start_time < 10:
                if self.error_msg:
                    print(f"DEBUG: Error detected: {self.error_msg}")
                    return f"ASR Error: {self.error_msg}"
                time.sleep(0.1)
                if int(time.time() - start_time) % 2 == 0:
                     print(f"DEBUG: Waiting... {int(time.time() - start_time)}s")
                
            if self.error_msg:
                 return f"ASR Error: {self.error_msg}"
            
            if not self.is_completed:
                print("DEBUG: ASR Timeout")
                return "ASR Timeout: No response from server."

            print(f"DEBUG: Transcribed text: {self.transcribed_text}")
            return self.transcribed_text
        except Exception as e:
            return f"ASR Exception: {e}"

def recognize_short_speech(audio_bytes):
    """
    Transcribes audio bytes using Aliyun Short Sentence Recognition.
    Expected: PCM 16k 16bit mono.
    """
    # Simple check for WAV header (RIFF)
    if audio_bytes.startswith(b'RIFF'):
        # Strip 44 bytes header
        pcm_data = audio_bytes[44:]
    else:
        pcm_data = audio_bytes
        
    asr = AliyunASRShort()
    return asr.transcribe(pcm_data)
