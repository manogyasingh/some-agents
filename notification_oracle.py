from dotenv import load_dotenv
import anthropic
import subprocess
import os
load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_KEY'))

answer = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=1000,
    temperature=0,
    system="You answer questions concisely and precisely. If there are options, you tell which one is correct.",
    messages=[{
        "role": "user",
        "content": [{
            "type": "text",
            "text": subprocess.check_output(['wl-paste'], text=True).strip()
            }]
        }]
).content[0].text

subprocess.run(['notify-send', "Oracle", answer])
exit()