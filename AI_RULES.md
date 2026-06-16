# AI Development Constitution

## Core Principle

The objective of this project is to build a stable, maintainable, scalable application with minimal unnecessary change.

The AI's primary responsibility is preserving existing functionality while implementing requested improvements.

---

# Rule 1 - Never destroy working code

If code is working, do not rewrite it for style, optimization, or personal preference.

Only modify code when required to satisfy a requested change.

---

# Rule 2 - Minimize change

Always make the smallest possible modification.

Prefer changing 10 lines over rewriting 500.

Never replace an entire file when a small patch will solve the problem.

---

# Rule 3 - Preserve architecture

Do not restructure folders, rename files, rename functions, or rename variables unless explicitly requested.

Existing naming conventions must be respected.

---

# Rule 4 - Reuse before creating

Before creating:

* a function
* a class
* a component
* an endpoint
* a utility
* a helper

first verify whether one already exists.

Never duplicate functionality.

---

# Rule 5 - Explain first

Before making changes, provide:

* files that will change
* reason for each change
* possible risks
* expected outcome

Do not silently edit code.

---

# Rule 6 - Never guess

If requirements are ambiguous:

STOP.

Ask questions instead of making assumptions.

---

# Rule 7 - Backwards compatibility

Existing functionality must continue working unless explicitly approved to change.

Do not introduce breaking changes without warning.

---

# Rule 8 - Refactoring policy

No refactoring unless specifically requested.

No cosmetic rewrites.

No "cleanup" passes.

No unnecessary optimization.

Working code is valuable.

---

# Rule 9 - End-of-task report

Every completed task must include:

Files modified

Functions added

Functions removed

Breaking changes

Database changes

Configuration changes

Recommended next step

---

# Rule 10 - Documentation

If architecture changes, documentation must also be updated.

AI must keep documentation synchronized with implementation.

---

# Rule 11 - Confidence rule

If confidence is below 95%, stop and request clarification instead of implementing uncertain code.

---

# Rule 12 - Human intent wins

Never replace explicit user instructions with inferred best practices.

The user's stated objective has priority.

Rule 13 - Environment specifics

Development machine: Windows PC, use py (not python), use copy or ren (not cp or mv)
Runtime machine: Raspberry Pi (192.168.2.11:5000), use python3
Never assume commands work across both — always specify which environment

Rule 14 - File verification before delivery

Before giving the user a file to download, verify it:

Syntax check passes
All expected functions/strings are present
All removed things are actually gone
Print a checklist of passes/fails — ALL must pass before presenting



Rule 15 - Database and code files

Never modify mill.db directly — only through database.py migrations
Key files (app.py, database.py, index.html): patch only, never rewrite
Key files (scheduler.py, reports.py): avoid touching — they're stable

Rule 16 - User context

Roelof is learning software development — explain what each step does in plain language
Never assume he knows a command or concept without explaining it
Give complete instructions, not shortcuts

Rule 17 

Update  all files on completion of, we need to Log decission, 

Rule 18 please do not use web popups in code but instead make it a local popup inside software

Rule 19
Single Source of Truth

Every piece of information should exist in exactly one authoritative location. All other parts of the application should reference it rather than duplicate it.

Rule 20

If AI has  a suggestion ofor improvement please explain and notify before writing code.