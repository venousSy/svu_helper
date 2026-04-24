# NotebookLM Commit-Tour — Session Plan

## Goal
Walk through the full git history of `svu_helper` (134 commits, oldest → newest) one commit at a time. Each turn produces a compact, copy-paste-ready block that you drop into a Google NotebookLM source.

---

## How the Project Evolved (high-level arc)

| Phase | Commits | Theme |
|-------|---------|-------|
| 1 | #01 – #08 | SQLite monolith bot — first working version, broadcast, modularization |
| 2 | #09 – #35 | Button-driven offer system, master list, status tracking |
| 3 | #36 – #54 | Production hardening — Dockerfile, i18n, payment flow, helpers |
| 4 | #55 – #78 | Multi-admin, MongoDB FSM, web dashboard (added then removed) |
| 5 | #79 – #100 | Security, E2E tests, inline keyboards, clean architecture (repos, DI) |
| 6 | #101 – #110 | Interactive calendar, middleware refactor |
| 7 | #111 – #120 | Ticketing system, sparse index fixes, keyboard factory |
| 8 | #121 – #134 | i18n pipeline, multi-file uploads, date validation, LLM fuzzer |

---

## Per-Turn Workflow

```
User says "next"
     ↓
1. Run: git show --stat <sha>   → get file list
2. Run: git log -1 --format="%ad %s" --date=short <sha>  → date + subject
3. (Optional) git show <sha> -- <key_file>   → ≤30 lines of representative code
4. Produce the standard output block (see skill)
5. Save output to notebooklm_tour/commits/NNN_<sha>.md
6. Wait for user
```

---

## Output Format (per commit)

```
━━━━━━━━━━━━━━━━━━━━━━━━
COMMIT #N — <sha>
<subject>
━━━━━━━━━━━━━━━━━━━━━━━━
🗂 Files Changed …
🎯 What & Why …
🔑 Key Snippet (optional) …
📋 NotebookLM Paste Block …
━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Token-Saving Rules

- ❌ Never dump full `git diff`
- ❌ Never reprint the commit list unless user types `list`
- ✅ ≤ 30 lines per code snippet
- ✅ Use `git show --stat` for file lists, `git show <sha> -- <file>` for targeted diffs
- ✅ The skill file stores the commit list — no need to keep it in context
- ✅ Save each commit output to `notebooklm_tour/commits/` automatically

---

## Quick-Command Reference

| Type | Effect |
|------|--------|
| `next` | Next commit |
| `prev` | Previous commit |
| `goto N` | Jump to commit #N |
| `list` | Reprint the full commit table |
| `status` | Show current position |

---

## Folder Structure

```
c:\Users\ali\svu_helper\notebooklm_tour\
├── README.md            ← progress tracker with all 134 commits
├── 00_plan.md           ← this file
└── commits\
    ├── 001_9290beb.md   ← one file per completed commit
    ├── 002_6f0fcc8.md
    └── ...
```

---

## Current Position

> **#00 — not started.** Type `next` or `goto 1` to begin.
