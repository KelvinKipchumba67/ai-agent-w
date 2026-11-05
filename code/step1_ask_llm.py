"""
STEP 1 - Talk to an LLM. No tools, no agent. Just text in, text out.

Run:  python step1_ask_llm.py
Watch what the model says about LIVE information it cannot know.
"""

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads GEMINI_API_KEY from the .env file
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

question = "What will the weather be in Mombasa this weekend?"

response = client.models.generate_content(model=MODEL, contents=question)

print("QUESTION:", question)
print("\nANSWER:\n" + response.text)
