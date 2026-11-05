"""
check_setup.py - run this FIRST to confirm everything works.

Run:  python check_setup.py
"""

import os
import sys

ok = True
print("Checking your setup...\n")

# 1. Python version
if sys.version_info >= (3, 10):
    print(f"[OK]   Python {sys.version.split()[0]}")
else:
    print(f"[FAIL] Python {sys.version.split()[0]} - please install Python 3.10 or newer")
    ok = False

# 2. Packages
try:
    import requests  # noqa: F401
    from dotenv import load_dotenv
    from google import genai
    print("[OK]   Packages installed")
except ImportError as e:
    print(f"[FAIL] Missing package ({e.name}). Run:  pip install -r requirements.txt")
    sys.exit(1)

# 3. API key
load_dotenv()
key = os.getenv("GEMINI_API_KEY", "")
if not key or key.startswith("paste"):
    print("[FAIL] GEMINI_API_KEY not set. Copy .env.example to .env and paste your key.")
    sys.exit(1)
print("[OK]   API key found in .env")

# 4. Free tool APIs (no key needed)
from tools import get_weather, get_place_info, web_search, TAVILY_API_KEY
for name, fn, args in [
    ("Weather (Open-Meteo)", get_weather, ("Nairobi", 1)),
    ("Wikipedia", get_place_info, ("Nairobi",)),
]:
    try:
        result = fn(*args)
        passed = "error" not in result
        ok = ok and passed
        print(f"{'[OK]  ' if passed else '[FAIL]'} {name}")
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        ok = False

# 4b. Optional web search - a failure here never blocks the workshop
if not TAVILY_API_KEY:
    print("[SKIP] Web search (Tavily): no TAVILY_API_KEY in .env - that's fine, it's optional")
else:
    try:
        result = web_search("Nairobi")
        print("[OK]   Web search (Tavily)" if "error" not in result
              else f"[WARN] Web search (Tavily): {result['error']}")
    except Exception as e:
        print(f"[WARN] Web search (Tavily): {e}")

# 5. Gemini itself
try:
    client = genai.Client(api_key=key)
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    reply = client.models.generate_content(model=model, contents="Reply with just: ready")
    print(f"[OK]   Gemini ({model}) says: {reply.text.strip()}")
except Exception as e:
    print(f"[FAIL] Gemini call failed: {e}")
    ok = False

print("\nAll good - you're ready for the workshop!" if ok else "\nFix the [FAIL] lines above, then run again.")
