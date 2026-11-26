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
