"""
Sends extracted resume text to Claude (Anthropic Messages API) and asks
for structured pre-fill data: profile fields and per-section
questionnaire answers matching the shape of
AUDIENCE_QUESTIONNAIRE_SECTIONS (app/db/seed_data.py). Uses forced
tool-use so the response is guaranteed valid JSON — no free-text
parsing.
"""
import json

from app.services.claude_client import ClaudeCallError, call_with_tool

_TOOL_NAME = "extract_resume_data"

_SYSTEM_PROMPT = (
    "You are extracting structured data from a resume to pre-fill a portfolio "
    "website onboarding flow. Use only facts present in the resume text — never "
    "invent employers, dates, skills, or numbers that aren't there. If a field "
    "can't be determined, omit it. You are also asked to classify the resume's "
    "author into one of a given set of audience types based on evident signals: "
    "job titles and years of work history suggest a working professional; "
    "an in-progress degree, no/minimal work history, or academic coursework "
    "suggests a student; contract/consulting/'freelance' language or a list of "
    "varied clients suggests a freelancer; founder/co-founder/business-owner "
    "language suggests an entrepreneur; and a portfolio of creative/artistic "
    "work (design, writing, photography, content, art) suggests a creator. "
    "Pick the single best match; if genuinely ambiguous, prefer 'professional'."
)


class ResumeLLMError(Exception):
    """Raised when the Anthropic API call fails or returns an unusable response."""


def _tool_schema(section_questions: dict[str, list[dict]], audience_slugs: list[str]) -> dict:
    section_properties = {
        section_key: {
            "type": "object",
            "description": f"Answers for the '{section_key}' questionnaire section. Keys are question "
                           f"keys: {[q['key'] for q in questions]}. For 'repeater' type questions, the "
                           f"value is a list of objects matching that question's nested fields.",
        }
        for section_key, questions in section_questions.items()
    }
    return {
        "name": _TOOL_NAME,
        "description": "Structured resume extraction result for portfolio pre-fill.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "object",
                    "properties": {
                        "display_name": {"type": "string"},
                        "email": {"type": "string"},
                        "city": {"type": "string"},
                        "country": {"type": "string"},
                        "audience_slug": {
                            "type": "string",
                            "enum": audience_slugs,
                            "description": "Best-matching audience type for this resume's author.",
                        },
                    },
                },
                "answers": {
                    "type": "object",
                    "properties": section_properties,
                },
            },
            "required": ["profile", "answers"],
        },
    }


def suggest_from_resume(
    resume_text: str,
    section_questions: dict[str, list[dict]],
    audience_slugs: list[str],
) -> dict:
    """
    section_questions: {section_key: [question dict, ...]} — the target
    field contract (from the Professional-audience QuestionnaireSchema
    rows, which serve as the universal questionnaire shape).
    audience_slugs: active AudienceType slugs the resume can be classified into.
    """
    tool = _tool_schema(section_questions, audience_slugs)

    user_content = (
        f"Questionnaire question definitions by section: {json.dumps(section_questions)}\n\n"
        f"Audience types to classify into: {audience_slugs}\n\n"
        f"Resume text:\n{resume_text}"
    )

    try:
        return call_with_tool(_SYSTEM_PROMPT, user_content, tool, max_tokens=4096)
    except ClaudeCallError as exc:
        raise ResumeLLMError(str(exc)) from exc
