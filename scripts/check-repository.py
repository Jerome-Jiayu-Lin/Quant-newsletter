#!/usr/bin/env python3
"""Check the repository invariants that keep future agent changes navigable."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path
from typing import Iterable


MAX_PRODUCT_MODULE_LINES = 400

MODULE_DEPENDENCIES: dict[str, frozenset[str]] = {
    "__init__": frozenset({"pipeline"}),
    "models": frozenset(),
    "http": frozenset(),
    "features": frozenset({"models"}),
    "ranking": frozenset({"models"}),
    "candidates": frozenset({"models"}),
    "sources": frozenset({"http", "models"}),
    "summarize": frozenset({"models"}),
    "publication": frozenset(),
    "r2": frozenset({"publication"}),
    "publish_cli": frozenset({"publication", "r2"}),
    "pipeline": frozenset({"candidates", "features", "http", "models", "ranking", "sources", "summarize"}),
    "archive": frozenset(),
    "cli": frozenset({"archive", "pipeline"}),
}

ALLOWED_ROOT_FILES = {
    ".env.local.example",
    ".gitignore",
    "AGENTS.md",
    "ARCHITECTURE.md",
    "CONTEXT.md",
    "README.md",
    "pyproject.toml",
}

REQUIRED_KNOWLEDGE_FILES = {
    "AGENTS.md",
    "ARCHITECTURE.md",
    "CONTEXT.md",
    "docs/QUALITY.md",
    "docs/technical-debt.md",
    "docs/exec-plans/index.md",
    "docs/exec-plans/template.md",
}


def _internal_dependencies(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    dependencies: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level and node.module:
                dependencies.add(node.module.split(".", 1)[0])
            elif node.module and node.module.startswith("quantbrief."):
                dependencies.add(node.module.split(".")[1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("quantbrief."):
                    dependencies.add(alias.name.split(".")[1])
    return dependencies


def python_architecture_violations(root: Path) -> list[str]:
    package = root / "quantbrief"
    violations: list[str] = []
    for path in sorted(package.glob("*.py")):
        module = path.stem
        relative = path.relative_to(root).as_posix()
        allowed = MODULE_DEPENDENCIES.get(module)
        if allowed is None:
            violations.append(
                f"{relative}: undeclared product module. Add its responsibility and dependency direction to "
                "ARCHITECTURE.md, then add an explicit rule to scripts/check-repository.py."
            )
            continue

        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_PRODUCT_MODULE_LINES:
            violations.append(
                f"{relative}: {line_count} lines exceeds the {MAX_PRODUCT_MODULE_LINES}-line navigation limit. "
                "Extract a cohesive deep module with a small interface before adding more behavior."
            )

        try:
            dependencies = _internal_dependencies(path)
        except SyntaxError as error:
            violations.append(f"{relative}:{error.lineno}: cannot inspect dependencies until the syntax error is fixed.")
            continue
        unexpected = sorted(dependencies - allowed)
        if unexpected:
            permitted = ", ".join(sorted(allowed)) or "none"
            violations.append(
                f"{relative}: imports disallowed module(s) {', '.join(unexpected)}; allowed: {permitted}. "
                "Move orchestration upward, or document and declare a deliberate new edge."
            )
    return violations


def _visible_repository_files(root: Path) -> Iterable[Path]:
    try:
        completed = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return (path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts)
    return (root / line for line in completed.stdout.splitlines() if line)


def repository_layout_violations(root: Path) -> list[str]:
    violations: list[str] = []
    for relative in sorted(REQUIRED_KNOWLEDGE_FILES):
        if not (root / relative).is_file():
            violations.append(f"{relative}: required repository knowledge file is missing.")

    for path in _visible_repository_files(root):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if len(relative.parts) != 1:
            continue
        name = relative.name
        if name.startswith(".env") and name != ".env.local.example":
            continue
        if name not in ALLOWED_ROOT_FILES:
            violations.append(
                f"{name}: repository-root file has no declared owner. Move it to the canonical location in "
                "AGENTS.md or deliberately add a project-wide entry point to this checker."
            )
    return violations


def collect_violations(root: Path) -> list[str]:
    return python_architecture_violations(root) + repository_layout_violations(root)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    violations = collect_violations(root)
    if not violations:
        print("repository architecture: ok")
        return 0
    print("repository architecture: failed", file=sys.stderr)
    for violation in violations:
        print(f"- {violation}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
