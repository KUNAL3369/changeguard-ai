"""Pure text normalization for the normalized_string evaluator (decision O8).

Pure Python: no I/O, no clock, no float, no environment access.
Steps (in order): NFC -> whitespace trim/collapse -> optional casefold.
NFKC is deliberately NOT used: compatibility folding can change meaning
(e.g. full-width or ligature characters) and the dataset must control
what is equivalent.
"""

import unicodedata


def normalize_text(value: str, *, case_sensitive: bool) -> str:
    """Return the normalized form of ``value``.

    1. ``unicodedata.normalize("NFC", value)`` -- composed vs decomposed
       Unicode becomes one canonical sequence.
    2. ``" ".join(value.split())`` -- trims and collapses every Unicode
       whitespace run (spaces, tabs, newlines, NBSP) to a single space.
    3. If ``case_sensitive`` is false, apply ``casefold()`` last so that
       case folding runs on the already-canonical string (e.g. "Stra\\u00dfe"
       and "STRASSE" both become "strasse").

    Punctuation, dashes and zero-width characters are NOT touched: they are
    significant differences between expected and actual output. The function
    is idempotent: applying it twice equals applying it once.
    """
    if not isinstance(value, str):
        raise TypeError(f"normalize_text expects str, got {type(value).__name__}")
    normalized = unicodedata.normalize("NFC", value)
    normalized = " ".join(normalized.split())
    if not case_sensitive:
        normalized = normalized.casefold()
    return normalized
