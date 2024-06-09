import json
from pathlib import Path
from whisper_wrapper_client import WhisperWrapperClient
import config


def print_segments(segments):
    for segment in segments:
        print('{}-{}:{}'.format(segment['start'],segment['end'],segment['text']))

def output_segment_text(segments,path:Path):
    with path.open('w') as f:
        for segment in segments:
            f.write('{}-{}:{}'.format(segment['start'],segment['end'],segment['text']))
            f.write('\n')

JAVASCRIPT= (
    'function seek_to_token(start_time){'
    ' audio = document.getElementById("ad");'
    ' audio.currentTime = start_time;}'
    )
HTML_FORMAT=(
    '<html>'
    '<script>{}</script>'
    '<body>'
    '<h1>result</h1>'
    '<audio id="ad" controls src="{}"></audio>'
    '<table border="1">{}</table>'
    '</body>'
    '</html>')
TABLE_ROW_FORMAT=(
    '<tr>'
    '<td onclick="seek_to_token({})">{}</td><td>{}</td><td>{}</td>'
    '<tr>')
def output_html(root_path:Path,audio_name,segments):

    table_html = ''
    for segment in segments:
        row = TABLE_ROW_FORMAT.format(segment['start'],segment['start'],segment['end'],segment['text'])
        table_html = table_html + row

    html_file = root_path/'index.html'
    with html_file.open('w') as f:
        f.write(HTML_FORMAT.format(JAVASCRIPT,audio_name,table_html))
        f.close()

if __name__ == "__main__":
    audio_path_str = 'C:/work/sound/test.MP3'
    client = WhisperWrapperClient(config.SERVER_HOST,config.SERVER_PORT)
    #res = client.transcribe_path(audio_path_str)
    res = client.transcribe_file(audio_path_str)
    audio_path = Path(audio_path_str)
    result_file = audio_path.parent / 'result.json'
    with result_file.open('w') as f:
        f.write(json.dumps(res))
        f.close()
    
    print_segments(res['result']['segments'])
    
    result_file = audio_path.parent / 'result.txt'
    output_segment_text(res['result']['segments'],result_file)

    output_html(audio_path.parent,audio_path.name,res['result']['segments'])

