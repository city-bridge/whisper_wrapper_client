import multiprocessing
import queue
import soundcard as sc
from soundcard.mediafoundation import _Recorder
import time
import logging
import sys

formatter = logging.Formatter("%(asctime)s %(levelname)5s %(name)s %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)


class SoundRecodeProcess:
    sound_queue: multiprocessing.Queue
    process: multiprocessing.Process
    run: multiprocessing.Value
    mic_name: str
    samplerate: int
    channel: int
    frame_size_sec: float

    def __init__(self) -> None:
        self.sound_queue = multiprocessing.Queue()
        self.run = multiprocessing.Value("i", 0)
        self.process = multiprocessing.Process(target=self.mic_recode_loop, args=())
        self.mic_name = None
        self.samplerate = 16000
        self.frame_size_sec = 0.5
        self.channel = 1

    def start(self):
        self.run.value = 1
        self.process.start()

    def stop(self):
        self.run.value = 0
        self.process.join()

    def mic_recode_loop(self):
        if self.mic_name == None:
            mic = sc.default_microphone()
        else:
            mic = sc.get_microphone(self.mic_name)
        logger.info("recode start mic:%s", mic.name)
        with mic.recorder(channels=self.channel, samplerate=self.samplerate) as rec:
            self._recode_loop(rec)
        self._end_queue()
        logger.info("recode end")

    def _recode_loop(self, rec: _Recorder):
        pre_time = time.time()
        frame_size = int(self.samplerate * self.frame_size_sec)
        while self.run.value != 0:
            data = rec.record(frame_size)
            now = time.time()

            # check time interval
            interval = now - pre_time
            pre_time = now
            if abs(interval - self.frame_size_sec) / self.frame_size_sec > 1:
                logger.warning("interval error %f / %f", interval, self.frame_size_sec)

            logger.debug("recved %s %f", data.shape, interval)

            self.sound_queue.put(data.reshape(-1))

    def _end_queue(self):
        while not self.sound_queue.empty():
            self.sound_queue.get()
        self.sound_queue.cancel_join_thread()


# sample code
if __name__ == "__main__":
    recode_proc = SoundRecodeProcess()
    recode_proc.start()
    print("start")

    try:
        print("stop ctrl+c")
        pre = time.time()
        while True:
            data = recode_proc.sound_queue.get()
            now = time.time()
            interval = now - pre
            print("recved ", data.shape, interval)
            pre = now
    except queue.Empty:
        print("time out ")
    except KeyboardInterrupt:
        pass
    recode_proc.stop()
    print("stoped")
