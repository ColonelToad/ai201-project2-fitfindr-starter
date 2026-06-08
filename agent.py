"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import re
from tools import search_listings, suggest_outfit, create_fit_card

# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """Initialize and return a fresh session dict for one user interaction."""
    return {
        "query": query,              
        "parsed": {},                
        "search_results": [],        
        "selected_item": None,       
        "wardrobe": wardrobe,        
        "outfit_suggestion": None,   
        "fit_card": None,            
        "error": None,               
    }

def _parse_query(query: str) -> dict:
    """
    Simple regex-based parser to extract size and price constraints.
    Keeps the agent fast and reduces unnecessary LLM calls.
    """
    parsed = {
        "description": query,
        "size": None,
        "max_price": None
    }
    
    # Extract price (e.g., "under $30", "under 30")
    price_match = re.search(r'under\s*\$?\s*(\d+(?:\.\d{2})?)', query.lower())
    if price_match:
        parsed["max_price"] = float(price_match.group(1))
        
    # Extract size (e.g., "size M", "size W30")
    size_match = re.search(r'size\s+([a-zA-Z0-9/]+)', query.lower())
    if size_match:
        parsed["size"] = size_match.group(1).upper()
        
    return parsed

# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.
    """
    # Step 1: Initialize
    session = _new_session(query, wardrobe)
    
    # Step 2: Parse parameters
    session["parsed"] = _parse_query(query)
    desc = session["parsed"]["description"]
    size = session["parsed"]["size"]
    price = session["parsed"]["max_price"]
    
    # Step 3: Search with constraints
    results = search_listings(description=desc, size=size, max_price=price)
    
    # SMART FALLBACK LOGIC
    # If no results and the user specified a size, try again without the size limit.
    if len(results) == 0 and size is not None:
        results = search_listings(description=desc, size=None, max_price=price)
        
    session["search_results"] = results
    
    # HARD FAIL LOGIC
    if len(results) == 0:
        session["error"] = "I couldn't find exactly what you're looking for in your size or price range. Try dropping some specific keywords!"
        return session
        
    # Step 4: Select the item
    session["selected_item"] = results[0]
    
    # Step 5: Generate Outfit
    session["outfit_suggestion"] = suggest_outfit(
        new_item=session["selected_item"], 
        wardrobe=session["wardrobe"]
    )
    
    # Step 6: Generate Fit Card
    session["fit_card"] = create_fit_card(
        outfit=session["outfit_suggestion"], 
        new_item=session["selected_item"]
    )
    
    # Step 7: Return final state
    return session

# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")