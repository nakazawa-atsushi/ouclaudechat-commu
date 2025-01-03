import requests
import json
import pyaudio
import threading
import queue
import time
import re
import alkana

# test of threading
# queueを監視するスレッド
class play_voicebox:
    def __init__(self) -> None:
        self.q_audio = queue.Queue()
        self.voiceend_flag = False
        self.change_event = threading.Event()
        self.talkend_event = threading.Event()
        self.talkstart_flag = False
        self.nod_event = threading.Event()
        self.nod_event.set()

    def monitor(self, x:queue, namelist):
        audio_t = threading.Thread(target=self.audio_play, daemon=True)
        audio_t.start()
        print("Thread start")
        print(x)
        print(x.empty())
        memory_voicetype = None
        while(True):
            if x.empty() == True:
                time.sleep(0.1)
            else:
                val = x.get()
                # print("value = ", val)
                name, buf = val[0], val[1]
                if name == "*chatstart*" and buf == "*signal*":
                    print("chat start")
                    self.change_event.set()
                    continue
                if name == "*chatend*" and buf == "*signal*": #chatから出力が最後の合図を受け取ったら
                    print("voice end")
                    self.voiceend_flag = True
                    audio_t.join()  #音声再生が終了するまでストップ
                    self.talkend_event.set()    #robotgesture用のイベント
                    print(f"talkeventflag is {self.talkend_event.is_set()}")
                    self.talkstart_flag = False
                    return
                voicetype = self.name_conversion(name,namelist)
                
                delay_flag = False
                if not memory_voicetype:
                    memory_voicetype = voicetype
                elif not memory_voicetype == voicetype: #話者が変わったらdelay_flagをTrueにする
                    delay_flag = True
                    memory_voicetype = voicetype
                
                buf = self.english_convert(buf) #英単語をカタカナ読みに変換(できない単語もある)
                self.voicevox(voicetype,buf,delay_flag)
                
                

    def name_conversion(self,name,namelist):
        #http://localhost:50021/speakers voicevox起動中にアクセスするとspeaker一覧にアクセスできる
        if name == namelist[1]: #まさる
            voice_type = 11
            #2は四国メタン、11は玄野武宏
        elif name == namelist[2]:   #きよこ
            voice_type = 46
            # 小夜
            # 雨晴はう 10
        elif name == namelist[0]:   #たかこorたかし
            voice_type = 20
            # もち子さん
        else:
            print("Undefined name")
            voice_type = 20

        return voice_type

    def english_convert(self, text):
        english_words = re.findall(r'[a-zA-Z]+', text)
        for word in english_words:
            katakana_word = alkana.get_kana(word)
            # 英単語をカタカナに置き換え
            if katakana_word == "" or katakana_word == None:
                print(f"変換できませんでした {word}")
                continue
            text = text.replace(word, katakana_word)
        return text

    def voicevox(self, voice_type, text, delay_flag:bool):
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
        if delay_flag:  #delay_flagがtrueならqueueに"delay"文字列を追加
            self.q_audio.put("*delay*")
        self.q_audio.put(voice)
            
        
    def audio_play(self):
        while True:
            try:
                self.nod_event.wait()
                voice = self.q_audio.get_nowait()
            except queue.Empty:
                if self.voiceend_flag:  #もし音声合成がすべて終了した後にq.audio(queue)が空なら，音声再生も終わったと判断する
                    print("def audioplay return")
                    self.voiceend_flag = False  #flagを元に戻してからreturn
                    return
                time.sleep(0.1)
                continue
                        
            if voice == "*delay*":    #getした文字が"delay"なら音声出力せずに1秒間sleep
                print("delay")
                self.change_event.set()
                time.sleep(1)
                continue
            
            pya = pyaudio.PyAudio()
            # サンプリングレートが24000以外だとずんだもんが高音になったり低音になったりする
            stream = pya.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=24000,
                            output=True)
            time.sleep(0.15)    #これがないと音声を開始するたびにぶつぶつ音が鳴ります（0.15より短くしてもなります）
            stream.write(voice) #音声再生
            # cpu = stream.get_cpu_load()   #Return the CPU load. Always 0.0 when using the blocking API.
            # stream.stop_stream()  #stop_stream, close, terminateを使用すると音声の末尾が途中で切れます
            # stream.close()
            # pya.terminate()