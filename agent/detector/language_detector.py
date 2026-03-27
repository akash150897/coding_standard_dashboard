"""Detects the primary programming language used in a project."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from agent.utils.logger import get_logger

logger = get_logger(__name__)

# Extension → language mapping
_EXT_LANGUAGE: Dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".java": "java",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".rs": "rust",
    ".swift": "swift",
    ".kt": "kotlin",
}

# Presence of these files strongly indicates a language
_INDICATOR_FILES: Dict[str, str] = {
    "requirements.txt": "python",
    "setup.py": "python",
    "setup.cfg": "python",
    "pyproject.toml": "python",
    "Pipfile": "python",
    # package.json handled separately to distinguish JS vs TS
    # "package.json": "javascript",
    "go.mod": "go",
    "Gemfile": "ruby",
    "pom.xml": "java",
    "build.gradle": "java",
    "composer.json": "php",
    "Cargo.toml": "rust",
}


class LanguageDetector:
    """Detects the primary language of the project and per-file languages."""

    def __init__(self, project_root: str = ".") -> None:
        self.project_root = Path(project_root)

    def detect_primary_language(self) -> str:
        """Return the primary language used in the project.

        Strategy:
        1. Check well-known indicator files in the project root.
        2. Count file extensions across the project.
        3. Fall back to 'unknown'.
        """
        # 1. Indicator files (fast and reliable) — check root and one level of subdirs
        search_dirs = [self.project_root]
        for subdir in self.project_root.iterdir():
            if subdir.is_dir() and subdir.name not in {"node_modules", ".git", "venv", "dist", "build"}:
                search_dirs.append(subdir)

        for search_dir in search_dirs:
            for filename, lang in _INDICATOR_FILES.items():
                if (search_dir / filename).exists():
                    logger.debug("Language detected via indicator file '%s': %s", filename, lang)
                    return lang

        # 2. Check if package.json marks a TypeScript project — root and subdirs
        for search_dir in search_dirs:
            pkg_json = search_dir / "package.json"
            if pkg_json.exists():
                try:
                    data = json.loads(pkg_json.read_text(encoding="utf-8"))
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    if "typescript" in deps:
                        return "typescript"
                except Exception:
                    pass
                return "javascript"

        # 3. Count extensions
        counts: Dict[str, int] = {}
        for ext, lang in _EXT_LANGUAGE.items():
            count = self._count_files_with_extension(ext)
            if count:
                counts[lang] = counts.get(lang, 0) + count

        if counts:
            primary = max(counts, key=lambda k: counts[k])
            logger.debug("Language detected via extension count: %s", primary)
            return primary

        return "unknown"

    def detect_file_language(self, file_path: str) -> Optional[str]:
        """Return the language for a single file based on its extension."""
        ext = Path(file_path).suffix.lower()
        return _EXT_LANGUAGE.get(ext)

    def _count_files_with_extension(self, ext: str) -> int:
        count = 0
        skip = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"}
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in skip]
            count += sum(1 for f in files if f.endswith(ext))
        return count

    @staticmethod
    def get_extensions_for_language(language: str) -> List[str]:
        """Return all file extensions associated with a given language."""
        return [ext for ext, lang in _EXT_LANGUAGE.items() if lang == language]
