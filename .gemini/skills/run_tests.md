# Skill: Running Tests in the SVU Helper Project

This skill provides instructions for the agent (Antigravity) on how to correctly run tests in this environment.

## Context
- **No Local `.env` File**: The project is intentionally configured without a local `.env` file because it is deployed on **Railway**, where environment variables are managed securely.
- **Mocking**: During local development and testing, environment variables required by `config.py` (such as `BOT_TOKEN` and `MONGO_URI`) must be mocked to prevent validation errors.

## Instructions for Running Tests

1.  **Use `python -m pytest`**: Always use the modular run command to ensure the current directory is added to `sys.path`.
    ```bash
    python -m pytest
    ```

2.  **Rely on `tests/conftest.py`**: Do not attempt to create a `.env` file or look for real Railway variables locally. All necessary environment variables for testing are defined in `tests/conftest.py`.

3.  **Required Variables**: Ensure the following variables are always mocked if adding new tests:
    - `BOT_TOKEN`: A dummy string (e.g., `test_token`).
    - `ADMIN_IDS`: A comma-separated string of IDs.
    - `MONGO_URI`: A valid MongoDB URI (usually `mongodb://localhost:27017` for local mocks).

4.  **Database state**: Tests should ideally use a mocked database or a temporary local instance. Do not attempt to connect to the production Railway database during tests.

## Why this skill?
Following these instructions prevents `pydantic.ValidationError` when `config.py` initializes, and ensures that the local environment remains clean and decoupled from the Railway deployment.
