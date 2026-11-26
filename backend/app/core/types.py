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
    UNPARSEABLE = "unparseable"
    AMBIGUOUS = "ambiguous"
    SCHEMA_INVALID = "schema_invalid"
    RULE_FAILED = "rule_failed"
    EVIDENCE_UNVERIFIED = "evidence_unverified"


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
    expected: str | None
    actual: str | None
    evaluator_type: EvaluatorType
    passed: bool
    score: Decimal | None = None
    failure_reason: FailureReason | None = None
    severity: Severity = Severity.MEDIUM
    evidence: Evidence | None = None
    evaluator_version: str = EVALUATOR_VERSION

    def __post_init__(self) -> None:
        if not self.passed and self.failure_reason is None:
            raise ValueError("failed FieldResult requires a non-None failure_reason")
