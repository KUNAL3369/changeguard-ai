"""Deterministic field evaluators (docs/EVALUATION_ENGINE.md).

Pure Python only: no DB/HTTP/env/clock, no float, no logging.
State and presence rules run before evaluator dispatch; an evaluator type
that is not implemented yet raises ``NotImplementedError`` instead of
silently passing.
"""

from app.core.types import (
    EvaluatorType,
    FailureReason,
    FieldResult,
    FieldSpec,
    ValueState,
)


def evaluate_field(
    expected: object | None,
    actual: object | None,
    spec: FieldSpec,
    *,
    actual_state: ValueState,
) -> FieldResult:
    """Evaluate one field deterministically.

    Presence and state rules (docs/EVALUATION_ENGINE.md, decisions D1-D3):
    - expected null + actual ABSENT/NULL -> pass, unless ``spec.required``,
      which fails ``missing`` (D1: a required promise never silently passes).
    - expected null + actual PRESENT -> fail ``unexpected_value`` (D2),
      except the ``required`` evaluator, which passes when the value is
      present and non-empty (D3: required checks presence only).
    - expected non-null + actual ABSENT/NULL -> fail ``missing``.
    - ``spec.required`` + empty/whitespace-only actual -> fail ``empty``
      (evaluated for non-``required`` evaluators; the ``required``
      evaluator always applies the non-empty gate itself).

    Raises ValueError when ``actual`` contradicts ``actual_state``.
    """
    if actual_state is ValueState.PRESENT and actual is None:
        raise ValueError(
            "actual_state=PRESENT requires a non-None actual; "
            "use ABSENT for a missing key or NULL for an explicit null"
        )
    if actual_state in (ValueState.ABSENT, ValueState.NULL) and actual is not None:
        raise ValueError(
            f"actual_state={actual_state.value} requires actual=None; "
            "an absent or null state cannot carry a value"
        )

    if expected is None:
        if actual_state in (ValueState.ABSENT, ValueState.NULL):
            if spec.required:
                # D1: required wins over the expected-null pass rule.
                return _build_result(
                    spec,
                    expected,
                    actual,
                    actual_state,
                    passed=False,
                    failure_reason=FailureReason.MISSING,
                )
            return _build_result(spec, expected, actual, actual_state, passed=True)
        if spec.evaluator_type is EvaluatorType.REQUIRED:
            return _evaluate_required(expected, actual, spec, actual_state)
        # D2: a value appeared where the dataset says null.
        return _build_result(
            spec,
            expected,
            actual,
            actual_state,
            passed=False,
            failure_reason=FailureReason.UNEXPECTED_VALUE,
        )

    if actual_state in (ValueState.ABSENT, ValueState.NULL):
        return _build_result(
            spec,
            expected,
            actual,
            actual_state,
            passed=False,
            failure_reason=FailureReason.MISSING,
        )

    if (
        spec.required
        and spec.evaluator_type is not EvaluatorType.REQUIRED
        and _is_empty(actual)
    ):
        return _build_result(
            spec,
            expected,
            actual,
            actual_state,
            passed=False,
            failure_reason=FailureReason.EMPTY,
        )

    match spec.evaluator_type:
        case EvaluatorType.EXACT:
            return _evaluate_exact(expected, actual, spec, actual_state)
        case EvaluatorType.REQUIRED:
            return _evaluate_required(expected, actual, spec, actual_state)
        case _:
            raise NotImplementedError(
                f"evaluator not implemented: {spec.evaluator_type.value}"
            )


def _build_result(
    spec: FieldSpec,
    expected: object | None,
    actual: object | None,
    actual_state: ValueState,
    *,
    passed: bool,
    failure_reason: FailureReason | None = None,
) -> FieldResult:
    """Stamp field_path, evaluator_type and severity from the spec (D4: score stays None)."""
    return FieldResult(
        field_path=spec.field_path,
        expected=expected,
        actual=actual,
        evaluator_type=spec.evaluator_type,
        passed=passed,
        actual_state=actual_state,
        failure_reason=failure_reason,
        severity=spec.severity,
    )


def _is_empty(value: object) -> bool:
    """True only for None and empty/whitespace-only strings.

    Deliberately not truthiness: ``0`` and ``False`` are present values.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def _evaluate_exact(
    expected: object | None,
    actual: object | None,
    spec: FieldSpec,
    actual_state: ValueState,
) -> FieldResult:
    """Strict equality after an exact type check; no normalization (EVALUATION_ENGINE)."""
    if type(actual) is not type(expected):
        return _build_result(
            spec,
            expected,
            actual,
            actual_state,
            passed=False,
            failure_reason=FailureReason.TYPE_MISMATCH,
        )
    if actual != expected:
        return _build_result(
            spec,
            expected,
            actual,
            actual_state,
            passed=False,
            failure_reason=FailureReason.VALUE_MISMATCH,
        )
    return _build_result(spec, expected, actual, actual_state, passed=True)


def _evaluate_required(
    expected: object | None,
    actual: object | None,
    spec: FieldSpec,
    actual_state: ValueState,
) -> FieldResult:
    """Present and non-empty only; never compares against expected (D3)."""
    if _is_empty(actual):
        return _build_result(
            spec,
            expected,
            actual,
            actual_state,
            passed=False,
            failure_reason=FailureReason.EMPTY,
        )
    return _build_result(spec, expected, actual, actual_state, passed=True)
