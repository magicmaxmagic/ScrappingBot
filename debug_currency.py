from typing import Optional

def test_normalize_currency(currency: Optional[str]) -> str:
    """Test version of normalize_currency."""
    if not currency:
        return "EUR"
    
    currency = str(currency).upper().strip()
    print(f"Processing currency: {repr(currency)}")
    
    # Common currency mappings
    currency_map = {
        "€": "EUR",
        "EUR": "EUR",
        "EURO": "EUR",
        "EUROS": "EUR",
        "$": "USD",
        "USD": "USD",
        "DOLLAR": "USD",
        "DOLLARS": "USD",
        "£": "GBP",
        "GBP": "GBP",
        "POUND": "GBP",
        "POUNDS": "GBP",
        "CHF": "CHF",
        "FRANC": "CHF",
        "FRANCS": "CHF",
    }
    
    print(f"Currency in map: {currency in currency_map}")
    if currency in currency_map:
        result = currency_map[currency]
        print(f"Direct mapping result: {result}")
        return result
    
    # Extract currency code from text
    for key, value in currency_map.items():
        if key in currency:
            print(f"Text search result: {value}")
            return value
    
    # Default fallback
    print("Using default fallback")
    return "EUR"

# Test it
if __name__ == "__main__":
    print("=== Testing USD ===")
    result = test_normalize_currency("USD")
    print(f"Final result: {result}")
    print()
    
    print("=== Testing EUR ===")
    result = test_normalize_currency("EUR")
    print(f"Final result: {result}")
