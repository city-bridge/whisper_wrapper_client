import numpy as np
from .sound_recode_process import SoundRecodeProcess


class SoundRecodeAndCrop:
    sound_threhold: float
    sound_recode_limit_sec: float
    start_silent_margin_sec: float
    end_silent_margin_sec: float
    start_silent_check_sec: float
    frame_size_sec: float

    def __init__(self):
        self.sound_threhold = 0.001
        self.sound_recode_limit_sec = 5
        self.start_silent_margin_sec = 0.8
        self.end_silent_margin_sec = 0.4
        self.start_silent_check_sec = 0.4
        self.frame_size_sec = 0.2

    def _check_silent(self, audio):
        return (audio**2).max() < self.sound_threhold

    def wait_sound(self):
        recode_proc = SoundRecodeProcess()
        recode_proc.frame_size_sec = self.frame_size_sec
        recode_proc.start()
        max_recode_count = int(self.sound_recode_limit_sec / recode_proc.frame_size_sec)
        start_margin_count = int(
            self.start_silent_margin_sec / recode_proc.frame_size_sec
        )
        end_margin_count = int(self.end_silent_margin_sec / recode_proc.frame_size_sec)
        silent_check_count = int(
            self.start_silent_check_sec / recode_proc.frame_size_sec
        )
        result = None
        try:
            recode_list = []
            silent_check_list = []
            timer_count = 0
            step = 0
            while True:
                one_frame = recode_proc.sound_queue.get(
                    timeout=recode_proc.frame_size_sec * 10
                )
                silent_check_list.append(one_frame)

                if len(silent_check_list) > start_margin_count:
                    return

                check_audio = np.concatenate(
                    silent_check_list[-silent_check_count:], axis=0
                )
                is_silent = self._check_silent(check_audio)

                if step == 0:
                    # wait start
                    if not is_silent:
                        recode_list.extend(silent_check_list)
                        step = 1
                elif step == 1:
                    # wait end
                    if is_silent:
                        step = 2
                    recode_list.append(one_frame)
                    if len(recode_list) > max_recode_count:
                        break
                else:
                    # end margin
                    recode_list.append(one_frame)
                    if timer_count >= end_margin_count:
                        break
                    else:
                        timer_count = timer_count + 1

                silent_check_list.pop(0)
            result = np.array(
                np.concatenate(recode_list, axis=0), dtype=np.float, ndmin=2
            ).T
        finally:
            recode_proc.stop()
        return result


if __name__ == "__main__":
    sound_recode_and_crop = SoundRecodeAndCrop()
    for i in range(3):
        data = sound_recode_and_crop.wait_sound()
        print(data)
