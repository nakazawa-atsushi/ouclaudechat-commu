import dotenv
import os
import glob
import time
import sys
from anthropic import Anthropic
import random
import base64
import datetime
import argparse
import threading
import socket
from telnetlib import Telnet
from commu_claude_chat import CommuClaudeChat
from play_voicebox import play_voicebox
from local_whisper_mic import WhisperMic
import introduce

dotenv.load_dotenv()
 
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
 
def robot_gesture(x,tn_masaru,tn_kiyoko,tn_takashi,edison_angle_str,pi_angle_str,h_angle_str):
    print("Thread start")
    print(x)
    print(x.empty())
    tn_masaru.write(b"pi_angle=" + pi_angle_str.encode('utf-8') + b"\n")
    tn_kiyoko.write(b"pi_angle=" + pi_angle_str.encode('utf-8') + b"\n")
    tn_takashi.write(b"edison_angle=" + edison_angle_str.encode('utf-8') + b"\n")
    tn_kiyoko.write(b"h=" + h_angle_str.encode('utf-8') + b"\n")
    tn_masaru.write(b"h=" + h_angle_str.encode('utf-8') + b"\n")
    while(True):
        audio.change_event.wait(timeout=0.5)
        if audio.change_event.is_set():
            val = x.get()
            
            print(f"→→→→→→{val}←←←←←")
            try:
                    
                    if val[0] == "たかこ":
                        
                        if val[1] == "joy":
                            tn_takashi.write(b"6\n")
                        elif val[1] == "question":                            
                            tn_takashi.write(b"7\n")
                        elif val[1] == "interest":                            
                            tn_takashi.write(b"8\n")
                        elif val[1] == "surprise":                           
                            tn_takashi.write(b"9\n")
                        else:
                            tn_takashi.write(b"s\n")

                        time.sleep(1.5)
                        tn_masaru.write(b"l\n")
                        tn_kiyoko.write(b"r\n")
                        
                    


                    if val[0] == "きよこ":
                        
                        if val[1] == "joy":
                            print("喜び")
                            tn_kiyoko.write(b"6\n")
                        elif val[1] == "question":
                            print("疑問")
                            tn_kiyoko.write(b"7\n")
                        elif val[1] == "interest":
                            print("興味")
                            tn_kiyoko.write(b"8\n")
                        elif val[1] == "surprise":
                            print("驚き")
                            tn_kiyoko.write(b"9\n")
                        else:
                            tn_kiyoko.write(b"s\n")

                        time.sleep(1.5)
                        tn_takashi.write(b"l\n")  
                        tn_masaru.write(b"s\n")
                  
                    
                    
                    if val[0] == "まさる":
                       
                        if val[1] == "joy":
                            print("喜び")
                            tn_masaru.write(b"6\n")
                        elif val[1] == "question":
                            print("疑問")
                            tn_masaru.write(b"7\n")
                        elif val[1] == "interest":
                            print("興味")
                            tn_masaru.write(b"8\n")
                        elif val[1] == "surprise":
                            print("驚き")
                            tn_masaru.write(b"9\n")    
                        else:
                            tn_masaru.write(b"s\n")                    
                        
                        time.sleep(1.5)
                        tn_kiyoko.write(b"s\n")                        
                        tn_takashi.write(b"r\n")


                    audio.change_event.clear()

                    # time.sleep(5)    
            except ConnectionRefusedError:
                print("接続が拒否されました")
            except TimeoutError:
                print("接続がタイムアウトしました")
            except Exception as e:
                print(f"Telnet不良: {str(e)}")
        
        else:
            # print("pass talker change")
            pass
   
        if audio.talkend_event.is_set():
 
            # time.sleep(1.5)
            tn_masaru.write(b"human_r\n")
            tn_kiyoko.write(b"human_l\n")
            tn_takashi.write(b"s\n")

            audio.talkend_event.clear()
    
    


if __name__ == "__main__":

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
    # print(args.task, args.img_file)
    
    print(args)
    
    convend_flag = False

    if args.task is None:
        print("specify task by option -t [art|art_view|normal] -f image_file")
        sys.exit(0)

    # setup claude
    adapter = CommuClaudeChat()
    audio = play_voicebox()
    # intro = introduce.intro_chat()
    extract = introduce.extract_name()
    
    try:
        mic = WhisperMic(pause=1.2) if args.mic else None
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
    # mic = WhisperMic(pause=0.5) if args.mic else None    
 
    if args.task == "art":
        # art_conv: アートについて語る　モードの場合
        # names = ['まさる','きよこ','たかし']
        personalities = ['アートの初心者','アートの初心者','アートの中級者']
        
        # adapter.set_task("art", names, personalities, experience_flag = args.experience)
    elif args.task == "art_view":
        # art_view_conv: 示された画像について語るモードの場合
        # names = ['まさる','きよこ','たかし']
        personalities = ['アートの初心者','アートの初心者','アートの中級者']
        # adapter.set_task("art_view", names, personalities, args.img_file, experience_flag = args.experience)
    elif args.task == "normal":
        # names = ['まさる','きよこ','たかし']
        personalities = ['average','selfcenter','average']
        # adapter.set_task("normal", names, personalities, experience_flag = args.experience)
    else:
        print("wrong task name.")
        sys.exit(0)
    names = ['まさる','きよこ','たかこ']
    if not args.personality:
        personalities = []

    attributes = [['male','20'],["female","20"],["female","60"]]
    adapter.set_task(args.task, names, personalities, imgfile=args.img_file)
    
    if args.experience:
        adapter.add_experience(attributes)
    
    if args.gesture:
        args.voice = True
        try:
            tn_masaru = Telnet("192.168.2.101", 10001)
            tn_kiyoko = Telnet("192.168.2.103", 10001)
            tn_takashi = Telnet("192.168.2.102", 10001)
            edison_angle_str = input(f"edison角度(デフォルト350): ")
            if edison_angle_str == (""):
                edison_angle_str = "350"
            pi_angle_str = input(f"pi角度(デフォルト800): ")
            if pi_angle_str == (""):
                pi_angle_str = "800"
            h_angle_str = input(f"人間用追加角度(デフォルト250): ")
            if h_angle_str == (""):
                h_angle_str = "250"
            threading.Thread(target=robot_gesture, args=(adapter.q_behavior,tn_masaru,tn_kiyoko,tn_takashi,edison_angle_str,pi_angle_str,h_angle_str,), daemon=True).start()
        except TimeoutError as e:
            print(e)
            print("timeout")
        except Exception as e:
            print(e)
            print("予期しないエラー")
    
    if args.introduce:
        # intro(args, adapter, audio)
        user_input = "こんにちは．60文字以内で自己紹介をお願いします．"
        if args.voice:
            voice_thread = threading.Thread(target=audio.monitor, args=(adapter.q_speech,), daemon=True)
            start_voice_thread(voice_thread)
        # intro.initial_set(args.task, names, personalities, attributes, imgfile=args.img_file, experience_flag = args.experience)
        res = adapter.introduction(user_input)
        if args.voice:
            if voice_thread.is_alive():
                voice_thread.join()
        
    while True:
        if args.mic:
            mic.toggle_microphone()
            user_input = mic.listen()    #
            mic.toggle_microphone()
            print("You said: " + user_input)
        else:
            user_input = input("message: ")
            if user_input == "":
                print("文字を入力してください")
                continue
            
            
        
        # if user_input.lower() == "quit" or user_input == "くいｔ" or user_input == "終了" or user_input == "さようなら":s
        end_words = ["quit","くいｔ","終了","さようなら","さよなら","サヨナラ","サヨウナラ"]
        for end_word in end_words:
            if end_word in user_input.lower():
                print("ありがとうございました．またお会いしましょう.")
                if not args.voice:
                    break
                convend_flag = True

        if args.voice:  # -vフラグが立っていればvoice start
            voice_thread = threading.Thread(target=audio.monitor, args=(adapter.q_speech,), daemon=True)
            start_voice_thread(voice_thread)
            if convend_flag:
                adapter.q_speech.put([names[0],"ありがとうございました．またお会いしましょう."])
                adapter.q_behavior.put([names[0],"joy"])
                adapter.q_speech.put(["*chatend*","*signal*"])
                audio.change_event.set()
                voice_thread.join()
                if args.gesture:
                    tn_masaru.write(b"s\n")
                    tn_kiyoko.write(b"s\n")
                    tn_takashi.write(b"s\n")
                break
        
        if args.introduce:
            user, reason = extract.extract_claude(user_input)
            if not reason == "tool_use":
                print("ごめんなさい．もう一度お名前を教えてもらえますか？")
                if args.voice:
                    adapter.q_speech.put([names[1],"ごめんなさい．うまく聞き取れなかったので，もう一度お名前を教えてもらえますか？"])
                    adapter.q_behavior.put([names[1],"question"])
                    adapter.q_speech.put(["*chatend*","*signal*"])
                    audio.change_event.set()
                    if voice_thread.is_alive():
                        voice_thread.join() 
                continue
            adapter.set_username(user)
            args.introduce = False                

            
        res = adapter.main_conversation(user_input)
        if adapter.streaming == False:
            print(f"{res}")
        print("\n")
            
        if args.voice:
            if voice_thread.is_alive():
                voice_thread.join()
        
        