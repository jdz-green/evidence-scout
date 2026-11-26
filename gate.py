"""The deterministic gate, kept free of the SDK so it can be tested without installing OpenMinion."""
import re


def has_checkable_fact(text: str) -> bool:
    """True when the text carries a digit, i.e. something a note could quote as a number or date."""
    return bool(re.search(r"\d", text))
