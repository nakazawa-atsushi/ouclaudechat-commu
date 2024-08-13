import requests
import json
import pyaudio
import threading
import queue
import time
import tempfile
import simpleaudio


# test of threading
# queueを監視するスレッド
class play_voicebox:
    def __init__(self) -> None:
        self.q_audio = queue.Queue()

    def monitor(self,x):
        audio_t = threading.Thread(target=self.audio_play, daemon=True)
        audio_t.start()
        print("Thread start")
        print(x)
        print(x.empty())
        while(True):
            if x.empty() == True:
                time.sleep(0.01)
            else:
                val = x.get()
                print("value = ", val)
                name, buf = val[0], val[1]
                voicetype = self.name_conversion(name)
                self.voicevox(voicetype,buf)
                
                

    def name_conversion(self,name):
        #http://localhost:50021/speakers voicevox起動中にアクセスするとspeaker一覧にアクセスできる
        if name == "まさる":
            voice_type = 2
        elif name == "きよこ":
            voice_type = 3
        elif name == "たかし":
            voice_type = 29
        else:
            print("Undefined name")
            voice_type = 20

        return voice_type

    def voicevox(self, voice_type, text):
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
        self.q_audio.put(voice)
            
        

    def audio_play(self):
        pya = pyaudio.PyAudio()  
        
        while True:
            if self.q_audio.empty() == True:
                time.sleep(0.01)
            else:
                voice = self.q_audio.get()
                # サンプリングレートが24000以外だとずんだもんが高音になったり低音になったりする
                stream = pya.open(format=pyaudio.paInt16,
                                channels=1,
                                rate=24000,
                                output=True)
                
                stream.write(voice)
                stream.stop_stream()
                stream.close()
        pya.terminate()

    """            
    def wavplay(self):
        while True:
            if self.q_audio.empty() == True:
                time.sleep(0.01)
            else:
                voice = self.q_audio.get()
                with tempfile.TemporaryDirectory() as tmp:
                    with open(f"{tmp}/audi.wav", "wb") as f:
                        f.write(voice)
                        wav_obj = simpleaudio.WaveObject.from_wave_file(f"{tmp}/audi.wav")
                        play_obj = wav_obj.play() #Starts playback of the audio
                        play_obj.wait_done() #Waits for the playback job to finish before returning.
    """