"""
BONUS - the same Safari agent, but the Gemini SDK runs the loop for us.

Same prompt, same tools, same memory, same step limit as agent.py.
The difference: we hand the SDK plain Python functions and it does the rest.
"""

from google.genai import types

# Reuse agent.py's client, prompt and settings, so we only compare the machinery
from agent import (client, MODEL, MAX_STEPS, SYSTEM_PROMPT,
                   YELLOW, GREEN, GREY, RESET)
from tools import TOOL_FUNCTIONS

config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    tools=list(TOOL_FUNCTIONS.values()),  # plain Python functions, no menu!
    automatic_function_calling=types.AutomaticFunctionCallingConfig(
        maximum_remote_calls=MAX_STEPS),  # same safety limit as agent.py
)


def new_chat(history=None):
    """A chat object is the SDK's version of our `messages` memory list."""
    return client.chats.create(model=MODEL, config=config, history=history)


def main():
    print(f"{GREEN}Safari agent ready ({MODEL}, SDK shortcut).{RESET}")
    print(f"{GREY}Tools: {', '.join(TOOL_FUNCTIONS)}. Type 'quit' to exit.{RESET}\n")
    chat = new_chat()  # MEMORY: the chat remembers every turn for us
    while True:
        question = input(f"{YELLOW}You: {RESET}").strip()
        if question.lower() in {"quit", "exit", "q"}:
            break
        if not question:
            continue
        checkpoint = len(chat.get_history())
        try:
            reply = chat.send_message(question)  # the WHOLE agent loop, in 1 line
            if reply.function_calls:  # still asking for tools: hit MAX_STEPS
                chat = new_chat(chat.get_history()[:checkpoint])
                answer = "Sorry, I hit my step limit before finishing. Try a simpler question."
            else:
                answer = reply.text
        except Exception as e:
            # The SDK saves history as it goes, so forget the half-finished turn
            chat = new_chat(chat.get_history()[:checkpoint])
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                answer = "Rate limit reached on the free tier. Wait a minute and try again."
            else:
                answer = f"Something went wrong: {e}"
        print(f"\n{GREEN}Safari:{RESET} {answer}\n")


if __name__ == "__main__":
    main()
