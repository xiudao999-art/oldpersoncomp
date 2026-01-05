import time
import nls
import os
from dotenv import load_dotenv

load_dotenv()

URL = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
TOKEN = os.getenv("ALIYUN_TOKEN")
APPKEY = os.getenv("ALIYUN_APPKEY")

class AliyunASR:
    def __init__(self):
        self.transcribed_text = ""
        self.is_completed = False
        self.error_msg = None

    def on_sentence_begin(self, message, *args):
        pass

    def on_sentence_end(self, message, *args):
        # Result is in message['payload']['result']
        if 'payload' in message and 'result' in message['payload']:
            self.transcribed_text += message['payload']['result']

    def on_start(self, message, *args):
        pass

    def on_error(self, message, *args):
        self.error_msg = message
        self.is_completed = True # Stop waiting on error

    def on_close(self, *args):
        pass

    def on_result_chg(self, message, *args):
        pass

    def on_completed(self, message, *args):
        self.is_completed = True

    def transcribe(self, audio_data):
        if not TOKEN or not APPKEY:
            return "Error: ALIYUN_TOKEN or ALIYUN_APPKEY not set in .env"

        try:
            sr = nls.NlsSpeechTranscriber(
                url=URL,
                token=TOKEN,
                appkey=APPKEY,
                on_sentence_begin=self.on_sentence_begin,
                on_sentence_end=self.on_sentence_end,
                on_start=self.on_start,
                on_result_changed=self.on_result_chg,
                on_completed=self.on_completed,
                on_error=self.on_error,
                on_close=self.on_close
            )

            # Start recognition
            # aformat="pcm" implies 16000Hz, 16bit, mono usually.
            r = sr.start(aformat="pcm",
                        enable_intermediate_result=False,
                        enable_punctuation_prediction=True,
                        enable_inverse_text_normalization=True)
            
            # Send audio data in chunks
            # audio_data should be bytes (PCM)
            chunk_size = 640
            slices = [audio_data[i:i+chunk_size] for i in range(0, len(audio_data), chunk_size)]
            
            for s in slices:
                sr.send_audio(bytes(s))
                time.sleep(0.001) # Small delay to simulate stream

            sr.stop()
            
            # Wait for completion
            start_time = time.time()
            while not self.is_completed and time.time() - start_time < 10:
                if self.error_msg:
                    return f"ASR Error: {self.error_msg}"
                time.sleep(0.1)
                
            if self.error_msg:
                 return f"ASR Error: {self.error_msg}"

            return self.transcribed_text
        except Exception as e:
            return f"ASR Exception: {e}"

def recognize_speech(audio_bytes):
    """
    Transcribes audio bytes (PCM 16k 16bit mono preferred).
    If WAV, header should be stripped before calling, or handled here.
    Simple header stripping (44 bytes) for standard WAV.
    """
    # Simple check for WAV header (RIFF)
    if audio_bytes.startswith(b'RIFF'):
        # Strip 44 bytes header
        pcm_data = audio_bytes[44:]
    else:
        pcm_data = audio_bytes
        
    asr = AliyunASR()
    return asr.transcribe(pcm_data)
