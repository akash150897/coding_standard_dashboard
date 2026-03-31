"""Installs the code review agent as a git pre-commit hook."""

import os
import platform
import stat
import subprocess
import sys
from pathlib import Path
from typing import Optional

from agent.utils.logger import get_logger

logger = get_logger(__name__)


_PROVIDERS = {
    "1": ("GROQ_API_KEY",       "Groq",      "https://console.groq.com        (Free, no limits)"),
    "2": ("GEMINI_API_KEY",     "Gemini",    "https://aistudio.google.com     (Free tier)"),
    "3": ("OPENAI_API_KEY",     "OpenAI",    "https://platform.openai.com     (Paid)"),
    "4": ("ANTHROPIC_API_KEY",  "Anthropic", "https://console.anthropic.com   (Paid)"),
}


def _save_api_key(env_var: str, key: str) -> None:
    """Persist the given API key as a permanent system environment variable."""
    system = platform.system()
    if system == "Windows":
        subprocess.run(["setx", env_var, key], check=True, capture_output=True)
        os.environ[env_var] = key
        print(f"[OK] {env_var} saved to Windows environment variables.")
        print("")
        print("=" * 62)
        print("  IMPORTANT: Close this terminal and open a NEW one before")
        print("  running git commit — Windows requires a new session to")
        print("  load the saved environment variable.")
        print("=" * 62)
    else:
        shell = os.environ.get("SHELL", "")
        profile = Path.home() / (".zshrc" if "zsh" in shell else ".bashrc")
        line = f'\nexport {env_var}="{key}"\n'
        with open(profile, "a", encoding="utf-8") as f:
            f.write(line)
        os.environ[env_var] = key
        print(f"[OK] {env_var} saved to {profile}")
        print(f"[INFO] Run: source {profile}  (or open a new terminal)")


def _prompt_api_key() -> None:
    """Ask the user to choose an AI provider and enter their API key."""
    # Check if any key is already set
    existing_var = next(
        (var for var, _, _ in _PROVIDERS.values() if os.environ.get(var)), None
    )
    if existing_var:
        print(f"\n[INFO] {existing_var} is already set ({os.environ[existing_var][:8]}...).")
        try:
            answer = input("       Do you want to replace it? [y/N] ").strip().lower()
        except KeyboardInterrupt:
            print("\n[WARNING] Skipped.")
            return
        if answer != "y":
            return

    print("\n[SETUP] Choose your AI provider for code review:\n")
    for num, (env_var, name, url) in _PROVIDERS.items():
        print(f"  {num}. {name:12}  {url}")

    print()
    try:
        choice = input("  Enter choice (1-4): ").strip()
    except KeyboardInterrupt:
        print("\n[WARNING] Skipped. Run 'cra install' again to set the key later.")
        return

    if choice not in _PROVIDERS:
        print("[WARNING] Invalid choice — skipping. Run 'cra install' again to set the key later.")
        return

    env_var, name, url = _PROVIDERS[choice]
    print(f"\n  Get your free API key at: {url.split()[0]}")
    try:
        key = input(f"  Enter your {env_var}: ").strip()
    except KeyboardInterrupt:
        print("\n[WARNING] Skipped. Run 'cra install' again to set the key later.")
        return

    if not key:
        print("[WARNING] No key entered — skipping. Run 'cra install' again to set it later.")
        return

    _save_api_key(env_var, key)

_HOOK_TEMPLATE = """\
#!/bin/sh
# Code Review Agent — pre-commit hook
# Auto-installed by: cra install

# Use forward slashes — backslashes break Git's sh.exe on Windows
PYTHON="{python_bin}"

# Deactivate any active venv so the system Python (where cra is installed) is used
unset VIRTUAL_ENV
unset PYTHONHOME

# Review only staged files before the commit is created (with AI review)
"$PYTHON" -m agent.cli review --staged --ai
STATUS=$?
exit $STATUS
"""


def install_hook(repo_root: Optional[str] = None, force: bool = False) -> bool:
    """Install the pre-commit hook into the git repository.

    Args:
        repo_root: Path to the git repository root. Defaults to CWD.
        force: Overwrite an existing hook without prompting.

    Returns:
        True if installation succeeded.
    """
    root = Path(repo_root or os.getcwd())
    hooks_dir = root / ".git" / "hooks"

    if not hooks_dir.exists():
        logger.error("No .git/hooks directory found at %s", root)
        print(f"[ERROR] {root} does not appear to be a git repository.")
        return False

    hook_path = hooks_dir / "pre-commit"
    # Convert backslashes to forward slashes — Git's sh.exe on Windows
    # silently fails when the Python path contains backslashes
    python_bin = sys.executable.replace("\\", "/")

    if hook_path.exists() and not force:
        content = hook_path.read_text()
        if "Code Review Agent" in content:
            print(f"[INFO] Hook already installed at {hook_path}")
            _prompt_api_key()
            return True
        print(f"[WARNING] A pre-commit hook already exists at {hook_path}")
        answer = input("Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("[ABORTED] Hook installation cancelled.")
            return False

    hook_content = _HOOK_TEMPLATE.format(
        python_bin=python_bin,
    )
    # Write with Unix line endings — CRLF breaks sh execution on Windows/Git Bash
    hook_path.write_text(hook_content, encoding="utf-8", newline="\n")

    # Make the hook executable
    current = hook_path.stat().st_mode
    hook_path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"[OK] Pre-commit hook installed at {hook_path}")

    # Ask for API key
    _prompt_api_key()

    return True


def _remove_api_key() -> None:
    """Remove all known AI provider API keys from the system environment."""
    all_vars = [var for var, _, _ in _PROVIDERS.values()]
    system = platform.system()
    removed = []

    for env_var in all_vars:
        if system == "Windows":
            result = subprocess.run(
                ["reg", "delete", "HKCU\\Environment", "/v", env_var, "/f"],
                capture_output=True,
            )
            if result.returncode == 0:
                removed.append(env_var)
        else:
            shell = os.environ.get("SHELL", "")
            profile = Path.home() / (".zshrc" if "zsh" in shell else ".bashrc")
            if profile.exists():
                lines = profile.read_text(encoding="utf-8").splitlines(keepends=True)
                new_lines = [l for l in lines if env_var not in l]
                if len(new_lines) != len(lines):
                    profile.write_text("".join(new_lines), encoding="utf-8")
                    removed.append(env_var)
        os.environ.pop(env_var, None)

    if removed:
        print(f"[OK] Removed: {', '.join(removed)}")
    else:
        print("[INFO] No API keys found to remove.")


def uninstall_hook(repo_root: Optional[str] = None) -> bool:
    """Remove the code review agent pre-commit hook if it was installed by us.

    Args:
        repo_root: Path to the git repository root. Defaults to CWD.

    Returns:
        True if the hook was removed (or was not present).
    """
    root = Path(repo_root or os.getcwd())
    hook_path = root / ".git" / "hooks" / "pre-commit"

    if not hook_path.exists():
        print("[INFO] No pre-commit hook found — nothing to remove.")
    else:
        content = hook_path.read_text()
        if "Code Review Agent" not in content:
            print("[WARNING] The existing pre-commit hook was not installed by this agent.")
            print("[SKIPPED] Remove it manually if needed.")
            return False
        hook_path.unlink()
        print(f"[OK] Pre-commit hook removed from {hook_path}")

    # Offer to remove any set API keys
    all_vars = [var for var, _, _ in _PROVIDERS.values()]
    set_vars = [v for v in all_vars if os.environ.get(v)]
    if set_vars:
        print(f"\n[INFO] Found API key(s): {', '.join(set_vars)}")
        try:
            answer = input("Do you also want to remove them from your system? [y/N] ").strip().lower()
        except KeyboardInterrupt:
            answer = "n"
        if answer == "y":
            _remove_api_key()
    else:
        print("[INFO] No API keys found in environment — nothing to clean up.")

    print("\n[INFO] To fully remove the package run:  pip uninstall code-review-agent")
    return True
