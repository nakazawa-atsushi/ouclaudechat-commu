import dotenv
import os
import glob
import time
import sys
import PySimpleGUI as sg
from anthropic import Anthropic
import random
import base64
import datetime
import argparse
import threading
import socket
from telnetlib import Telnet
from   commu_claude_chat import CommuClaudeChat
from   play_voicebox import play_voicebox
from   local_whisper_mic import WhisperMic
import introduce

# load environment for Claude
dotenv.load_dotenv()

# global variable to access from window processing
mic = None


def start_voice_thread(voice_t:threading):
    print("voice start")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
    try:
        s.connect(("127.0.0.1",50021))
        s.close()
        print("通信成功")
        voice_t.start()
    except socket.error as e:
        print("エラー発生:",e)
        print("voicevoxを起動してください")
        print("音声出力無しで実行します")
        args.voice = False
        s.close()

def robot_write(tn,command):
    if tn is not None:
        tn.write(command)

def connect_robot(ip,commnad):
    try:
        tn = Telnet(ip, commnad)
    except TimeoutError as e:
        print(e)
        print("timeout")
        tn = None
    except Exception as e:
        print(e)
        print("予期しないエラー")
        tn = None

    return tn
    """    
    edison_angle_str = input(f"edison角度(デフォルト300): ")
    if edison_angle_str == (""):
        edison_angle_str = "300"
    pi_angle_str = input(f"pi角度(デフォルト850): ")
    if pi_angle_str == (""):
        pi_angle_str = "850"
    h_angle_str = input(f"人間用追加角度(デフォルト300): ")
    if h_angle_str == (""):
        h_angle_str = "300"
    threading.Thread(target=robot_gesture, args=(adapter.q_behavior,tn_masaru,tn_kiyoko,tn_takashi,edison_angle_str,pi_angle_str,h_angle_str,names,), daemon=True).start()
    """

def robot_gesture(x, tn_masaru, tn_kiyoko, tn_takashi, edison_angle_str, pi_angle_str, h_angle_str, names):
    print("Thread start")
    print(x)
    print(x.empty())
    robot_write(tn_masaru, b"pi_angle=" + pi_angle_str.encode('utf-8') + b"\n")
    robot_write(tn_kiyoko, b"pi_angle=" + pi_angle_str.encode('utf-8') + b"\n")
    robot_write(tn_takashi, b"edison_angle=" + edison_angle_str.encode('utf-8') + b"\n")
    robot_write(tn_kiyoko, b"h=" + h_angle_str.encode('utf-8') + b"\n")
    robot_write(tn_masaru, b"h=" + h_angle_str.encode('utf-8') + b"\n")
    
    while(True):
        audio.change_event.wait(timeout=0.1)

        if mic.micend_event.is_set():
            while True:
                if audio.change_event.is_set():
                    print("nod break")
                    break
                audio.nod_event.clear()
                tn = random.choice(range(1, 4-names.count("")))
                if tn == 1:
                    robot_write(tn_takashi, b"nod\n")
                elif tn == 2:
                    robot_write(tn_masaru, b"nod_r\n")
                elif tn == 3:
                    robot_write(tn_kiyoko, b"nod_l\n")
                print("sleep before")
                time.sleep(2.5)
            audio.nod_event.set()
            mic.micend_event.clear()

        if audio.change_event.is_set():
            val = x.get()
            
            print(f"→→→→→→{val}←←←←←")
            try:
                if val[0] == names[0]:
                    if val[1] == "joy":
                        robot_write(tn_takashi, b"6\n")
                    elif val[1] == "question":                            
                        robot_write(tn_takashi, b"7\n")
                    elif val[1] == "interest":                            
                        robot_write(tn_takashi, b"8\n")
                    elif val[1] == "surprise":                           
                        robot_write(tn_takashi, b"9\n")
                    else:
                        robot_write(tn_takashi, b"8\n")

                    time.sleep(1.5)
                    robot_write(tn_masaru, b"l\n")
                    robot_write(tn_kiyoko, b"r\n")
                
                if val[0] == names[2]:
                    if val[1] == "joy":
                        print("喜び")
                        robot_write(tn_kiyoko, b"6\n")
                    elif val[1] == "question":
                        print("疑問")
                        robot_write(tn_kiyoko, b"7\n")
                    elif val[1] == "interest":
                        print("興味")
                        robot_write(tn_kiyoko, b"8\n")
                    elif val[1] == "surprise":
                        print("驚き")
                        robot_write(tn_kiyoko, b"9\n")
                    else:
                        robot_write(tn_kiyoko, b"8\n")

                    time.sleep(1.5)
                    robot_write(tn_takashi, b"l\n")  
                    robot_write(tn_masaru, b"s\n")
                
                if val[0] == names[1]:
                    if val[1] == "joy":
                        print("喜び")
                        robot_write(tn_masaru, b"6\n")
                    elif val[1] == "question":
                        print("疑問")
                        robot_write(tn_masaru, b"7\n")
                    elif val[1] == "interest":
                        print("興味")
                        robot_write(tn_masaru, b"8\n")
                    elif val[1] == "surprise":
                        print("驚き")
                        robot_write(tn_masaru, b"9\n")    
                    else:
                        robot_write(tn_masaru, b"8\n")                    
                    
                    time.sleep(1.5)
                    robot_write(tn_kiyoko, b"s\n")                        
                    robot_write(tn_takashi, b"r\n")

                audio.change_event.clear()
            except ConnectionRefusedError:
                print("接続が拒否されました")
            except TimeoutError:
                print("接続がタイムアウトしました")
            except IndexError:
                print("配列が範囲外です")
            except Exception as e:
                print(f"Telnet不良: {str(e)}")
        
        if audio.talkend_event.is_set():
            print("human turn")
            robot_write(tn_masaru, b"human_r\n")
            robot_write(tn_kiyoko, b"human_l\n")
            robot_write(tn_takashi, b"s\n")
            audio.talkend_event.clear()

def mainloop():
    global mic

    # コマンドライン引数を解釈する
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', "--task",default="normal")     # タスク
    parser.add_argument('-f', "--img_file")
    parser.add_argument('-v', '--voice',action='store_true',
                        help="指定したらvoicevoxを使用する(フラグ)")
    parser.add_argument('-m', '--mic', action='store_true',
                        help="指定したらマイク入力になる(フラグ)")
    parser.add_argument("-e", "--experience", action= "store_true",
                        help="個人的体験をclaudeに与える(フラグ)")
    parser.add_argument("-i", "--introduce", action= "store_true",
                        help="自己紹介をする(フラグ)")
    parser.add_argument("-p", "--personality", action= "store_true",
                        help="性格特性を付与する(フラグ)")
    parser.add_argument("-g", "--gesture", action= "store_true",
                        help="ロボットのジェスチャ(フラグ)")
    args = parser.parse_args()
    
    convend_flag = False
    robots_number = 2
    if args.task == "shikata":
        robots_number = 1

    if args.task is None:
        print("specify task by option -t [art|art_view|normal] -f image_file")
        sys.exit(0)

    # WisperMic Parameters
    wm_pause = 1.0
    wm_energy = 200
    wm_dynamic_energy = True
    wm_hallucinate_threshold = 100

    # setup claude
    adapter = CommuClaudeChat()
    audio = play_voicebox()
    # intro = introduce.intro_chat()
    extract = introduce.extract_name()

    try:
        if args.mic:
            mic = WhisperMic(pause=wm_pause, energy=wm_energy, 
                             dynamic_energy=wm_dynamic_energy, 
                             hallucinate_threshold=wm_hallucinate_threshold)
    except AssertionError as e:
        print(f"AsserionError: {e}")
        print("テキスト入力でプログラムを実行します")
        args.mic = False
    except AttributeError as e:
        print(f"AttributeError: {e}")
        print("マイクの接続を確認してください")
        print("テキスト入力でプログラムを実行します")
        args.mic = False
    except Exception as e:
        print(f"予期しないエラー: {e}")
        print("テキスト入力でプログラムを実行します")
        args.mic = False

    if args.task == "art":
        # art_conv: アートについて語る　モードの場合
        # names = ['まさる','きよこ','たかし']
        personalities = ['アートの初心者','アートの初心者','アートの中級者']
    elif args.task == "art_view":
        # art_view_conv: 示された画像について語るモードの場合
        # names = ['まさる','きよこ','たかし']
        personalities = ['アートの初心者','アートの初心者','アートの中級者']
    elif args.task == "normal":
        # names = ['まさる','きよこ','たかし']
        personalities = ['average','selfcenter','average']
    elif args.task == "shikata":
        names = ['たかこ',"",""]
        personalities = ["average"]
    else:
        print("wrong task name.")
        sys.exit(0)

    if not args.task == "shikata":
        names = ['たかこ',"",""]
        if robots_number >= 2:
            names[1] = "まさる"
        if robots_number >= 3:
            names[2] = "きよこ"

    if not args.personality:
        personalities = []
    adapter.set_task(args.task, names, personalities, imgfile=args.img_file)
    
    if args.experience:
        attributes = [['male','20'],["female","20"],["female","60"]]
        adapter.add_experience(attributes)
    
    if args.gesture:
        args.voice = True
        tn_masaru = None
        tn_kiyoko = None
        tn_takashi = None
        
        if robots_number >= 1:
            tn_takashi = connect_robot("192.168.2.102", 10001)
        if robots_number >= 2:
            tn_masaru = connect_robot("192.168.2.101", 10001)
        if robots_number >= 3:
            tn_kiyoko = connect_robot("192.168.2.103", 10001)
            
        edison_angle_str = input(f"edison角度(デフォルト300): ")
        if edison_angle_str == (""):
            edison_angle_str = "300"
        pi_angle_str = input(f"pi角度(デフォルト850): ")
        if pi_angle_str == (""):
            pi_angle_str = "850"
        h_angle_str = input(f"人間用追加角度(デフォルト300): ")
        if h_angle_str == (""):
            h_angle_str = "300"
        threading.Thread(target=robot_gesture, args=(adapter.q_behavior,tn_masaru,tn_kiyoko,tn_takashi,edison_angle_str,pi_angle_str,h_angle_str,names,), daemon=True).start()
    
    if args.introduce:
        # intro(args, adapter, audio)
        user_input = "こんにちは．60文字以内で自己紹介をお願いします．"
        if args.voice:
            voice_thread = threading.Thread(target=audio.monitor, args=(adapter.q_speech,names,), daemon=True)
            start_voice_thread(voice_thread)
        # intro.initial_set(args.task, names, personalities, attributes, imgfile=args.img_file, experience_flag = args.experience)
        res = adapter.introduction(user_input)
        if args.voice:
            if voice_thread.is_alive():
                voice_thread.join()
    else:
        if args.gesture:
            robot_write(tn_masaru,b"human_r\n")
            robot_write(tn_kiyoko,b"human_l\n")
            robot_write(tn_takashi,b"s\n")            
            # tn_masaru.write(b"human_r\n")
            # tn_kiyoko.write(b"human_l\n")
            # tn_takashi.write(b"s\n")

    while True:
        if args.mic:
            mic.toggle_microphone()
            user_input = mic.listen(try_again=False)
            mic.toggle_microphone()
            if user_input != None:
                print("You said: " + user_input)
        else:
            user_input = input("message: ")
            if user_input == "":
                print("文字を入力してください")
                continue

        if user_input == None:
            print("ごめんなさい、聞き取れなかったので、もう一度お願いします。")
            if args.voice:
                voice_thread = threading.Thread(target=audio.monitor, args=(adapter.q_speech,names), daemon=True)
                start_voice_thread(voice_thread)
                adapter.q_speech.put([names[0],"ごめんなさい、聞き取れなかったので、もう一度お願いします。"])
                adapter.q_behavior.put([names[0],"question"])
                adapter.q_speech.put(["*chatend*","*signal*"])
                audio.change_event.set()
                if voice_thread.is_alive():
                    voice_thread.join()
                continue

        end_words = ["quit","くいｔ","終了","さようなら","さよなら","サヨナラ","サヨウナラ","사요나라","사요 나라","사연하라","Sådär då","sayonara","sayounara"]
        for end_word in end_words:
            if end_word in user_input.lower():
                print("ありがとうございました．またお会いしましょう.")
                if not args.voice:
                    sys.exit(0)
                convend_flag = True

        if args.voice:  # -vフラグが立っていればvoice start
            voice_thread = threading.Thread(target=audio.monitor, args=(adapter.q_speech,names), daemon=True)
            start_voice_thread(voice_thread)
            if convend_flag:
                adapter.q_speech.put([names[0],"ありがとうございました．またお会いしましょう."])
                adapter.q_behavior.put([names[0],"joy"])
                adapter.q_speech.put(["*chatend*","*signal*"])
                audio.change_event.set()
                voice_thread.join()
                if args.gesture:
                    robot_write(tn_masaru,b"s\n")
                    robot_write(tn_kiyoko,b"s\n")
                    robot_write(tn_takashi,b"s\n")                    
                    # tn_masaru.write(b"s\n")
                    # tn_kiyoko.write(b"s\n")
                    # tn_takashi.write(b"s\n")
                break

        # if user_input.lower() == "quit" or user_input == "くいｔ" or user_input == "終了" or user_input == "さようなら":s
        if args.introduce:
            user, reason = extract.extract_claude(user_input)
            if not reason == "tool_use":
                print("ごめんなさい．もう一度お名前を教えてもらえますか？")
                if args.voice:
                    adapter.q_speech.put([names[0],"ごめんなさい．うまく聞き取れなかったので，もう一度お名前を教えてもらえますか？"])
                    adapter.q_behavior.put([names[0],"question"])
                    adapter.q_speech.put(["*chatend*","*signal*"])
                    audio.change_event.set()
                    if voice_thread.is_alive():
                        voice_thread.join() 
                continue
            adapter.set_username(user)
            args.introduce = False                

        if args.task == "shikata":
            res = adapter.shikata_conversation(user_input)
        else:
            res = adapter.main_conversation(user_input)
            
        if adapter.streaming == False:
            print(f"{res}")
        print("\n")
            
        if args.voice:
            if voice_thread.is_alive():
                voice_thread.join()

def sg_status_update(window):
    global mic

    while(True):
        if mic is not None:
            amp = mic.current_audio_amplitude
            pause = mic.pause
            energy = mic.energy
            denergy = mic.dynamic_energy
            hthresh = mic.hallucinate_threshold
            window.write_event_value("EVAL_UPDATE", (True, amp, pause, energy, denergy, hthresh))
        else:
            window.write_event_value("EVAL_UPDATE", (False, 0))

        time.sleep(0.1)

if __name__ == "__main__":
    # メインプログラムを起動する
    thread = threading.Thread(target=mainloop, name='mainloop',daemon = True)
    thread.start()

    # ウィンドウの作成
    layout = [[sg.Text("Current Sound LV"), sg.Text("", key="SOUND_LV")],
              [sg.HorizontalSeparator(color='red')],
                [sg.Text("Pause", size=(20,1)),  sg.Text("0", key="PAUSE", size=(10,1)),   sg.Slider((0.0, 5.0), orientation='horizontal', key="PAUSE_IN", enable_events=True)],
                [sg.Text("Energy", size=(20,1)), sg.Text("0", key="ENERGY", size=(10,1)),  sg.Slider((0.0, 500), orientation='horizontal', key="ENERGY_IN", enable_events=True)],
                [sg.Text("Hallucinate Thresh", size=(20,1)), sg.Text("0", key="HTHRESH", size=(10,1)), sg.Slider((0, 500), orientation='horizontal', key="HTHRESH_IN", enable_events=True)],
                [sg.Button("Set Default Parameters", key="SETDEFALUT")]]                                                
    window = sg.Window("CommU Conversation Control", layout, finalize=True)

    # 評価値をアップデートする関数
    window.start_thread(lambda: sg_status_update(window), "EVAL_FINISH")

    while True:
        # windows processing
        event, values = window.read()

        if event is None:
            print("stop application")
            break;

        if event == "EVAL_UPDATE":
            # micのステータスがアップデートされた
            if values["EVAL_UPDATE"][0] == True:
                amp = float(values["EVAL_UPDATE"][1])
                pause = float(values["EVAL_UPDATE"][2])
                energy = float(values["EVAL_UPDATE"][3])
                #denergy = float(values["EVAL_UPDATE"][4])
                hthresh = float(values["EVAL_UPDATE"][5])
                
                window["SOUND_LV"].update(value=f"{amp}")
                window["PAUSE"].update(value=pause)
                window["ENERGY"].update(value=energy)
                #window["DENERGY"].update(value=denergy)
                window["HTHRESH"].update(value=hthresh)

                window["PAUSE_IN"].update(value=pause)
                window["ENERGY_IN"].update(value=energy)
                #window["DENERGY_IN"].update(value=denergy)
                window["HTHRESH_IN"].update(value=hthresh)

        if event == "HTHRESH_IN":
            value = float(values['HTHRESH_IN'])
            mic.hallucinate_threshold = value

        if event == "ENERGY_IN":
            value = float(values['ENERGY_IN'])
            mic.energy = value

        if event == "PAUSE_IN":
            value = float(values['PAUSE_IN'])
            mic.pause = value                        

        if event == "SETDEFAULT":
            if mic is not None:
                mic.pause = 1.0
                mic.energy = 200
                mic.dynamic_energy = True
                mic.hallucinate_threshold = 100

    window.close()