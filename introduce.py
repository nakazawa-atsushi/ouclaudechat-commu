from anthropic import Anthropic

client = Anthropic()

def tool():
    with open("tool_description.txt","r",encoding="utf-8") as f:
        description = f.read()
    tools = [
        {
            "name": "name_extraction",
            "description": description,
            "input_schema":{
                "type": "object",
                "properties":{
                    "speaker_name":{
                        "type": "string",
                        "description": "Names extracted from conversational text"
                    }
                },
                "required": ["speaker_name"]
            },
        }
    ]
    return tools

def extract_claude(text):
    while True:
        tools = tool()
        res = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            tools=tools,
            messages=[{"role":"user","content":text}]
        )
        print(res)
        print(res.stop_reason)
        if res.stop_reason == "tool_use":
            print(res.content[1].input["speaker_name"])
            break
        else:
            text = input("もう一度お願いします: ")

if __name__ == "__main__":
    text = "私は掃除が好きです"
    extract_claude(text)