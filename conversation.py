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
        s.close()

def robottest():
    while True:
        audio.change_event.wait(timeout=1)
        if audio.change_event.is_set():
            print("robot gesture")
            audio.change_event.clear()
        else:
            print("pass talker change")
            
        if audio.talkend_event.is_set():
            print("robot gesture end")
            audio.talkend_event.clear()
            return
    

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
    args = parser.parse_args()
    # print(args.task, args.img_file)

    print(args)

    if args.task is None:
        print("specify task by option -t [art|art_view|normal] -f image_file")
        sys.exit(0)

    # setup claude
    adapter = CommuClaudeChat()
    audio = play_voicebox()
    try:
        mic = WhisperMic() if args.mic else None
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
        names = ['まさる','きよこ','たかし']
        personalities = ['アートの初心者','アートの初心者','アートの中級者']
        adapter.set_task("art", names, personalities)
    elif args.task == "art_view":
        # art_view_conv: 示された画像について語るモードの場合
        names = ['まさる','きよこ','たかし']
        personalities = ['アートの初心者','アートの初心者','アートの中級者']
        adapter.set_task("art_view", names, personalities, args.img_file)
    elif args.task == "normal":
        names = ['まさる','きよこ','たかし']
        personalities = ['average','selfcenter','average']
        adapter.set_task("normal", names, personalities,experience_flag = args.experience)
    else:
        print("wrong task name.")
        sys.exit(0)
        

    while True:
        if args.mic:
            mic.toggle_microphone()
            user_input = mic.listen()
            mic.toggle_microphone()
            print("You said: " + user_input)
        else:
            user_input = input("message: ")
        if user_input.lower() == "quit" or user_input == "くいｔ" or user_input == "終了":
            break
        
        if args.voice:  # -vフラグが立っていればvoice start
            voice_thread = threading.Thread(target=audio.monitor, args=(adapter.q_speech,), daemon=True)
            start_voice_thread(voice_thread)
            
        res = adapter.create_chat(user_input)
        if adapter.streaming == False:
            print(f"{res}")
            
        if args.voice:
            robottest()
            if voice_thread.is_alive():
                voice_thread.join()
        
        