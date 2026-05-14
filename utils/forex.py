from forex_python.converter import CurrencyRates

_converter = CurrencyRates()

CURRENCY_SYMBOLS = {
    "USD": "$",  "EUR": "€",  "INR": "₹",  "GBP": "£",
    "JPY": "¥",  "CNY": "¥",  "AED": "د.إ","AUD": "A$",
    "CAD": "C$", "CHF": "CHF ","SGD": "S$",
}

CURRENCY_OPTIONS = [
    "Currency", "USD", "EUR", "INR", "GBP",
    "JPY", "AUD", "CAD", "CHF", "CNY", "SGD", "AED",
]


def get_currency_symbol(currency: str) -> str:
    return CURRENCY_SYMBOLS.get(currency, currency + " ")


def convert_price(amount: float, from_currency: str, to_currency: str) -> tuple[float, float]:
    """
    Convert amount from from_currency to to_currency.
    Returns (converted_amount, fx_rate).
    Falls back to original on error.
    """
    if to_currency == "CurrencySelector" or from_currency == to_currency:
        return amount, 1.0
    try:
        rate = _converter.get_rate(from_currency, to_currency)
        return amount * rate, rate
    except Exception:
        return amount, 1.0
