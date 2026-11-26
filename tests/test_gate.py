"""Tests for the deterministic gate. No model, no network, no SDK: these run anywhere."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gate import has_checkable_fact  # noqa: E402


def test_plain_prose_has_no_fact():
    assert not has_checkable_fact("Gno is an interpreted version of Go, with realms and packages.")


def test_a_single_digit_is_enough():
    assert has_checkable_fact("Turnout reached 36.8 percent by 26 November 2026.")


def test_empty_page_has_no_fact():
    assert not has_checkable_fact("")


if __name__ == "__main__":
    test_plain_prose_has_no_fact()
    test_a_single_digit_is_enough()
    test_empty_page_has_no_fact()
    print("3 gate tests passed")
