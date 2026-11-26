import pytest

from app.core.normalizers import normalize_text


def test_identical_string_passes_through() -> None:
    assert normalize_text("Acme Ltd.", case_sensitive=True) == "Acme Ltd."


def test_leading_and_trailing_whitespace_is_trimmed() -> None:
    assert normalize_text("  Acme Ltd. \t", case_sensitive=True) == "Acme Ltd."


def test_internal_multiple_spaces_collapse_to_one() -> None:
    assert normalize_text("Acme   Ltd.", case_sensitive=True) == "Acme Ltd."


def test_tabs_newlines_and_nbsp_collapse() -> None:
    raw = "a \t b\n c\u00a0d"

    assert normalize_text(raw, case_sensitive=True) == "a b c d"


def test_whitespace_only_becomes_empty_string() -> None:
    assert normalize_text(" \t\n\u00a0 ", case_sensitive=True) == ""


def test_nfc_composed_and_decomposed_are_equal() -> None:
    composed = "Caf\u00e9"
    decomposed = "Cafe\u0301"

    assert normalize_text(composed, case_sensitive=True) == normalize_text(
        decomposed, case_sensitive=True
    )


def test_case_is_preserved_when_case_sensitive() -> None:
    assert normalize_text("Acme Ltd", case_sensitive=True) == "Acme Ltd"


def test_case_is_folded_when_not_case_sensitive() -> None:
    assert normalize_text("Acme Ltd", case_sensitive=False) == "acme ltd"


def test_casefold_maps_sharp_s_to_double_s() -> None:
    assert normalize_text("Stra\u00dfe", case_sensitive=False) == normalize_text(
        "STRASSE", case_sensitive=False
    )
    assert normalize_text("Stra\u00dfe", case_sensitive=True) != normalize_text(
        "STRASSE", case_sensitive=True
    )


def test_punctuation_is_preserved() -> None:
    assert normalize_text("Acme Ltd.", case_sensitive=True) == "Acme Ltd."


def test_nfkc_is_not_applied() -> None:
    # Full-width "A" would become ASCII "A" under NFKC; NFC keeps it.
    assert normalize_text("\uff21", case_sensitive=True) == "\uff21"


def test_zero_width_space_is_not_removed() -> None:
    # Known limit (documented): zero-width characters are not whitespace.
    assert normalize_text("a\u200bb", case_sensitive=True) == "a\u200bb"


def test_different_dash_characters_stay_distinct() -> None:
    assert normalize_text("a\u2013b", case_sensitive=True) != normalize_text(
        "a-b", case_sensitive=True
    )


def test_normalize_text_is_idempotent() -> None:
    raw = "  Caf\u00e9\u0301 \t Stra\u00dfe\n NBSP\u00a0end  "

    once = normalize_text(raw, case_sensitive=False)
    twice = normalize_text(once, case_sensitive=False)

    assert twice == once


def test_normalize_text_rejects_non_str() -> None:
    with pytest.raises(TypeError, match="expects str"):
        normalize_text(42, case_sensitive=True)  # type: ignore[arg-type]
