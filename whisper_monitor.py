from local_whisper_mic import WhisperMic

def monitor():
    try:
        mic = WhisperMic(pause=1.5,energy=200,dynamic_energy=True,hallucinate_threshold=300)
    except AssertionError as e:
        print(f"AsserionError: {e}")
        print("テキスト入力でプログラムを実行します")
    except AttributeError as e:
        print(f"AttributeError: {e}")
        print("マイクの接続を確認してください")
        print("テキスト入力でプログラムを実行します")
    except Exception as e:
        print(f"予期しないエラー: {e}")
        print("テキスト入力でプログラムを実行します")


    
    while True:
        mic.toggle_microphone()
        user_input = mic.listen(try_again=False)  #
        mic.toggle_microphone()
        if user_input == None:
            print("**************認識できません***************")
        else: 
            print("You said: " + user_input)
        

        

