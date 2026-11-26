import pytest

from app.core.evaluators import evaluate_field
from app.core.types import (
    EvaluatorType,
    FailureReason,
    FieldSpec,
    Severity,
    ValueState,
)


def _spec(
    evaluator_type: EvaluatorType = EvaluatorType.EXACT,
    *,
    severity: Severity = Severity.MEDIUM,
    required: bool = True,
    field_path: str = "invoice_number",
    case_sensitive: bool = True,
) -> FieldSpec:
    return FieldSpec(
        field_path=field_path,
        evaluator_type=evaluator_type,
        severity=severity,
        required=required,
        case_sensitive=case_sensitive,
    )


# --- state invariants and dispatcher honesty -------------------------------


def test_evaluate_field_present_state_with_none_raises_value_error() -> None:
    with pytest.raises(ValueError, match="PRESENT requires a non-None actual"):
        evaluate_field("INV-1042", None, _spec(), actual_state=ValueState.PRESENT)


def test_evaluate_field_absent_state_with_value_raises_value_error() -> None:
    with pytest.raises(ValueError, match="requires actual=None"):
        evaluate_field("INV-1042", "INV-1042", _spec(), actual_state=ValueState.ABSENT)


def test_evaluate_field_null_state_with_value_raises_value_error() -> None:
    with pytest.raises(ValueError, match="requires actual=None"):
        evaluate_field("INV-1042", "INV-1042", _spec(), actual_state=ValueState.NULL)


def test_unimplemented_evaluator_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError, match="numeric"):
        evaluate_field(
            "10000.00",
            "10000.00",
            _spec(EvaluatorType.NUMERIC),
            actual_state=ValueState.PRESENT,
        )


# --- exact: pass ------------------------------------------------------------


def test_exact_equal_strings_pass() -> None:
    result = evaluate_field(
        "INV-1042",
        "INV-1042",
        _spec(),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.score is None
    assert result.actual_state is ValueState.PRESENT
    assert result.evaluator_type is EvaluatorType.EXACT


def test_exact_equal_ints_pass() -> None:
    result = evaluate_field(
        7,
        7,
        _spec(field_path="line_count"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.actual == 7


def test_exact_equal_bools_pass() -> None:
    result = evaluate_field(
        True,
        True,
        _spec(field_path="is_final"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.actual is True


# --- exact: fail ------------------------------------------------------------


def test_exact_unequal_strings_fail_value_mismatch() -> None:
    result = evaluate_field(
        "INV-1042",
        "INV-1043",
        _spec(),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.VALUE_MISMATCH


def test_exact_absent_actual_fails_missing() -> None:
    result = evaluate_field(
        "INV-1042",
        None,
        _spec(),
        actual_state=ValueState.ABSENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.MISSING
    assert result.actual_state is ValueState.ABSENT


def test_exact_explicit_null_actual_fails_missing() -> None:
    result = evaluate_field(
        "INV-1042",
        None,
        _spec(),
        actual_state=ValueState.NULL,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.MISSING
    assert result.actual_state is ValueState.NULL


def test_exact_expected_null_and_absent_passes() -> None:
    result = evaluate_field(
        None,
        None,
        _spec(required=False),
        actual_state=ValueState.ABSENT,
    )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.actual_state is ValueState.ABSENT


def test_exact_expected_null_and_explicit_null_passes() -> None:
    result = evaluate_field(
        None,
        None,
        _spec(required=False),
        actual_state=ValueState.NULL,
    )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.actual_state is ValueState.NULL


def test_exact_expected_null_and_present_value_fails_unexpected_value() -> None:
    result = evaluate_field(
        None,
        "PO-77",
        _spec(field_path="po_number"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.UNEXPECTED_VALUE


def test_exact_string_expected_int_actual_fails_type_mismatch() -> None:
    result = evaluate_field(
        "10000.00",
        10000,
        _spec(field_path="total_amount"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.TYPE_MISMATCH


def test_exact_zero_expected_false_actual_fails_type_mismatch() -> None:
    result = evaluate_field(
        0,
        False,
        _spec(field_path="quantity"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.TYPE_MISMATCH


def test_exact_required_empty_string_fails_empty() -> None:
    result = evaluate_field(
        "INV-1042",
        "",
        _spec(),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.EMPTY


def test_exact_required_whitespace_only_fails_empty() -> None:
    result = evaluate_field(
        "INV-1042",
        "   ",
        _spec(),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.EMPTY


def test_exact_optional_empty_matches_empty_passes() -> None:
    result = evaluate_field(
        "",
        "",
        _spec(required=False),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.failure_reason is None


def test_exact_unicode_strings_pass() -> None:
    value = "Café ☕ 銀行"

    result = evaluate_field(
        value,
        value,
        _spec(field_path="vendor_name"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.failure_reason is None


def test_exact_does_not_normalize_unicode() -> None:
    composed = "Café"
    decomposed = "Café"

    result = evaluate_field(
        composed,
        decomposed,
        _spec(field_path="vendor_name"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.VALUE_MISMATCH


def test_exact_carries_spec_severity_and_evaluator_type() -> None:
    spec = _spec(severity=Severity.HIGH)

    passing = evaluate_field(
        "INV-1042",
        "INV-1042",
        spec,
        actual_state=ValueState.PRESENT,
    )
    failing = evaluate_field(
        "INV-1042",
        "INV-1043",
        spec,
        actual_state=ValueState.PRESENT,
    )

    for result in (passing, failing):
        assert result.severity is Severity.HIGH
        assert result.evaluator_type is EvaluatorType.EXACT
        assert result.field_path == "invoice_number"


# --- required: presence only ------------------------------------------------


def test_required_present_string_passes() -> None:
    result = evaluate_field(
        "INV-1042",
        "INV-1042",
        _spec(EvaluatorType.REQUIRED),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.evaluator_type is EvaluatorType.REQUIRED


def test_required_absent_fails_missing() -> None:
    result = evaluate_field(
        "INV-1042",
        None,
        _spec(EvaluatorType.REQUIRED),
        actual_state=ValueState.ABSENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.MISSING


def test_required_explicit_null_fails_missing() -> None:
    result = evaluate_field(
        "INV-1042",
        None,
        _spec(EvaluatorType.REQUIRED),
        actual_state=ValueState.NULL,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.MISSING


def test_required_empty_string_fails_empty() -> None:
    result = evaluate_field(
        "INV-1042",
        "",
        _spec(EvaluatorType.REQUIRED),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.EMPTY


def test_required_whitespace_only_fails_empty() -> None:
    result = evaluate_field(
        "INV-1042",
        "\t\n ",
        _spec(EvaluatorType.REQUIRED),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.EMPTY


def test_required_zero_passes() -> None:
    result = evaluate_field(
        0,
        0,
        _spec(EvaluatorType.REQUIRED, field_path="quantity"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.actual == 0


def test_required_false_passes() -> None:
    result = evaluate_field(
        False,
        False,
        _spec(EvaluatorType.REQUIRED, field_path="is_final"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.actual is False


def test_required_unicode_non_empty_passes() -> None:
    result = evaluate_field(
        "Grüße",
        "Grüße",
        _spec(EvaluatorType.REQUIRED, field_path="vendor_name"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True


def test_required_ignores_expected_value_when_present() -> None:
    result = evaluate_field(
        "INV-1042",
        "INV-9999",
        _spec(EvaluatorType.REQUIRED),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.actual == "INV-9999"


def test_required_expected_null_absent_when_optional_passes() -> None:
    result = evaluate_field(
        None,
        None,
        _spec(EvaluatorType.REQUIRED, required=False),
        actual_state=ValueState.ABSENT,
    )

    assert result.passed is True
    assert result.failure_reason is None


def test_required_expected_null_absent_when_required_fails_missing() -> None:
    result = evaluate_field(
        None,
        None,
        _spec(EvaluatorType.REQUIRED),
        actual_state=ValueState.ABSENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.MISSING


def test_required_expected_null_and_present_value_passes() -> None:
    result = evaluate_field(
        None,
        "PO-77",
        _spec(EvaluatorType.REQUIRED, field_path="po_number"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.actual == "PO-77"


def test_required_carries_spec_severity_and_evaluator_type() -> None:
    spec = _spec(EvaluatorType.REQUIRED, severity=Severity.CRITICAL, field_path="po_number")

    passing = evaluate_field(None, "PO-77", spec, actual_state=ValueState.PRESENT)
    failing = evaluate_field(None, None, spec, actual_state=ValueState.ABSENT)

    for result in (passing, failing):
        assert result.severity is Severity.CRITICAL
        assert result.evaluator_type is EvaluatorType.REQUIRED
        assert result.field_path == "po_number"


# --- vocabulary and defaults ------------------------------------------------


def test_failure_reason_value_mismatch_is_enum_value() -> None:
    assert FailureReason.VALUE_MISMATCH.value == "value_mismatch"


def test_failure_reason_unexpected_value_is_enum_value() -> None:
    assert FailureReason.UNEXPECTED_VALUE.value == "unexpected_value"


def test_value_state_is_enum_values() -> None:
    assert [state.value for state in ValueState] == ["present", "absent", "null"]


def test_failed_result_from_evaluator_always_has_reason() -> None:
    failures = [
        evaluate_field("INV-1042", None, _spec(), actual_state=ValueState.ABSENT),
        evaluate_field("INV-1042", None, _spec(), actual_state=ValueState.NULL),
        evaluate_field(
            "INV-1042",
            "INV-1043",
            _spec(),
            actual_state=ValueState.PRESENT,
        ),
        evaluate_field(None, "PO-77", _spec(), actual_state=ValueState.PRESENT),
        evaluate_field("INV-1042", "", _spec(), actual_state=ValueState.PRESENT),
        evaluate_field(
            "10000.00",
            10000,
            _spec(field_path="total_amount"),
            actual_state=ValueState.PRESENT,
        ),
    ]

    assert failures
    for result in failures:
        assert result.passed is False
        assert result.failure_reason is not None


# --- normalized_string (T09) ------------------------------------------------


def _nspec(
    *,
    severity: Severity = Severity.MEDIUM,
    required: bool = True,
    case_sensitive: bool = True,
    field_path: str = "vendor_name",
) -> FieldSpec:
    return _spec(
        EvaluatorType.NORMALIZED_STRING,
        severity=severity,
        required=required,
        case_sensitive=case_sensitive,
        field_path=field_path,
    )


def test_normalized_identical_strings_pass() -> None:
    result = evaluate_field(
        "Acme Ltd.",
        "Acme Ltd.",
        _nspec(),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.failure_reason is None


def test_normalized_case_difference_fails_by_default() -> None:
    result = evaluate_field(
        "Acme Ltd.",
        "ACME LTD.",
        _nspec(),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.VALUE_MISMATCH


def test_normalized_case_difference_passes_when_not_case_sensitive() -> None:
    result = evaluate_field(
        "Acme Ltd.",
        "ACME LTD.",
        _nspec(case_sensitive=False),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.failure_reason is None


def test_normalized_casefold_handles_sharp_s() -> None:
    result = evaluate_field(
        "Stra\u00dfe",
        "STRASSE",
        _nspec(case_sensitive=False),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.failure_reason is None


def test_normalized_leading_and_trailing_whitespace_passes() -> None:
    result = evaluate_field(
        "  Acme Ltd.  ",
        "Acme Ltd.",
        _nspec(),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.normalized_expected == "Acme Ltd."
    assert result.normalized_actual == "Acme Ltd."


def test_normalized_internal_multiple_spaces_pass() -> None:
    result = evaluate_field(
        "Acme   Ltd.",
        "Acme Ltd.",
        _nspec(),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True


def test_normalized_tabs_newlines_and_nbsp_collapse() -> None:
    result = evaluate_field(
        "a \t b\n c\u00a0d",
        "a b c d",
        _nspec(field_path="notes"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.normalized_actual == "a b c d"


def test_normalized_nfc_composed_and_decomposed_pass() -> None:
    result = evaluate_field(
        "Caf\u00e9",
        "Cafe\u0301",
        _nspec(),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.normalized_expected == result.normalized_actual


def test_normalized_punctuation_is_significant() -> None:
    result = evaluate_field(
        "Acme Ltd.",
        "Acme Ltd",
        _nspec(),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.VALUE_MISMATCH
    assert result.normalized_expected == "Acme Ltd."
    assert result.normalized_actual == "Acme Ltd"


def test_normalized_different_dash_characters_fail() -> None:
    result = evaluate_field(
        "a\u2013b",
        "a-b",
        _nspec(field_path="notes"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.VALUE_MISMATCH


def test_normalized_zero_width_space_is_not_removed() -> None:
    # Known limit, documented in EVALUATION_ENGINE.md.
    result = evaluate_field(
        "ab",
        "a\u200bb",
        _nspec(field_path="notes"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.VALUE_MISMATCH


def test_normalized_int_actual_fails_type_mismatch() -> None:
    result = evaluate_field(
        "10000",
        10000,
        _nspec(field_path="total_amount"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.TYPE_MISMATCH
    assert result.normalized_expected is None
    assert result.normalized_actual is None


def test_normalized_int_expected_fails_type_mismatch() -> None:
    result = evaluate_field(
        10000,
        "10000",
        _nspec(field_path="total_amount"),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.TYPE_MISMATCH
    assert result.normalized_expected is None
    assert result.normalized_actual is None


def test_normalized_absent_actual_fails_missing() -> None:
    result = evaluate_field(
        "Acme Ltd.",
        None,
        _nspec(),
        actual_state=ValueState.ABSENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.MISSING


def test_normalized_explicit_null_actual_fails_missing() -> None:
    result = evaluate_field(
        "Acme Ltd.",
        None,
        _nspec(),
        actual_state=ValueState.NULL,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.MISSING


def test_normalized_expected_null_and_absent_optional_passes() -> None:
    result = evaluate_field(
        None,
        None,
        _nspec(required=False),
        actual_state=ValueState.ABSENT,
    )

    assert result.passed is True
    assert result.failure_reason is None


def test_normalized_expected_null_and_present_value_fails_unexpected_value() -> None:
    result = evaluate_field(
        None,
        "Acme Ltd.",
        _nspec(),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.UNEXPECTED_VALUE


def test_normalized_required_whitespace_only_fails_empty_before_normalizing() -> None:
    result = evaluate_field(
        "Acme Ltd.",
        "   ",
        _nspec(),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.EMPTY


def test_normalized_optional_empty_expected_and_whitespace_actual_passes() -> None:
    result = evaluate_field(
        "",
        "   ",
        _nspec(required=False),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.normalized_expected == ""
    assert result.normalized_actual == ""


def test_normalized_records_normalized_values_on_pass() -> None:
    result = evaluate_field(
        "  Caf\u00e9  ",
        "Cafe\u0301",
        _nspec(case_sensitive=False),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is True
    assert result.normalized_expected == "caf\u00e9"
    assert result.normalized_actual == "caf\u00e9"


def test_normalized_records_normalized_values_on_fail() -> None:
    result = evaluate_field(
        "Acme Ltd.",
        "ACME SUPPLIES",
        _nspec(case_sensitive=False),
        actual_state=ValueState.PRESENT,
    )

    assert result.passed is False
    assert result.failure_reason is FailureReason.VALUE_MISMATCH
    assert result.normalized_expected == "acme ltd."
    assert result.normalized_actual == "acme supplies"


def test_normalized_carries_spec_severity_and_evaluator_type() -> None:
    spec = _nspec(severity=Severity.HIGH)

    passing = evaluate_field("Acme", "Acme", spec, actual_state=ValueState.PRESENT)
    failing = evaluate_field("Acme", "acme", spec, actual_state=ValueState.PRESENT)

    for result in (passing, failing):
        assert result.severity is Severity.HIGH
        assert result.evaluator_type is EvaluatorType.NORMALIZED_STRING
        assert result.field_path == "vendor_name"


def test_normalized_numeric_evaluator_still_raises_not_implemented() -> None:
    spec = FieldSpec(
        field_path="total_amount",
        evaluator_type=EvaluatorType.NUMERIC,
        severity=Severity.MEDIUM,
    )

    with pytest.raises(NotImplementedError, match="numeric"):
        evaluate_field(
            "10000.00",
            "10000.00",
            spec,
            actual_state=ValueState.PRESENT,
        )
