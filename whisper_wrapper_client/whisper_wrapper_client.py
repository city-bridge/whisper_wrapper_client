import socket
import json
import numpy as np
from pathlib import Path

WS_REQ_STOP = 0x7F
WS_REQ_RECOG_RAW = 0
WS_REQ_RECOG_FILE = 1
WS_REQ_RECOG_PATH = 2
WS_REQ_TRANS_RAW = 6
WS_REQ_TRANS_FILE = 3
WS_REQ_TRANS_PATH = 4
WS_REQ_SET_INIT_PROMPT = 5

SAMPLE_RATE = 16000
SOUND_INT_MAX = 32767


class WhisperWrapperClient:
    _host: str
    _port: int

    def __init__(self, host, port) -> None:
        self._host = host
        self._port = port

    def server_stop_request(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((socket.gethostbyname(self._host), self._port))
            # send header
            sock.send(bytes([0x00, 0x00, 0x00, WS_REQ_STOP]))
            # recv result
            result = self._recv_data_json(sock)
            return result

    def recognize_raw_audio(self, audio_data: np.ndarray):
        return self.recognize_raw(self._audio_data_to_bytes(audio_data))

    def recognize_raw(self, sound_bytes):
        result = None
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((socket.gethostbyname(self._host), self._port))
            # send header
            sock.send(bytes([0x00, 0x00, 0x00, WS_REQ_RECOG_RAW]))
            # send path
            self._send_bytes(sock, sound_bytes)
            # recv data
            result = self._recv_data_json(sock)
        return result

    def recognize_path(self, path: str):
        return self._send_str_req(WS_REQ_RECOG_PATH, path)

    def transcribe_raw_audio(self, audio_data: np.ndarray):
        return self.transcribe_raw(self._audio_data_to_bytes(audio_data))

    def transcribe_raw(self, sound_bytes):
        return self._send_byte_req(WS_REQ_TRANS_RAW, sound_bytes)

    def transcribe_path(self, path: str):
        return self._send_str_req(WS_REQ_TRANS_PATH, path)

    def set_init_prompt(self, prompt: str):
        return self._send_str_req(WS_REQ_SET_INIT_PROMPT, prompt)

    def recognize_file(self, path):
        result = None
        if not isinstance(path, Path):
            path = Path(str(path))

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((socket.gethostbyname(self._host), self._port))
            # send header
            sock.send(bytes([0x00, 0x00, 0x00, WS_REQ_RECOG_FILE]))
            # send file
            self._send_file_data(sock, path)
            # recv result
            result = self._recv_data_json(sock)
        return result

    def transcribe_file(self, path):
        result = None
        if not isinstance(path, Path):
            path = Path(str(path))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((socket.gethostbyname(self._host), self._port))
            # send header
            sock.send(bytes([0x00, 0x00, 0x00, WS_REQ_TRANS_FILE]))
            # send file
            self._send_file_data(sock, path)
            # recv result
            result = self._recv_data_json(sock)
        return result

    def _send_str_req(self, header: int, send_str: str):
        result = None
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((socket.gethostbyname(self._host), self._port))
            # send header
            sock.send(bytes([0x00, 0x00, 0x00, header]))
            # send path
            self._send_str(sock, send_str)
            # recv data
            result = self._recv_data_json(sock)
        return result

    def _send_byte_req(self, header: int, send_bytes):
        result = None
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((socket.gethostbyname(self._host), self._port))
            # send header
            sock.send(bytes([0x00, 0x00, 0x00, header]))
            # send path
            self._send_bytes(sock, send_bytes)
            # recv data
            result = self._recv_data_json(sock)
        return result

    def _send_str(self, sock: socket.socket, send_str: str):
        # send path data
        send_bytes = bytes(send_str, "utf-8")
        self._send_bytes(sock, send_bytes)

    def _send_bytes(self, sock: socket.socket, send_bytes):
        # send path size
        send_size = len(send_bytes)
        send_size_bytes = int.to_bytes(
            send_size, length=4, byteorder="big", signed=False
        )
        sock.send(send_size_bytes)
        # send path data
        sock.send(send_bytes)

    def _send_file_data(self, sock: socket.socket, path: Path):
        # send path size
        send_size = path.stat().st_size
        send_size_bytes = int.to_bytes(
            send_size, length=4, byteorder="big", signed=False
        )
        sock.send(send_size_bytes)

        # send data
        with path.open("rb") as f:
            i = 0
            while i < send_size:
                data = f.read(1024)
                sock.send(data)
                i = i + len(data)

    def _recv_data_bytearray(self, sock: socket.socket) -> bytearray:
        # recv size
        recv_size_bytes = sock.recv(4)
        recv_size = int.from_bytes(recv_size_bytes, byteorder="big", signed=False)

        # recv data
        recv_bytes = bytearray()
        while len(recv_bytes) < recv_size:
            recv_data_one = sock.recv(recv_size - len(recv_bytes))
            recv_bytes.extend(recv_data_one)

        return recv_bytes

    def _recv_data_json(self, sock: socket.socket) -> dict:
        recv_bytes = self._recv_data_bytearray(sock)
        recv_str = str(recv_bytes, "utf-8")
        json_dict = json.loads(recv_str)
        return json_dict

    def _audio_data_to_bytes(self, sound_data: np.ndarray) -> bytearray:
        # convert pcm 16bit monoral
        (sample_num, ch) = sound_data.shape

        buffer = bytearray(sample_num * 2)

        # -1~1 to -32767 to 32767
        sound_data = sound_data * SOUND_INT_MAX
        sound_data = sound_data.astype(np.int16)
        offset = 0
        for i in range(sample_num):
            sample = int(sound_data[i])
            sample_bytes = int.to_bytes(sample, 2, byteorder="big", signed=True)
            buffer[offset] = sample_bytes[0]
            buffer[offset + 1] = sample_bytes[1]
            offset += 2
        return buffer
