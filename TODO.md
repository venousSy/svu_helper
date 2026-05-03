# SVU Helper Bot - Future Enhancements & TODOs

## High Priority (Important)
- [x] **Fix Architecture Violation (i18n)**: Extract the hard-coded Arabic session timeout message in `main.py` and move it to `locales/ar.json` and `constants.py` to strictly comply with `AGENTS.md`.
- [x] **State Separation (Redis)**: Implement Redis for Aiogram's FSM storage and rate-limiting (`ThrottlingMiddleware`) to offload ephemeral state from MongoDB, drastically improving responsiveness.
- [ ] **Google Drive Backup**: Implement automated MongoDB backups to Google Drive every 6 hours according to `google_drive_backup_plan.md` to prevent data loss. *(Note: Remove the `google_drive_backup_plan.md` file once finished).*

## Needs More Study
- [ ] **Telegram Mini Apps (Web Apps)**: Research the feasibility of upgrading the "New Project" text-based FSM flow to a mobile-native Telegram Mini App to streamline the user experience and reduce form abandonment.

## Backlog (Can wait but should do)
- [x] **Observability & Admin Dashboard**: Implement a secure web dashboard (e.g., using FastAPI) alongside the bot to visually chart project volume, conversion rates, and revenue over time.
- [x] **Audit Trail (Business Events)**: Implement the MongoDB audit log feature according to `audit_trail_plan.md` to track state changes professionally. Remove the plan file once complete.

*(Note: AI-powered project triage and automated CI/CD pipelines were reviewed and explicitly skipped).*
