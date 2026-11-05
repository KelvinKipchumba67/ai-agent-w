"""
STEP 2 - Give the LLM ONE tool and do ONE round trip by hand.

This shows the core trick of every agent ("function calling"):
  1. We tell the model which tools exist.
  2. The model replies with a REQUEST to call a tool (not an answer!).
  3. OUR code runs the tool.
  4. We send the result back, and the model writes the final answer.

Run:  python step2_one_tool.py
"""

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools import get_weather, TOOL_DECLARATIONS

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# Only offer the weather tool in this step
weather_tool = types.Tool(function_declarations=[TOOL_DECLARATIONS[0]])
config = types.GenerateContentConfig(tools=[weather_tool])

question = "Will it rain in Mombasa in the next 2 days?"
messages = [types.Content(role="user", parts=[types.Part(text=question)])]

# --- 1st call: the model decides it needs the tool ------------------------
response = client.models.generate_content(
    model=MODEL, contents=messages, config=config)
call = response.function_calls[0]
print(f"1) Model asks us to run: {call.name}({call.args})")

# --- We run the real Python function ---------------------------------------
result = get_weather(**call.args)
print(f"2) Tool returned: {result}")

# --- 2nd call: give the model the tool result ------------------------------
messages.append(response.candidates[0].content)   # the model's request
messages.append(types.Content(role="user", parts=[
    types.Part(function_response=types.FunctionResponse(
        id=call.id, name=call.name, response={"result": result}))
]))
final = client.models.generate_content(
    model=MODEL, contents=messages, config=config)
print(f"3) Final answer:\n{final.text}")
