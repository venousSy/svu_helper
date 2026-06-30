# Comprehensive E2E Testing Plan (5-Account Strategy)

This document outlines the master plan for testing the `svu_helper` bot's most complex edge cases, race conditions, and multi-user interactions. 

To execute these tests, the testing environment will require **5 distinct Telegram accounts**.

## 1. Prerequisites & Account Setup

Before these tests can be automated, you must acquire 5 separate Telegram accounts (phone numbers), log into `my.telegram.org` for each, and extract their `API_ID` and `API_HASH`.

The `.env` file for the test runner will need to be updated to support all 5 clients:

```env
# Admin Accounts
ADMIN1_TEST_API_ID=...
ADMIN1_TEST_API_HASH=...

ADMIN2_TEST_API_ID=...
ADMIN2_TEST_API_HASH=...

# Student Accounts
STUDENT1_TEST_API_ID=...
STUDENT1_TEST_API_HASH=...

STUDENT2_TEST_API_ID=...
STUDENT2_TEST_API_HASH=...

STUDENT3_TEST_API_ID=...
STUDENT3_TEST_API_HASH=...
```

### Roles Definition
*   **Admin 1 (Primary):** Processes standard admin flows.
*   **Admin 2 (Secondary):** Used exclusively to test admin-side race conditions.
*   **Student 1 (Host/Referrer):** Creates teams, sends out referrals.
*   **Student 2 (Applicant A/Referee A):** Joins teams, signs up under Student 1.
*   **Student 3 (Applicant B/Referee B):** Used to test contention (applying to full teams, cross-referrals).

---

## 2. Test Scenarios (Edge Cases)

### Scenario A: Matchmaking Contention (The "Full Team" Race Condition)
**Goal:** Ensure the system does not exceed team capacity when multiple users apply simultaneously.
1.  **Student 1** creates a new team, specifying they need exactly **1 more member**.
2.  **Student 2** and **Student 3** both search for the team and click "انضمام" (Join) at approximately the same time.
3.  **Student 1** receives two pending join requests.
4.  **Student 1** clicks "قبول" (Accept) on **Student 2**'s request.
5.  *Assertion 1:* The team state immediately changes to "Completed" (مكتمل).
6.  *Assertion 2:* **Student 3**'s request is automatically invalidated. If Student 1 tries to click Accept on Student 3's old message, the bot must reject the action (e.g., "عذراً، اكتمل الفريق").

### Scenario B: Cross-Team Interference
**Goal:** Prevent a student from holding spots in multiple teams.
1.  **Student 1** creates Team X.
2.  **Student 2** creates Team Y.
3.  **Student 3** applies to both Team X and Team Y.
4.  **Student 1** accepts **Student 3** into Team X.
5.  *Assertion 1:* **Student 3** is successfully added to Team X.
6.  *Assertion 2:* **Student 3**'s pending application to Team Y is automatically withdrawn/deleted from the database so **Student 2** doesn't accept a user who is already matched.

### Scenario C: Admin Race Conditions (Double Booking)
**Goal:** Prevent two admins from processing the same order or ticket simultaneously.
1.  **Student 1** submits a new Project Order (or Support Ticket).
2.  The bot broadcasts the "New Order" inline keyboard to both **Admin 1** and **Admin 2**.
3.  **Admin 1** clicks "إرسال عرض سعر" (Send Price Offer).
4.  Immediately after, **Admin 2** clicks the exact same button on their instance of the message.
5.  *Assertion 1:* **Admin 1** is successfully transitioned to the price-offer FSM state.
6.  *Assertion 2:* **Admin 2** receives a popup or message stating "تمت معالجة هذا الطلب من قبل أدمن آخر" (This request was already handled by another admin) and is NOT placed into the FSM state.

### Scenario D: Referral Fraud & Stacking Prevention
**Goal:** Ensure the referral logic handles multiple referees and blocks self/retroactive referrals.
1.  **Student 1** generates their referral link.
2.  **Student 2** starts the bot using Student 1's link and successfully registers.
3.  *Assertion 1:* **Student 1**'s referral count/credit increases.
4.  **Student 3** starts the bot using Student 1's link.
5.  *Assertion 2:* **Student 1**'s referral count increases again (stacking works).
6.  **Student 2** (already registered) attempts to click **Student 3**'s referral link.
7.  *Assertion 3:* The system detects **Student 2** is already registered and prevents any referral credit from being assigned to Student 3.

### Scenario E: Broadcast Reliability
**Goal:** Ensure system-wide broadcasts reach all intended admin targets without failing mid-loop.
1.  A system event triggers a broadcast (e.g., a new ticket).
2.  *Assertion 1:* Both **Admin 1** and **Admin 2** receive the exact same message payload within an acceptable time delta.

---

## 3. Implementation Notes
*   **Framework:** Use `telethon` (as currently used in `e2e_matchmaking_suite.py`).
*   **Orchestration:** The runner script will need to initialize `asyncio.gather` for race condition tests to ensure button clicks from multiple clients happen in the exact same event loop tick.
*   **Cleanup:** The suite must include a robust `teardown` phase to wipe the database states of these 5 users between runs so tests remain isolated.
