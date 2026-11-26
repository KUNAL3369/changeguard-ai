from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.core.types import (
    EVALUATOR_VERSION,
    SEVERITY_ORDER,
    EvaluatorType,
    Evidence,
    FailureReason,
    FieldResult,
    FieldSpec,
    Severity,
)


def test_severity_order_constant() -> None:
    assert SEVERITY_ORDER == (
        Severity.CRITICAL,
        Severity.HIGH,
        Severity.MEDIUM,
        Severity.LOW,
    )


def test_field_spec_is_immutable() -> None:
    spec = FieldSpec(
        field_path="total_amount",
        evaluator_type=EvaluatorType.NUMERIC,
        severity=Severity.CRITICAL,
    )

    with pytest.raises(FrozenInstanceError):
        spec.severity = Severity.LOW


def test_field_result_is_immutable() -> None:
    result = FieldResult(
        field_path="vendor_name",
        expected="Acme Pvt Ltd",
        actual="Acme Pvt Ltd",
        evaluator_type=EvaluatorType.EXACT,
        passed=True,
    )

    with pytest.raises(FrozenInstanceError):
        result.passed = False


def test_field_result_defaults_are_explicit() -> None:
    result = FieldResult(
        field_path="invoice_number",
        expected="INV-1042",
        actual="INV-1042",
        evaluator_type=EvaluatorType.EXACT,
        passed=True,
    )

    assert result.score is None
    assert result.failure_reason is None
    assert result.evidence is None
    assert result.evaluator_version == EVALUATOR_VERSION
    assert result.severity == Severity.MEDIUM


def test_field_result_failure_reason_is_enum_value() -> None:
    result = FieldResult(
        field_path="invoice_number",
        expected="INV-1042",
        actual=None,
        evaluator_type=EvaluatorType.REQUIRED,
        passed=False,
        failure_reason=FailureReason.MISSING,
    )

    assert result.failure_reason is FailureReason.MISSING
    assert result.failure_reason.value == "missing"


def test_failed_field_result_requires_reason() -> None:
    with pytest.raises(ValueError, match="failure_reason"):
        FieldResult(
            field_path="total_amount",
            expected="10000.00",
            actual="9000.00",
            evaluator_type=EvaluatorType.NUMERIC,
            passed=False,
        )


def test_score_uses_decimal_not_float() -> None:
    result = FieldResult(
        field_path="total_amount",
        expected="10000.00",
        actual="10000.00",
        evaluator_type=EvaluatorType.NUMERIC,
        passed=True,
        score=Decimal("1.000"),
    )

    assert isinstance(result.score, Decimal)
    assert result.score == Decimal("1.000")


def test_evidence_fields_are_nullable() -> None:
    evidence = Evidence()

    assert evidence.quote is None
    assert evidence.page is None
    assert evidence.verified is None
