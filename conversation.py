import dotenv
import os
import glob
import sys
from anthropic import Anthropic
import random
import base64
import datetime
import argparse
import CommuClaudeChat from commu_claude_chat

dotenv.load_dotenv()

if __name__ == "__main__":

    # コマンドライン引数を解釈する
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', "--task")     # タスク
    parser.add_argument('-f', "--img_file")
    args = parser.parse_args()
    # print(args.task, args.img_file)

    print(args)

    if args.task is None:
        print("specify task by option -t [art_conv|art_view_conv|normal_conv] -f image_file")
        sys.exit(0)

    # setup claude
    adapter = CommuClaudeChat()
    
    # streaming mode
    if args.streaming == 'on':
        print("streaming mode")
        adapter.streaming = True

    if args.task == "art_conv":
        # art_conv: アートについて語る　モードの場合
        names = ['まさる','きよこ','たかし']
        personalities = ['アートの初心者','アートの初心者','アートの中級者']
        adapter.set_task("art_conv", names, personalities)
    elif args.task == "art_view_conv":
        # art_view_conv: 示された画像について語るモードの場合
        names = ['まさる','きよこ','たかし']
        personalities = ['アートの初心者','アートの初心者','アートの中級者']
        adapter.set_task("art_view_conv", names, personalities, args.img_file)
    elif args.task == "normal_conv":
        names = ['まさる','きよこ','たかし']
        personalities = ['average','selfcenter','average']
        adapter.set_task("normal_conv", names, personalities)
    else:
        print("wrong task name.")
        sys.exit(0)

    while True:
        user_input = input("message: ")
        if user_input.lower() == "quit":
            break

        res = adapter.create_chat(user_input)
        if adapter.streaming == False:
            print(f"{res}")