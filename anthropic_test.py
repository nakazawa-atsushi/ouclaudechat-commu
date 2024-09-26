from anthropic import Anthropic
import os


client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
model = "claude-3-5-sonnet-20240620"
message = []
system_prompt = ""

path = "experience\omoshiroi\original\\2010001.txt"
path2 = path.replace("\\","/")

with open(path2,"r",encoding="utf-8") as f:
    ex = f.read()

system_prompt = "次の文章から個人的体験を抽出してください"
message = [{"role":"user", "content":ex}]

res = client.messages.create(
    model = model,
    system = system_prompt,
    messages = message,
    max_tokens = 500
)

print(res.content[0].text.strip())

path3 = path.replace("original","sampling")
with open(path3,"w",encoding="utf-8") as f:
    f.write(res.content[0].text.strip())