"""Static validation of generated CadQuery Python (untrusted)."""

from __future__ import annotations

import ast
import re
from typing import Iterable, List, Set

from aiva3d.ai.types import CodeValidationResult

_FORBIDDEN_IMPORT_ROOTS: Set[str] = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "shutil",
    "pathlib",
    "urllib",
    "http",
    "ftplib",
    "pickle",
    "builtins",
    "importlib",
    "ctypes",
    "multiprocessing",
    "threading",
    "signal",
    "webbrowser",
    "tempfile",
    "glob",
    "sqlite3",
    "ssl",
    "requests",
}

_FORBIDDEN_NAMES: Set[str] = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "open",
    "input",
    "breakpoint",
    "help",
    "exit",
    "quit",
}

_FORBIDDEN_ATTR_PATTERNS = (
    re.compile(r"\bos\s*\.\s*system\b"),
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\bPopen\b"),
    re.compile(r"\b__builtins__\b"),
)


def _strip_markdown_fences(source: str) -> str:
    text = source.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _walk_import_roots(node: ast.AST) -> Iterable[str]:
    if isinstance(node, ast.Import):
        for alias in node.names:
            yield alias.name.split(".")[0]
    elif isinstance(node, ast.ImportFrom):
        if node.module:
            yield node.module.split(".")[0]


class _CadQueryAstVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.has_cq_import = False
        self.assigns_result = False

    def visit_Import(self, node: ast.Import) -> None:
        for root in _walk_import_roots(node):
            if root == "cadquery":
                self.has_cq_import = True
            elif root in _FORBIDDEN_IMPORT_ROOTS:
                self.errors.append(f"Forbidden import: {root}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for root in _walk_import_roots(node):
            if root == "cadquery":
                self.has_cq_import = True
            elif root in _FORBIDDEN_IMPORT_ROOTS:
                self.errors.append(f"Forbidden import: {root}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_NAMES:
            self.errors.append(f"Forbidden call: {node.func.id}()")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in _FORBIDDEN_NAMES and isinstance(node.ctx, ast.Load):
            self.errors.append(f"Forbidden name reference: {node.id}")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "result":
                self.assigns_result = True
        self.generic_visit(node)


def validate_cadquery_code(source: str) -> CodeValidationResult:
    cleaned = _strip_markdown_fences(source)
    errors: List[str] = []

    for pat in _FORBIDDEN_ATTR_PATTERNS:
        if pat.search(cleaned):
            errors.append(f"Forbidden pattern in source: {pat.pattern}")

    try:
        tree = ast.parse(cleaned, mode="exec")
    except SyntaxError as exc:
        return CodeValidationResult(
            ok=False,
            errors=[f"Syntax error: {exc}"],
            cleaned_code=cleaned,
        )

    visitor = _CadQueryAstVisitor()
    visitor.visit(tree)

    if not visitor.has_cq_import:
        errors.append("Code must import cadquery (typically `import cadquery as cq`).")
    if not visitor.assigns_result:
        errors.append("Code must assign the final model to variable `result`.")
    errors.extend(visitor.errors)

    return CodeValidationResult(
        ok=len(errors) == 0,
        errors=errors,
        cleaned_code=cleaned,
    )
