import requests
import json
import pyaudio
import threading
import queue
import time


def play_voicebox(self, voice_type, text):
    # エンジン起動時に表示されているIP、portを指定
    host = "127.0.0.1"
    port = 50021

    # 音声化する文言と話者を指定
    params = (
        ('text', text),
        ('speaker', voice_type),
    )

    # 音声合成用のクエリ作成
    query = requests.post(
        f'http://{host}:{port}/audio_query',
        params=params
    )

    # 音声合成を実施
    synthesis = requests.post(
        f'http://{host}:{port}/synthesis',
        headers = {"Content-Type": "application/json"},
        params = params,
        data = json.dumps(query.json())
    )

    voice = synthesis.content
    pya = pyaudio.PyAudio()  
                
        # サンプリングレートが24000以外だとずんだもんが高音になったり低音になったりする
    stream = pya.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=24000,
                    output=True)

    stream.write(voice)
    stream.stop_stream()
    stream.close()
    pya.terminate()
        
            

class Play_Voicebox_Stream(threading.Thread):
    def __init__(self, voice_type, text):
        super().__init__(daemon=True)
        self.voice_type= voice_type
        self.text = text
        self.voice = None
        self.lock = threading.Lock()
        self.voice_switch = True
        self.play_switch = True
    
    def fetch_voice(self) :
        # エンジン起動時に表示されているIP、portを指定
        host = "127.0.0.1"
        port = 50021
        
        # 音声化する文言と話者を指定
        params = (
            ('text', self.text),
            ('speaker', self.voice_type),
        )
        
        # 音声合成用のクエリ作成
        query = requests.post(
            f'http://{host}:{port}/audio_query',
            params=params
        )
        
        # 音声合成を実施
        synthesis = requests.post(
            f'http://{host}:{port}/synthesis',
            headers = {"Content-Type": "application/json"},
            params = params,
            data = json.dumps(query.json())
        )
        
        # 再生処理
        with self.lock:
            self.voice = synthesis.content
        self.voice_switch = False
    
    
    def play_voice(self):
        while True:
            with self.lock:
                if self.voice is not None:
                    voice = self.voice
                    self.voice = None
                else:
                    if not self.voice_switch and not self.play_switch:
                        return
                    time.sleep(0.1)
                    continue
            
            pya = pyaudio.PyAudio()  
                  
            # サンプリングレートが24000以外だとずんだもんが高音になったり低音になったりする
            stream = pya.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=24000,
                            output=True)
            
            stream.write(voice)
            stream.stop_stream()
            stream.close()
            pya.terminate()
            self.play_switch = False
        
    def run(self):
        play_t = threading.Thread(target=self.play_voice, daemon=True)
        play_t.start()
        self.fetch_voice()
        play_t.join()