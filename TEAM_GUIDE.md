# Code Review Agent — Team Guide

**Version:** 1.0 &nbsp;|&nbsp; **Team:** B4G Projects &nbsp;|&nbsp; **Updated:** March 2026

---

## What Is It?

> A silent quality guard that automatically checks your code **every time you commit** —
> before anything reaches the shared repository.

You write code. You `git commit`. The agent runs in the background, checks your changes
against the team's coding standards, and either lets the commit through or tells you exactly
what to fix.

**No extra tools to open. No extra steps. It just works.**

---

## The Problem It Solves

```
WITHOUT the agent                    WITH the agent
─────────────────────────────        ──────────────────────────────
Developer commits code               Developer commits code
        ↓                                    ↓
Code reaches the repo                Agent checks automatically
        ↓                                    ↓
Reviewer catches issues         ┌── PASS ──► Code reaches the repo
  (days later, if at all)       │
        ↓                       └── FAIL ──► Developer told exactly
Expensive fix in production                  what to fix, right now
```

| Catching an issue...     | Cost to fix |
|--------------------------|-------------|
| At commit time           | **1×**      |
| During code review       | 6×          |
| During testing           | 15×         |
| In production            | 100×        |

---

## What It Checks

### 🔒 Security
| Issue caught | Example |
|---|---|
| Hardcoded passwords / API keys | `JWT_SECRET = "abc123"` |
| `.env` files accidentally committed | `server/.env` staged for commit |
| Dangerous functions | `eval(user_input)` |

### 🧹 Code Quality
| Issue caught | Example |
|---|---|
| Debug code left in | `console.log("testing 123")` |
| Unresolved merge conflicts | `<<<<<<< HEAD` in source file |
| Unused imports | `import os` never used |

### ⚡ Performance
| Issue caught | Example |
|---|---|
| Missing async/await | Blocking calls in async functions |
| Unvalidated API inputs | Route handlers with no input check |

### 📐 Team Standards
| Issue caught | Example |
|---|---|
| Wrong naming conventions | `myFunction` instead of `my_function` |
| Hardcoded URLs | `http://192.168.1.10:3000/api` in code |
| Missing type hints (Python) | Functions with no return type |

---

## What You See When a Commit Is Blocked

```
══════════════════════════════════════════════════════════════
  Code Review Agent  —  Pre-Commit Gate
  Language  : JavaScript
  Framework : Express
══════════════════════════════════════════════════════════════

  📄 server/config/db.js

  ✖ [ERROR  ]   Line 4   COM001 — Hardcoded secret detected.
                → const DB_PASS = "supersecret123"
                Fix: Use process.env.DB_PASS instead.

  ✖ [ERROR  ]   file     COM006 — .env file detected in commit.
                Fix: Add .env to .gitignore and use .env.example.

  ──────────────────────────────────────────────────────────
  2 file(s) scanned  |  11 rule(s) applied  |  2 error(s)

  🚫  Commit BLOCKED — fix the violations above and try again.
```

The developer knows:
- ✅ **Which file** has the problem
- ✅ **Which line** to look at
- ✅ **What the problem is**
- ✅ **How to fix it**

---

## What You See When Everything Is Clean

```
══════════════════════════════════════════════════════════════
  Code Review Agent  —  Pre-Commit Gate
  Language  : Python
  Framework : FastAPI
══════════════════════════════════════════════════════════════

  ──────────────────────────────────────────────────────────
  3 file(s) scanned  |  20 rule(s) applied  |  0 errors

  ✅  All checks passed — commit allowed.
```

---

## Supported Technologies

| Language | Frameworks Supported |
|---|---|
| **Python** | FastAPI, Django, Flask |
| **JavaScript** | React, Next.js, Node.js + Express, React Native |
| **TypeScript** | React, Node.js |

The agent **auto-detects** the language and framework — no configuration needed.

---

## Installation

> ⏱ Takes less than 2 minutes per machine.

---

### Step 1 — Install the agent (once per machine)

Open a terminal and run:

```bash
pip install git+https://github.com/pratham-b4g/code_review_agent.git
```

Verify it installed:

```bash
cra --help
```

You should see the usage menu printed out.

---

### Step 2 — Activate it in your project (once per project)

Navigate to your project folder and run:

```bash
cd path\to\your\project
cra install
```

You should see:

```
[OK] Pre-commit hook installed at path\to\your\project\.git\hooks\pre-commit
```

---

### Step 3 — Done

From this point on, every `git commit` automatically runs the agent.
No other changes to your workflow are needed.

---

### Optional — Install a linter for richer feedback

**Python projects:**
```bash
pip install ruff
```

**JavaScript / Node.js projects:**
```bash
npm install --save-dev eslint
```

---

## Removing It

If you ever need to remove the agent from a project:

```bash
cra uninstall
```

---

## Severity Levels

| Level | Symbol | Effect |
|---|---|---|
| **Error** | `✖ [ERROR]` | Commit is **blocked** — must fix before committing |
| **Warning** | `⚠ [WARNING]` | Commit is **allowed** — but fix is recommended |
| **Info** | `ℹ [INFO]` | Informational note only |

---

## FAQ

**Q: Does this replace code review?**
No. It handles the mechanical checks so your reviewers can focus on logic and architecture.

**Q: What if the agent incorrectly blocks my commit?**
You can temporarily bypass it with `git commit --no-verify`. But use sparingly — the rules exist for good reasons.

**Q: Can we add our own rules?**
Yes. Rules are JSON files. Speak to the team lead about adding project-specific rules.

**Q: Does it slow down commits?**
No. A typical review runs in under 1 second.

**Q: What if I'm on Python 3.8 or below?**
The agent requires Python 3.9+. Run `python --version` to check.

---

*Code Review Agent v1.0 — Built for B4G Projects*
