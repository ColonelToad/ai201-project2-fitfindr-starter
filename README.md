# FitFindr 🛍️

FitFindr is an AI-driven, multi-tool styling agent that helps users find secondhand pieces and figure out how to wear them based on their existing digital wardrobe. 

This project utilizes the Groq API (`llama-3.3-70b-versatile`) to orchestrate a pipeline that searches mock inventory, evaluates color harmony, factors in real-world weather, and generates shareable social media captions.

## Features

- **Core Tools:** - `search_listings`: Filters a mock database by keywords, size, and maximum price.
  - `suggest_outfit`: Uses an LLM to pair a new item with the user's existing wardrobe.
  - `create_fit_card`: Generates a casual, Gen-Z/Millennial styled OOTD caption.
- **Stretch Feature (Smart Fallback):** Automatically relaxes search constraints (drops size requirement) if an initial highly-specific search yields zero results.
- **Stretch Feature (Color Harmony):** A dedicated `evaluate_harmony` tool that checks color theory and style tags between items before styling.
- **Stretch Feature (Weather Context):** A `get_weather_context` tool that pulls live data from `wttr.in` to ensure outfit suggestions make sense for the current temperature.
- **Interactive UI:** A complete Gradio web interface to test queries and view the agent's workflow.

## How the Agent Works (Planning & State)

FitFindr uses a centralized `session_state` dictionary to pass data between tools without requiring the user to repeat themselves. 

**The Planning Loop:**
1. **Extraction:** A lightweight regex parser extracts price and size constraints from the natural language query.
2. **Search & Fallback:** The agent calls `search_listings`. If no items are found and a size constraint was provided, the agent executes a **Smart Fallback**—retrying the search without the size constraint. 
3. **Branching/Hard Fail:** If the fallback also returns empty, the loop sets an error state and aborts early to prevent downstream LLM tools from hallucinating on empty data.
4. **Context Gathering:** The agent executes `get_weather_context` and `evaluate_harmony` to build a rich styling prompt.
5. **Styling & Output:** State flows into `suggest_outfit` and finally `create_fit_card`.

## Error Handling Strategy

"Fail silently" or "crash" are not acceptable. Every tool handles its own failures gracefully:
- **`search_listings`:** Triggers the Smart Fallback. If still empty, returns a polite message asking the user to loosen their keywords.
- **`suggest_outfit`:** If the user's `wardrobe_schema.json` is completely empty, it recognizes the empty list and prompts the LLM to provide a generic styling suggestion based on universal fashion basics (e.g., white tees, baggy jeans).
- **`create_fit_card`:** If the outfit string is somehow corrupted, it falls back to a hardcoded string template hyping up the purchased item.
- **`get_weather_context`:** Implements a strict 3-second timeout. If the live API fails, it returns a safe string prompting the user to manually specify the weather.

## Setup & Usage

1. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt