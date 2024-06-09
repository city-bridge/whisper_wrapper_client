import sys
from .whisper_wrapper_client import WhisperWrapperClient


if len(sys.argv) >= 4:
    host = sys.argv[1] 
    port = int(sys.argv[2])
    cmd = sys.argv[3]
    
    client = WhisperWrapperClient(host, port)
    
    if cmd == 'stop':
        client.server_stop_request()
    elif cmd == 'trans_path':
        print(client.transcribe_path(sys.argv[4]))   
    elif cmd == 'recg_path':
        print(client.recognize_path(sys.argv[4]))
    elif cmd == 'recg_file':
        print(client.recognize_file(sys.argv[4]))
    else:
        print(client.transcribe_file(sys.argv[4]))
else:
    print("usage: [host] [port] [cmd] [args]")


