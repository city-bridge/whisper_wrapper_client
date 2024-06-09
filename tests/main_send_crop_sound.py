import config
from whisper_wrapper_client import WhisperWrapperClient,SoundRecodeAndCrop

if __name__ == "__main__":
    SERVER_HOST = config.SERVER_HOST
    SERVER_PORT = config.SERVER_PORT
    sound_recode_and_crop = SoundRecodeAndCrop()

    for i in range(3):
        data = sound_recode_and_crop.wait_sound()
        client = WhisperWrapperClient(SERVER_HOST, SERVER_PORT)
        #res = client.set_init_prompt("apple,google")
        res = client.transcribe_raw_audio(data)
        # res = client.recognize_raw_audio(data)
        print(res)
