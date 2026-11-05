"""
exercise_solutions.py - answers for the "Your turn" exercises.
Try them yourself first!

How to plug a new tool into the agent (same 3 moves every time):
  1. Write the Python function           (in tools.py)
  2. Add its description to TOOL_DECLARATIONS
  3. Add  "name": function  to TOOL_FUNCTIONS
Nothing in agent.py needs to change. The loop already handles any tool.
"""

import json
from datetime import datetime

import requests

HEADERS = {"User-Agent": "SafariAgentWorkshop/1.0 (student learning project)"}


# ---------------------------------------------------------------------------
# Exercise 2: country facts  (REST Countries - free, no key)
# ---------------------------------------------------------------------------

def get_country_info(country: str) -> dict:
    """Capital, population, currencies, languages and time zones of a country."""
    data = requests.get(
        f"https://restcountries.com/v3.1/name/{country}",
        params={"fields": "name,capital,population,currencies,languages,timezones"},
        headers=HEADERS, timeout=10,
    ).json()
    if not isinstance(data, list) or not data:
        return {"error": f"No country found called '{country}'."}
    c = data[0]
    return {
        "name": c["name"]["common"],
        "capital": c.get("capital", []),
        "population": c.get("population"),
        "currencies": list(c.get("currencies", {}).keys()),
        "languages": list(c.get("languages", {}).values()),
        "timezones": c.get("timezones", []),
    }


COUNTRY_DECLARATION = {
    "name": "get_country_info",
    "description": "Get basic facts about a country: capital, population, currencies, languages, time zones.",
    "parameters_json_schema": {
        "type": "object",
        "properties": {"country": {"type": "string", "description": "e.g. 'Tanzania'"}},
        "required": ["country"],
    },
}


# ---------------------------------------------------------------------------
# Exercise 3: a tool that DOES something - save the plan to a file
# A human approves first ("human in the loop"), because this tool changes things.
# ---------------------------------------------------------------------------

def save_trip_plan(title: str, plan: str) -> dict:
    """Save a trip plan to a text file, after the user says yes."""
    answer = input(f"\n  Agent wants to save '{title}' to a file. Allow? (y/n) ").strip().lower()
    if answer != "y":
        return {"saved": False, "reason": "The user said no."}
    filename = f"trip_{datetime.now():%Y%m%d_%H%M%S}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"{title}\n{'=' * len(title)}\n\n{plan}\n")
    return {"saved": True, "file": filename}


SAVE_DECLARATION = {
    "name": "save_trip_plan",
    "description": "Save the final trip plan to a text file. Only use when the user asks to save.",
    "parameters_json_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "plan": {"type": "string", "description": "The full plan text"},
        },
        "required": ["title", "plan"],
    },
}


# To use them, add these lines at the bottom of tools.py:
#
#   from exercise_solutions import (get_country_info, COUNTRY_DECLARATION,
#                                   save_trip_plan, SAVE_DECLARATION)
#   TOOL_DECLARATIONS += [COUNTRY_DECLARATION, SAVE_DECLARATION]
#   TOOL_FUNCTIONS["get_country_info"] = get_country_info
#   TOOL_FUNCTIONS["save_trip_plan"] = save_trip_plan

if __name__ == "__main__":
    print(json.dumps(get_country_info("Kenya"), indent=2))
