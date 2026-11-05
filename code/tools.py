"""
tools.py - the agent's "hands".

Each tool is just a normal Python function that calls a web API.
The LLM never runs these itself. It only ASKS us to run them,
and our code (agent.py) does the actual calling.

  get_weather     Open-Meteo   free, no key
  get_place_info  Wikipedia    free, no key
  web_search      Tavily       free plan, needs TAVILY_API_KEY (optional)
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()
TIMEOUT = 20  # seconds - never let one slow API freeze the whole agent
HEADERS = {"User-Agent": "SafariAgentWorkshop/1.0 (student learning project)"}


# ---------------------------------------------------------------------------
# Tool 1: weather forecast  (Open-Meteo - https://open-meteo.com)
# ---------------------------------------------------------------------------

# Open-Meteo returns a number code for the weather. We translate it to words.
WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "fog", 51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain", 80: "rain showers",
    81: "rain showers", 82: "violent rain showers", 95: "thunderstorm",
    96: "thunderstorm with hail", 99: "thunderstorm with hail",
}
DAILY_FIELDS = ("weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_probability_max")


def get_weather(city: str, days: int = 3) -> dict:
    """Daily weather forecast for a city, for the next `days` days (1-7)."""
    days = max(1, min(int(days), 7))

    # API call 1: turn the city name into latitude / longitude
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        headers=HEADERS, timeout=TIMEOUT,
    ).json()
    if not geo.get("results"):
        return {"error": f"Could not find a place called '{city}'."}
    place = geo["results"][0]

    # API call 2: ask for the forecast at that location
    data = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": place["latitude"], "longitude": place["longitude"],
                "daily": DAILY_FIELDS, "timezone": "auto", "forecast_days": days},
        headers=HEADERS, timeout=TIMEOUT,
    ).json()
    if data.get("error"):  # e.g. 503 "The service is overloaded"
        return {"error": f"Weather service problem: {data.get('reason', 'unknown')}"}

    # Reshape: parallel lists -> one small dict per day
    daily = data["daily"]
    forecast = []
    for i, date in enumerate(daily["time"]):
        forecast.append({
            "date": date,
            "summary": WEATHER_CODES.get(daily["weather_code"][i], "mixed"),
            "max_c": daily["temperature_2m_max"][i],
            "min_c": daily["temperature_2m_min"][i],
            "chance_of_rain_pct": daily["precipitation_probability_max"][i],
        })
    return {"city": place["name"], "country": place.get("country"),
            "forecast": forecast}


# ---------------------------------------------------------------------------
# Tool 2: facts about a place  (Wikipedia - https://www.mediawiki.org/wiki/API)
# ---------------------------------------------------------------------------

def get_place_info(topic: str) -> dict:
    """Short Wikipedia introduction about a place, park or landmark."""
    data = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query", "format": "json",
            "generator": "search", "gsrsearch": topic, "gsrlimit": 1,
            "prop": "extracts", "exintro": 1, "explaintext": 1,
            "redirects": 1,
        },
        headers=HEADERS, timeout=TIMEOUT,
    ).json()
    if data.get("error"):  # e.g. {"error": {"code": "...", "info": "..."}}
        return {"error": f"Wikipedia problem: {data['error'].get('info', 'unknown')}"}
    pages = data.get("query", {}).get("pages")
    if not pages:
        return {"error": f"No Wikipedia article found for '{topic}'."}
    page = next(iter(pages.values()))
    # Keep it short: every character we send the LLM costs tokens and time.
    return {"title": page["title"], "summary": page.get("extract", "")[:1200]}


# ---------------------------------------------------------------------------
# Tool 3 (optional): web search  (Tavily - https://tavily.com)
# Only offered to the LLM if TAVILY_API_KEY is in your .env file.
# ---------------------------------------------------------------------------

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


def web_search(query: str) -> dict:
    """Search the live web. Good for events, prices and recent news."""
    data = requests.post(
        "https://api.tavily.com/search",
        json={"query": query, "max_results": 3},
        headers={**HEADERS, "Authorization": f"Bearer {TAVILY_API_KEY}"},
        timeout=TIMEOUT,
    ).json()
    if "results" not in data:  # e.g. {"detail": {"error": "Unauthorized..."}}
        detail = data.get("detail", data)
        if isinstance(detail, dict):
            detail = detail.get("error", detail)
        return {"error": f"Web search problem: {detail}"}
    return {"results": [
        {"title": r["title"], "url": r["url"], "snippet": r["content"][:400]}
        for r in data["results"]
    ]}


WEB_SEARCH_DECLARATION = {
    "name": "web_search",
    "description": "Search the live web for current events, opening hours, "
                   "prices or anything not in an encyclopedia.",
    "parameters_json_schema": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
}


# ---------------------------------------------------------------------------
# Tool "menu": what we show the LLM.  name + description + parameters
# The LLM reads ONLY this - it never sees the Python code above.
# ---------------------------------------------------------------------------

TOOL_DECLARATIONS = [
    {
        "name": "get_weather",
        "description": "Daily weather forecast for a city for the next few days.",
        "parameters_json_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "e.g. 'Mombasa'"},
                "days": {"type": "integer", "description": "1 to 7"},
            },
            "required": ["city"],
        },
    },
    {
        "name": "get_place_info",
        "description": "Get an encyclopedia summary about a place, park or landmark.",
        "parameters_json_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "e.g. 'Fort Jesus'"},
            },
            "required": ["topic"],
        },
    },
]

# Lookup table: tool name (text from the LLM) -> real Python function
TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "get_place_info": get_place_info,
}

# The optional third tool: only switched on when there's a key.
if TAVILY_API_KEY:
    TOOL_DECLARATIONS.append(WEB_SEARCH_DECLARATION)
    TOOL_FUNCTIONS["web_search"] = web_search


if __name__ == "__main__":
    # Run `python tools.py` to test the tools WITHOUT any LLM.
    print(get_weather("Mombasa", 2))
    print(get_place_info("Fort Jesus"))
    if TAVILY_API_KEY:
        print(web_search("events in Mombasa this weekend"))
    else:
        print("web_search skipped: no TAVILY_API_KEY in .env")
