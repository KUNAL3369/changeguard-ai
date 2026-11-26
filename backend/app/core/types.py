from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Final

EVALUATOR_VERSION: Final[str] = "0.1.0"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


SEVERITY_ORDER: Final[tuple[Severity, ...]] = (
    Severity.CRITICAL,
    Severity.HIGH,
    Severity.MEDIUM,
    Severity.LOW,
)


class EvaluatorType(StrEnum):
    EXACT = "exact"
    REQUIRED = "required"
    NORMALIZED_STRING = "normalized_string"
    NUMERIC = "numeric"
    DATE = "date"
    JSON_SCHEMA = "json_schema"
    CUSTOM_RULE = "custom_rule"


class FailureReason(StrEnum):
    MISSING = "missing"
    EMPTY = "empty"
    TYPE_MISMATCH = "type_mismatch"
    UNEXPECTED_VALUE = "unexpected_value"
    VALUE_MISMATCH = "value_mismatch"
    UNPARSEABLE = "unparseable"
    AMBIGUOUS = "ambiguous"
    SCHEMA_INVALID = "schema_invalid"
    RULE_FAILED = "rule_failed"
    EVIDENCE_UNVERIFIED = "evidence_unverified"


class ValueState(StrEnum):
    """How the actual value arrived from the workflow output."""

    PRESENT = "present"
    ABSENT = "absent"
    NULL = "null"


@dataclass(frozen=True, slots=True)
class Evidence:
    quote: str | None = None
    page: int | None = None
    verified: bool | None = None


@dataclass(frozen=True, slots=True)
class FieldSpec:
    field_path: str
    evaluator_type: EvaluatorType
    severity: Severity
    required: bool = True


@dataclass(frozen=True, slots=True)
class FieldResult:
    field_path: str
    expected: object | None
    actual: object | None
    evaluator_type: EvaluatorType
    passed: bool
    actual_state: ValueState = ValueState.PRESENT
    score: Decimal | None = None
    failure_reason: FailureReason | None = None
    severity: Severity = Severity.MEDIUM
    evidence: Evidence | None = None
    evaluator_version: str = EVALUATOR_VERSION

    def __post_init__(self) -> None:
        if not self.passed and self.failure_reason is None:
            raise ValueError("failed FieldResult requires a non-None failure_reason")
        if self.actual_state in (ValueState.ABSENT, ValueState.NULL) and self.actual is not None:
            raise ValueError("actual must be None when actual_state is absent or null")
        if self.actual_state is ValueState.PRESENT and self.actual is None:
            raise ValueError("actual must not be None when actual_state is present")
