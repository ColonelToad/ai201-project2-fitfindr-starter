# tests/test_tools.py

import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools import search_listings, suggest_outfit, create_fit_card, evaluate_harmony, get_weather_context
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe

# ── search_listings Tests ─────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    # Impossible query to trigger the empty return
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=45.0)
    assert all(item["price"] <= 45.0 for item in results)

def test_search_size_filter():
    results = search_listings("jeans", size="W30", max_price=100)
    # The size matching is substring based, so "W30 L30" should match "W30"
    assert all("w30" in item["size"].lower() for item in results)

# ── suggest_outfit Tests ──────────────────────────────────────────────────────

def test_suggest_outfit_empty_wardrobe():
    mock_item = {
        "title": "Vintage Leather Jacket",
        "style_tags": ["vintage", "leather"],
        "colors": ["black"]
    }
    empty_wardrobe = get_empty_wardrobe()
    
    result = suggest_outfit(mock_item, empty_wardrobe)
    assert isinstance(result, str)
    assert len(result) > 0
    # The LLM should mention adding items to the closet based on the prompt
    assert "closet" in result.lower() or "wardrobe" in result.lower()

# ── create_fit_card Tests ─────────────────────────────────────────────────────

def test_create_fit_card_empty_outfit():
    mock_item = {
        "title": "Y2K Baby Tee",
        "price": 18.00,
        "platform": "depop"
    }
    
    result = create_fit_card("", mock_item)
    # Should hit the fallback, not the LLM
    assert result == "just grabbed this Y2K Baby Tee off depop for $18.00 ✨"

def test_create_fit_card_normal():
    mock_item = {
        "title": "Y2K Baby Tee",
        "price": 18.00,
        "platform": "depop"
    }
    outfit = "Pair this tee with some low-rise cargo pants and chunky platform sneakers."
    
    result = create_fit_card(outfit, mock_item)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "18" in result
    assert "depop" in result.lower()

# ── evaluate_harmony Tests ────────────────────────────────────────────────────

def test_evaluate_harmony():
    mock_new_item = {
        "title": "Neon Green Corduroy Pants",
        "colors": ["neon green"],
        "style_tags": ["loud", "y2k"]
    }
    mock_wardrobe_item = {
        "name": "Classic Navy Blazer",
        "colors": ["navy blue"],
        "style_tags": ["preppy", "classic"]
    }
    
    result = evaluate_harmony(mock_new_item, mock_wardrobe_item)
    assert isinstance(result, str)
    assert len(result) > 0
    # The LLM should give an analytical response, ideally warning about this combo!

# ── get_weather_context Tests ─────────────────────────────────────────────────

def test_get_weather_context_valid():
    # Testing a major city should reliably hit the API
    result = get_weather_context("London")
    assert isinstance(result, str)
    # The success string contains "Current weather in"
    assert "Current weather in London" in result
    assert "°F" in result

def test_get_weather_context_empty():
    result = get_weather_context("")
    # Should trigger the empty location fallback
    assert "No location provided" in result

def test_get_weather_context_invalid():
    # Testing gibberish to force a 404/Exception from wttr.in
    result = get_weather_context("NotARealCity12345")
    # Should trigger the exception fallback
    assert "Weather service currently unavailable" in result