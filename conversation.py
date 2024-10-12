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
 
        
# def intro(args:argparse, adapter:CommuClaudeChat, audio:play_voicebox):
#     if args.voice:
#         voice_thread = threading.Thread(target=audio.monitor, args=(adapter.q_speech,), daemon=True)
#         start_voice_thread(voice_thread)
#     adapter.create_chat("まずは短く自己紹介しましょう")
#     if args.voice:
#         if voice_thread.is_alive():
#             voice_thread.join()
    
    


if __name__ == "__main__":

    # コマンドライン引数を解釈する
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', "--task")     # タスク
    parser.add_argument('-f', "--img_file")
    parser.add_argument('-v', '--voice',action='store_true',
                        help="指定したらvoicevoxを使用する(フラグ)")
    parser.add_argument('-m', '--mic', action='store_true',
                        help="指定したらマイク入力になる(フラグ)")
    parser.add_argument("-e", "--experience", action= "store_true",
                        help="個人的体験をclaudeに与える(フラグ)")
    parser.add_argument("-i", "--introduce", action= "store_true",
                        help="自己紹介をする(フラグ)")
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
        mic = WhisperMic(pause=0.5) if args.mic else None
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
    attributes = [['male','20'],["female","20"],["female","60"]]
    adapter.set_task(args.task, names, personalities, attributes, imgfile=args.img_file, experience_flag = args.experience)
    
    
    if args.introduce:
        # intro(args, adapter, audio)
        user_input = "こんにちは．40文字以内で自己紹介をお願いします．"
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
            
        if args.introduce:
            user, reason = extract.extract_claude(user_input)
            if not reason == "tool_use":
                print("ごめんなさい．もう一度お名前を教えてもらえますか？")
                if args.voice:
                    voice_thread = threading.Thread(target=audio.monitor, args=(adapter.q_speech,), daemon=True)
                    start_voice_thread(voice_thread)
                    adapter.q_speech.put([names[1],"ごめんなさい．うまく聞き取れなかったので，もう一度お名前を教えてもらえますか？"])
                    adapter.q_speech.put(["*chatend*","*signal*"])
                    voice_thread.join() 
                continue
            adapter.set_username(user)
            args.introduce = False                
            
        
        # if user_input.lower() == "quit" or user_input == "くいｔ" or user_input == "終了" or user_input == "さようなら":s
        if user_input.lower() in ["quit","くいｔ","終了","さようなら","さよなら"]:
            print("ありがとうございました．またお会いしましょう.")
            if not args.voice:
                break
            convend_flag = True
        
        if args.voice:  # -vフラグが立っていればvoice start
            voice_thread = threading.Thread(target=audio.monitor, args=(adapter.q_speech,), daemon=True)
            start_voice_thread(voice_thread)
            if convend_flag:
                adapter.q_speech.put([names[1],"ありがとうございました．またお会いしましょう."])
                adapter.q_behavior.put([names[1]],"joy")
                adapter.q_speech.put(["*chatend*","*signal*"])
                voice_thread.join()
                break
            
        res = adapter.main_conversation(user_input)
        if adapter.streaming == False:
            print(f"{res}")
        print("\n")
            
        if args.voice:
            if voice_thread.is_alive():
                voice_thread.join()
        
        