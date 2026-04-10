# Antigravity Skills & Workflows for SVU Helper

Based on the `svu_helper` project stack (**Python, Aiogram, Telethon, Motor/MongoDB, Pytest, Pydantic, Sentry**) and the current Clean Architecture implementation, this guide curates the most impactful skills from the `antigravity-awesome-skills` library and how to use them.

## 1. Telegram Bot & Framework Mastery
Because you are building an advanced bot using `aiogram` and test with `telethon`:
*   **`telegram-bot-builder` & `telegram`** 
    *   **Use Case:** Invoke these skills when adding complex Telegram UI/UX flows (like Reply Keyboards), handling Deep Links, preventing command leakage in your Finite State Machine (FSM), or dealing with rate-limiting and Telegram API quotas.
*   **`pydantic-models-py`**
    *   **Use Case:** Use this for defining strict schemas when validating incoming user data from Telegram or safely loading environment settings via `pydantic-settings`.

## 2. Architecture & Code Quality
The project follows a Clean Architecture pattern.
*   **`clean-architecture`**
    *   **Use Case:** Call this skill whenever you are adding a new feature. It ensures that new files correctly split Domain models, Application use cases (business logic), and Infrastructure concerns without violating dependency rules.
*   **`python-pro`**
    *   **Use Case:** Use this for advanced `asyncio` patterns. Since both `aiogram` and `motor` are heavily asynchronous, this skill helps prevent event-loop blocking and ensures optimal performance.

## 3. Database Operations
The project uses `motor` for asynchronous MongoDB operations.
*   **`nosql-expert` & `database`**
    *   **Use Case:** Use these when creating complex MongoDB aggregation pipelines for admin statistics, managing collections/indexes, or ensuring proper data cleanup scripts during tests.

## 4. Advanced Testing Workflows
The project invests in unit and Telethon-based E2E tests.
*   **`e2e-testing` & `python-testing-patterns`**
    *   **Use Case:** Ideal for maintaining and expanding `telethon` automated flows. These skills provide patterns for dealing with asynchronous E2E flakiness, race conditions, and correctly mocking states.
*   **`tdd-workflow`** (Test-Driven Development)
    *   **Use Case:** Use this for new features to follow a Red-Green-Refactor cycle, writing failing tests for repositories before implementing logic.

## 5. Debugging & Observability
*   **`systematic-debugging`**
    *   **Use Case:** When an E2E test fails or a regression occurs, use this skill to systematically isolate the problem (e.g., state management or unacknowledged updates).
*   **`sentry-automation` & `observability-engineer`**
    *   **Use Case:** Use these to build proper error middleware so admins are alerted immediately whenever an unexpected exception occurs.

## 6. DevOps & Version Control
*   **`github` & `pr-writer`**
    *   **Use Case:** After finishing a work phase, use these to audit commit history, generate professional Conventional Commits, and open clean pull requests.

---

## How to use them
If you want to apply any of these skills in a conversation, you can instruct the assistant like this:
> *"Use the `clean-architecture` and `python-testing-patterns` skills to help me create a new repository method for fetching student stats."*

> [!NOTE]
> These skills are accessible on-demand even if they are not pre-loaded in the initial AI context.
