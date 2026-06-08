"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
from dotenv import load_dotenv
from groq import Groq
from utils.data_loader import load_listings
import urllib.request
import urllib.parse
import json

load_dotenv()

# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)

# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.
    """
    listings = load_listings()
    keywords = [kw.lower() for kw in description.split()]
    scored_matches = []

    for item in listings:
        # Price filter
        if max_price is not None and item["price"] > max_price:
            continue
            
        # Size filter (case-insensitive substring match to handle "M" matching "S/M")
        if size is not None and size.lower() not in item["size"].lower():
            continue

        # Score by keyword overlap
        search_text = f"{item['title']} {item['description']} {' '.join(item['style_tags'])}".lower()
        score = sum(1 for kw in keywords if kw in search_text)

        if score > 0:
            scored_matches.append((score, item))

    # Sort by score (highest first), then by price (lowest first)
    scored_matches.sort(key=lambda x: (-x[0], x[1]["price"]))
    
    return [match[1] for match in scored_matches]

# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.
    """
    client = _get_groq_client()
    items = wardrobe.get("items", [])
    
    # Handle the empty wardrobe failure mode
    if not items:
        prompt = f"""
        The user just bought a '{new_item['title']}'. Their digital wardrobe is currently empty. 
        Give them a 2-3 sentence styling suggestion using universal basics (like baggy jeans, white tees, etc.).
        Kindly remind them to add items to their digital closet so you can give better recommendations next time.
        """
    else:
        wardrobe_names = [f"- {i['name']} ({', '.join(i['colors'])})" for i in items]
        wardrobe_list = "\n".join(wardrobe_names)
        
        prompt = f"""
        The user just bought: '{new_item['title']}'
        Style tags: {', '.join(new_item['style_tags'])}
        Colors: {', '.join(new_item['colors'])}
        
        Their current wardrobe includes:
        {wardrobe_list}
        
        Suggest 1-2 complete outfits pairing the new item with 1-2 specific items from their wardrobe.
        Explain why the colors or proportions work well together. Keep it to 3 sentences maximum.
        """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful, trendy personal fashion stylist."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=150
    )
    
    return response.choices[0].message.content.strip()

# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.
    """
    # Guard against missing/empty outfit string
    if not outfit or not outfit.strip():
        return f"just grabbed this {new_item['title']} off {new_item['platform']} for ${new_item['price']:.2f} ✨"

    client = _get_groq_client()
    
    prompt = f"""
    Create a punchy, casual Instagram/TikTok caption for this outfit.
    
    Item bought: {new_item['title']}
    Price: ${new_item['price']:.2f}
    Platform: {new_item['platform']}
    Outfit Idea: {outfit}
    
    Rules:
    - Lowercase aesthetic, use 1-2 emojis.
    - Mention the price and platform naturally.
    - Do not sound like a marketer, sound like a real person showing off an OOTD.
    - Keep it to 2-4 sentences.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You write engaging, authentic Gen-Z/Millennial social media captions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9, # Higher temp for varied, creative captions
        max_tokens=100
    )
    
    return response.choices[0].message.content.strip()

# ── Tool 4: evaluate_harmony (Stretch Goal) ───────────────────────────────────

def evaluate_harmony(new_item: dict, wardrobe_item: dict) -> str:
    """
    Evaluates color and style harmony between a thrifted item and a specific wardrobe piece.
    """
    client = _get_groq_client()
    
    prompt = f"""
    You are a strict fashion critic. 
    Item 1: {new_item['title']} (Colors: {', '.join(new_item.get('colors', []))}, Style: {', '.join(new_item.get('style_tags', []))})
    Item 2: {wardrobe_item['name']} (Colors: {', '.join(wardrobe_item.get('colors', []))}, Style: {', '.join(wardrobe_item.get('style_tags', []))})
    
    Do these two items clash, or do they work well together? 
    Answer in exactly 1-2 sentences with a clear "Yes" or "No" and a brief fashion rationale.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You evaluate color theory and fashion aesthetics."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3, # Low temp for analytical consistency
        max_tokens=60
    )
    
    return response.choices[0].message.content.strip()

# ── Tool 5: get_weather_context (Stretch Goal) ────────────────────────────────

def get_weather_context(location: str) -> str:
    """
    Fetches live weather data for a given city to inform outfit practicality.
    Fails gracefully by prompting the user if the API is down or location is invalid.
    """
    if not location or not location.strip():
        return "No location provided. Please manually specify if you need an outfit for hot, cold, or rainy weather."
        
    try:
        # URL encode the location to handle spaces (e.g., "New York")
        safe_location = urllib.parse.quote(location.strip())
        url = f"https://wttr.in/{safe_location}?format=j1"
        
        # 3-second timeout prevents the agent from hanging if wttr.in is slow
        req = urllib.request.Request(url, headers={'User-Agent': 'FitFindrAgent/1.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            current = data['current_condition'][0]
            temp = current['temp_F']
            desc = current['weatherDesc'][0]['value']
            
            return f"Current weather in {location}: {temp}°F and {desc.lower()}."
            
    except Exception:
        # Catch network timeouts, 404s, or JSON parsing errors
        return "Weather service currently unavailable. Please manually specify if you need an outfit for hot or cold weather."