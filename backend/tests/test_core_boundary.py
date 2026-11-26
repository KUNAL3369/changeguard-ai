import ast
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parents[1] / "app" / "core"

FORBIDDEN_APP_PREFIXES = (
    "app.api",
    "app.adapters",
    "app.config",
    "app.db",
    "app.main",
    "app.services",
    "app.worker",
)

FORBIDDEN_THIRD_PARTY = {
    "fastapi",
    "httpx",
    "logging",
    "pydantic",
    "requests",
    "sqlalchemy",
    "boto3",
    "supabase",
}

FORBIDDEN_STDLIB_IO = {
    "os",
    "pathlib",
    "socket",
    "subprocess",
    "sys",
}

CLOCK_CALLS = ("datetime.now(", "datetime.today(", "datetime.utcnow(", "time.time(")


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def test_app_core_has_no_forbidden_imports() -> None:
    violations: list[str] = []

    for path in sorted(CORE_DIR.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        roots = imported_roots(tree)

        for root in sorted(roots & FORBIDDEN_THIRD_PARTY):
            violations.append(f"{path.name}: imports forbidden dependency '{root}'")

        for root in sorted(roots & FORBIDDEN_STDLIB_IO):
            violations.append(f"{path.name}: imports forbidden stdlib I/O module '{root}'")

        from_imports = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        ]
        for module in from_imports:
            if module.startswith(FORBIDDEN_APP_PREFIXES):
                violations.append(f"{path.name}: imports forbidden app layer '{module}'")

        for call in CLOCK_CALLS:
            if call in source:
                violations.append(f"{path.name}: contains forbidden clock call '{call}'")

    assert violations == [], "\n".join(violations)


def test_app_core_types_imports_without_forbidden_modules() -> None:
    import app.core.types as core_types

    assert core_types.EVALUATOR_VERSION == "0.1.0"


def _annotation_has_float(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id == "float":
            return True
        if isinstance(child, ast.Attribute) and child.attr == "float":
            return True
    return False


def _float_violations(tree: ast.AST, name: str) -> list[str]:
    """Flag float literals, float() calls and float annotations.

    Narrowed on purpose (T08 D7): ``isinstance(x, float)`` is allowed.
    """
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            violations.append(f"{name}:{node.lineno}: float literal {node.value!r}")
        elif isinstance(node, ast.Call):
            func = node.func
            if (isinstance(func, ast.Name) and func.id == "float") or (
                isinstance(func, ast.Attribute) and func.attr == "float"
            ):
                violations.append(f"{name}:{node.lineno}: float() call")
        elif isinstance(node, ast.arg) and node.annotation is not None:
            if _annotation_has_float(node.annotation):
                violations.append(f"{name}:{node.lineno}: float annotation")
        elif isinstance(node, ast.AnnAssign) and node.annotation is not None:
            if _annotation_has_float(node.annotation):
                violations.append(f"{name}:{node.lineno}: float annotation")
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.returns is not None:
            if _annotation_has_float(node.returns):
                violations.append(f"{name}:{node.lineno}: float annotation")
    return violations


def test_app_core_has_no_float_literals_calls_or_annotations() -> None:
    violations: list[str] = []

    for path in sorted(CORE_DIR.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        violations.extend(_float_violations(tree, path.name))

    assert violations == [], "\n".join(violations)


def test_float_guard_detects_synthetic_violations() -> None:
    bad = ast.parse(
        "def scale(x: float) -> float:\n"
        "    return float(x) * 1.5\n"
    )
    violations = _float_violations(bad, "snippet.py")

    assert any("float literal" in item for item in violations)
    assert any("float() call" in item for item in violations)
    assert any("float annotation" in item for item in violations)

    allowed = ast.parse(
        "def check(x: object) -> bool:\n"
        "    return isinstance(x, float)\n"
    )
    assert _float_violations(allowed, "allowed.py") == []
