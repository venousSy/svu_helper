# NotebookLM Tour — Outputs

This folder stores all commit snapshots produced during the commit-by-commit
tour of the `svu_helper` project.

## Structure

```
notebooklm_tour/
├── README.md               ← this file
├── 00_plan.md              ← session plan & commit index
└── commits/
    ├── 001_9290beb.md      ← one file per commit
    ├── 002_6f0fcc8.md
    └── ...
```

## How to use with NotebookLM

1. Open [notebooklm.google.com](https://notebooklm.google.com)
2. Create a new notebook called **svu_helper development**
3. For each commit file, click **Add source → Paste text** and paste the
   contents of the "NotebookLM Paste Block" section.

## Progress tracker

| # | SHA | Subject | Done? |
|---|-----|---------|-------|
| 01 | 9290beb | First version of Telegram Bot with Database | ☐ |
| 02 | 6f0fcc8 | Add admin broadcast feature | ☐ |
| 03 | 1c2bb60 | Add Admin Dashboard | ☐ |
| 04 | 2e2494f | Cleanup: Consolidated broadcast | ☐ |
| 05 | e40dff9 | Modularization Attempt 2 | ☐ |
| 06 | 95c476c | Modularization: Split client and admin handlers | ☐ |
| 07 | 95b39ae | Fix: Re-implemented Pending Projects callback | ☐ |
| 08 | 9fdb424 | Fix: Added missing accept/deny callbacks | ☐ |
| 09 | 2691d78 | Cleanup: Refactored client handler | ☐ |
| 10 | 3eaf4ca | Refactor: Removed legacy reply-based offer system | ☐ |
| 11 | 3cbc88b | UI Update: Interactive project management menu | ☐ |
| 12 | d8d8d2d | Feature: Button-based Offer System | ☐ |
| 13 | dddaa5c | Fix: Student deny access and offer note states | ☐ |
| 14 | e45bf9c | Fix: Reordered routers and callback conflict | ☐ |
| 15 | ede2a52 | Update: Descriptive status tracking & Master List | ☐ |
| 16 | 7a1a3b0 | Chore: pytest and initial test structure | ☐ |
| 17 | 894a690 | Refactor: Unified status update functions | ☐ |
| 18 | f02d326 | Testing: Feature logic tests | ☐ |
| 19 | b1d07e4 | Testing: Broadcast logic verification | ☐ |
| 20 | 9f245a7 | Refactor: Modularized admin views | ☐ |
| 21 | 4360e8c | Refactor: Modularized client views | ☐ |
| 22 | a2910f3 | Testing: Edge case tests and full user journey | ☐ |
| 23 | 0d5e006 | Fix: Added init_db call to full journey test | ☐ |
| 24 | 3821b51 | Testing: Expanded full journey tests | ☐ |
| 25 | bc09b3f | Docs: Admin handler docstrings | ☐ |
| 26 | b55f7ff | Docs: Client handler docstrings | ☐ |
| 27 | 2af6458 | Testing: Admin logic tests | ☐ |
| 28 | b6763ca | Fix: Student offer acceptance flow | ☐ |
| 29 | a9942d9 | Fix: TypeError and AttributeError in test suite | ☐ |
| 30 | 48510be | Fix: ValueError in master report | ☐ |
| 31 | 61ff17d | Update: Master Report display all projects | ☐ |
| 32 | e459452 | feat: Added 'Offered' status | ☐ |
| 33 | 1d43c3b | Update: Test suite assertions | ☐ |
| 34 | b9c89c5 | Refactor: Finalized modular refactor | ☐ |
| 35 | dbc860c | Rebuild: Database schema for /my_offers | ☐ |
| 36 | cb8f33b | Refactor: Modularize handlers and improve database | ☐ |
| 37 | f4a84c6 | Clean: Simplify DB schema | ☐ |
| 38 | 17a62d7 | Docs: Docstrings and type hints | ☐ |
| 39 | 6a24fba | Pro: Production readiness | ☐ |
| 40 | b0739bd | feat: Complete Arabic localization | ☐ |
| 41 | f8bab6e | Refactor: Cleanup tests and handlers | ☐ |
| 42 | ec35992 | Add Dockerfile and .dockerignore | ☐ |
| 43 | 21360f5 | Refactor: Centralize constants | ☐ |
| 44 | 35d831e | Fix: SyntaxError triple-quote | ☐ |
| 45 | b9bc420 | Refactor: Safety improvements and UX enhancements | ☐ |
| 46 | 58bf580 | Fix: Disable Markdown for /help | ☐ |
| 47 | 72258db | feat: Payment registry and input validation | ☐ |
| 48 | 52e545f | feat: Payment history UI and wipe_db | ☐ |
| 49 | b3c8af0 | feat: View receipt files from payment history | ☐ |
| 50 | 06f039b | fix: NameError in update_payment_status | ☐ |
| 51 | e0f6154 | refactor: utils/helpers.py and deduplication | ☐ |
| 52 | 18bceda | feat: docker-compose infra | ☐ |
| 53 | a9c88d0 | Setup: testing, linting, and CI | ☐ |
| 54 | 2fbfff9 | feat: Error handling, testing infra, and CI/CD | ☐ |
| 55 | f8d4744 | feat: Stats, docker, and i18n support | ☐ |
| 56 | 88566c1 | feat: Multiple admins via ADMIN_IDS | ☐ |
| 57 | c812629 | fix: ImportError ADMIN_IDS in helpers | ☐ |
| 58 | 97ff9fd | fix: ADMIN_ID fallback for comma-separated lists | ☐ |
| 59 | 3a73db0 | feat: Persistent FSM storage with MongoDB | ☐ |
| 60 | ba0a036 | feat: Rate limit, maintenance mode, sentry | ☐ |
| 61 | 38631f8 | fix: Register maintenance mode commands | ☐ |
| 62 | 33b8479 | feat: Admin Web Dashboard (FastAPI + React) | ☐ |
| 63 | 7f9f16a | chore: Dockerfiles for Railway | ☐ |
| 64 | f92fbda | fix(web): Bind Vite to Railway PORT | ☐ |
| 65 | 75b9ef8 | fix(web): Allow all hosts for Railway | ☐ |
| 66 | f4f5e9e | fix(api): Serialize ObjectId | ☐ |
| 67 | 66461ab | Refactor: Pydantic validation and Typed Callbacks | ☐ |
| 68 | 903ae4a | Fix: Restore missing client handlers | ☐ |
| 69 | c626369 | Enhance: CI/CD pipeline with GitHub Actions | ☐ |
| 70 | 36d11eb | Enhance: Structured Logging and BroadcastingQueue | ☐ |
| 71 | a13fd27 | Refactor: Enums, Repositories, pydantic-settings | ☐ |
| 72 | 92acea6 | Fix: docker-compose env vars for pydantic-settings | ☐ |
| 73 | b12edaf | feat: CI/CD, centralized logging, config parsing | ☐ |
| 74 | 7cb0135 | fix: AttributeError broadcast.py | ☐ |
| 75 | bcb120f | feat/fix: Comprehensive security improvements | ☐ |
| 76 | 3d4d825 | fix(web): Dynamic API url for production | ☐ |
| 77 | 7e2191b | fix(web): Prevent Vite proxy crash | ☐ |
| 78 | c9ef3b9 | refactor: Remove web dashboard | ☐ |
| 79 | 717b90c | Fix: ProjectStatus import in admin views | ☐ |
| 80 | 0d24fa0 | fix: Deep codebase audit fixes | ☐ |
| 81 | 2ff7130 | fix: Admin media type crash and input validation | ☐ |
| 82 | 41b4162 | fix: Robust md rendering and legacy fallback | ☐ |
| 83 | f803645 | test: Telethon E2E testing framework | ☐ |
| 84 | 0dc0baf | Update requirements and e2e student flow tests | ☐ |
| 85 | 59c9c2e | fix: Document payment receipts handling | ☐ |
| 86 | f120b8a | fix: Capture file_type in process_payment_proof | ☐ |
| 87 | b12475d | test: Fix all string assertions in E2E suite | ☐ |
| 88 | bd482a9 | test: Expand E2E suite to 9 tests | ☐ |
| 89 | d8c2075 | Security: IDOR protection and rate limiting | ☐ |
| 90 | 1536fbd | feat(i18n): Refine Arabic welcome message | ☐ |
| 91 | e05d9b4 | feat(kb): Student welcome navigation keyboard | ☐ |
| 92 | aaabd76 | feat(client): Keyboard support for project submission | ☐ |
| 93 | 565bff5 | refactor(kb): Student main menu inline keyboard | ☐ |
| 94 | b078e71 | feat(common): Inline help callback handler | ☐ |
| 95 | 9ecd911 | feat(client): Inline callback handlers | ☐ |
| 96 | fd70773 | fix(client): ProjectCallback import | ☐ |
| 97 | f74f4a2 | test(e2e): Expand full suite | ☐ |
| 98 | 11be637 | test(db): file_type in project insertion tests | ☐ |
| 99 | 9c1515a | test(helpers): File ID extraction tests | ☐ |
| 100 | 2066516 | test(stats): Repository tests for aggregation | ☐ |
| 101 | e14b2e2 | feat(arch): Domain entities and enums | ☐ |
| 102 | 427f0ba | feat(arch): Repository pattern and DB handles | ☐ |
| 103 | 284a978 | feat(middleware): Dependency injection | ☐ |
| 104 | 834b201 | refactor(handlers): Migrate to injected repositories | ☐ |
| 105 | a0e0c3b | feat: Interactive calendar for deadline selection | ☐ |
| 106 | 54cb107 | feat: Unify calendar processing in common handlers | ☐ |
| 107 | 343429f | refactor: Global middleware, fsm storage stability | ☐ |
| 108 | 8369d8c | refactor: English slugs for status enums | ☐ |
| 109 | 9069f55 | chore: Remove redundant e2e test files | ☐ |
| 110 | 2682159 | feat: NotebookLM git history report script | ☐ |
| 111 | 229066a | docs: Codebase report generator | ☐ |
| 112 | a0720ab | feat: Ticketing system for student-admin support | ☐ |
| 113 | 4b9fd9a | chore: pydantic version constraints | ☐ |
| 114 | 365fe05 | fix: Sparse index null collision | ☐ |
| 115 | d1644bb | fix: Suppress 'message not modified' error | ☐ |
| 116 | f7fb142 | feat: Cancel functionality in ticketing system | ☐ |
| 117 | 73d029c | feat: Closed ticket history and reopen | ☐ |
| 118 | f59c2e5 | feat: Admin ticket management | ☐ |
| 119 | f244593 | feat: Session timeout and activity tracking | ☐ |
| 120 | 2a92848 | refactor: Keyboard factory consolidation | ☐ |
| 121 | fe9258f | fix: Admin payment verification from receipt view | ☐ |
| 122 | dbd0066 | feat: Admin payment dashboard and calendar UX | ☐ |
| 123 | 1478938 | fix: Date validation in submission and offer flows | ☐ |
| 124 | 1d39dc9 | ux: Date selection recovery | ☐ |
| 125 | bf08d2a | feat: Full i18n pipeline and architectural guidelines | ☐ |
| 126 | c9ccbeb | feat: Multi-file attachment support | ☐ |
| 127 | 56cc658 | feat: Simplify project submission flow | ☐ |
| 128 | 2aa6138 | feat: Manage project button in admin alert | ☐ |
| 129 | b4cd1fc | chore: Arabic localization for project details | ☐ |
| 130 | ce8bf06 | test: Refactor and expand E2E full suite | ☐ |
| 131 | a671242 | test: Fix delivery date format in E2E | ☐ |
| 132 | 429e335 | feat: Date validation, cancellation, localization | ☐ |
| 133 | f216d16 | feat: LLM fuzzer into admin dashboard | ☐ |
| 134 | 1735148 | chore: Revert LLM fuzzer to Gemini 3.1 Flash Lite | ☐ |
