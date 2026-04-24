"""
AI Date Parser
==============
Fallback date parser using the Google Gemini API.
When the standard regex-based parser fails (free-form text like "بكرا",
"tomorrow", "الاسبوع القادم"), this module sends the input to Gemini
to extract a normalised YYYY-MM-DD date string.
"""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

import structlog
from google import genai
from google.genai import types as genai_types

logger = structlog.get_logger(__name__)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DAMASCUS_TZ = ZoneInfo("Asia/Damascus")

# Model priority: primary → fallback on any error
_PRIMARY_MODEL = "gemini-3.1-flash-lite"
_FALLBACK_MODEL = "gemini-2.5-flash-lite"


def _build_prompt(user_input: str) -> str:
    """Build the Gemini prompt with current Damascus date/time injected."""
    now = datetime.now(_DAMASCUS_TZ)
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    current_day = now.strftime("%A")

    return (
        f"You are a strict date extraction assistant.\n"
        f"Current date: {current_date}\n"
        f"Current time: {current_time}\n"
        f"Current day of the week: {current_day}\n"
        f"Timezone: Asia/Damascus\n\n"
        f"The user typed: \"{user_input}\"\n\n"
        f"Your task:\n"
        f"1. Interpret the user input as a date. It may be in Arabic, English, "
        f"or any informal/conversational format (e.g. 'بكرا', 'الاسبوع القادم', "
        f"'tomorrow', 'next week', 'بعد يومين', etc.).\n"
        f"2. If you can determine a specific date, return ONLY the date in "
        f"YYYY-MM-DD format. Nothing else — no explanation, no extra text.\n"
        f"3. If the input is completely invalid, nonsensical, or too vague to "
        f"determine a specific date, return ONLY the string: INVALID_DATE\n\n"
        f"Examples:\n"
        f"- 'بكرا' → next day from current date\n"
        f"- 'الاسبوع القادم' → 7 days from current date\n"
        f"- 'بعد يومين' → 2 days from current date\n"
        f"- 'الخميس الجاي' → next Thursday from current date\n"
        f"- 'hello world' → INVALID_DATE\n\n"
        f"Respond with ONLY the YYYY-MM-DD date or INVALID_DATE:"
    )


async def parse_date_with_gemini(user_input: str, api_key: str) -> str | None:
    """Call Gemini to interpret free-form date text.

    Returns:
        A normalised YYYY-MM-DD string on success,
        or None if the input is invalid / the API call fails.
    """
    prompt = _build_prompt(user_input)

    for model_name in (_PRIMARY_MODEL, _FALLBACK_MODEL):
        try:
            client = genai.Client(api_key=api_key)
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=20,
                ),
            )

            result = response.text.strip()
            logger.info(
                "Gemini date parse response",
                model=model_name,
                user_input=user_input,
                raw_response=result,
            )

            if result == "INVALID_DATE":
                return None

            if _DATE_RE.match(result):
                return result

            # Response didn't match expected format
            logger.warning(
                "Gemini returned unexpected format",
                model=model_name,
                raw_response=result,
            )
            return None

        except Exception as exc:
            exc_type = type(exc).__name__

            if model_name == _PRIMARY_MODEL:
                # Any error from primary → fall back to secondary
                logger.warning(
                    "Primary model failed, falling back to secondary",
                    model=model_name,
                    fallback=_FALLBACK_MODEL,
                    error_type=exc_type,
                    error=str(exc),
                )
                continue  # try fallback model

            # Secondary model also failed — give up
            logger.error(
                "Gemini API call failed (both models)",
                model=model_name,
                error_type=exc_type,
                error=str(exc),
                user_input=user_input,
            )
            return None

    # Both models failed
    return None

