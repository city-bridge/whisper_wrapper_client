import numpy as np
import soundcard as sc
import config
from whisper_wrapper_client import WhisperWrapperClient

SAMPLE_RATE = 16000

if __name__ == "__main__":
    SERVER_HOST = config.SERVER_HOST
    SERVER_PORT = config.SERVER_PORT
    INTERVAL = 3
    mic = sc.default_microphone()

    with mic.recorder(channels=1, samplerate=SAMPLE_RATE) as rec:
        data = rec.record(SAMPLE_RATE * INTERVAL)
        client = WhisperWrapperClient(SERVER_HOST, SERVER_PORT)
        res = client.set_init_prompt("apple,google")
        # res = client.transcribe_raw_audio(data)
        res = client.recognize_raw_audio(data)
        print(res)
