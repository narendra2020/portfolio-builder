"""
Orchestrates the AI Resume Builder's Claude call shapes. Every structured
call goes through app.services.claude_client.call_with_tool (the same
shared client used by resume_llm.py and ai_assistant_llm.py — see that
module's docstring for the "do not introduce another LLM provider" intent).

Six call shapes:
  1. analyze_resume_inputs   - analysis ahead of rewriting
  2. generate_resume_content - rewrite content (non-fabrication contract)
  3. critique_resume         - independent integrity/quality re-check
  4. run_generation_pipeline - orchestrates 1-3 with one bounded retry
  5. analyze_ats             - 7-category ATS scorecard
  6. tailor_resume_to_job    - job-description gap analysis
  7. improve_bullet_text     - cheap single-field rewrite (shared by 8 actions)
"""
import json

from app.services.claude_client import ClaudeCallError, call_for_text
from app.services.claude_client import call_with_tool as _call_with_tool
from app.services import resume_prompts as prompts

CRITIQUE_SEVERITY_RETRY_THRESHOLD = "high"
MAX_GENERATION_RETRIES = 1


class ResumePipelineError(Exception):
    """Raised when a resume-builder Claude call fails or returns an unusable response."""


def _call(
    system: str, user_content: str, tool: dict, max_tokens: int = 4096,
    _required_override: list[str] | None = None,
) -> dict:
    try:
        result = _call_with_tool(system, user_content, tool, max_tokens=max_tokens)
    except ClaudeCallError as exc:
        raise ResumePipelineError(str(exc)) from exc

    required = (
        _required_override if _required_override is not None
        else tool.get("input_schema", {}).get("required", [])
    )
    missing = [key for key in required if key not in result]
    if missing:
        raise ResumePipelineError(
            f"Claude response for '{tool['name']}' is missing required field(s): {', '.join(missing)}."
        )
    return result


def analyze_resume_inputs(content: dict, target_role: str | None, job_description: str | None) -> dict:
    user_content = (
        f"Current resume content:\n{json.dumps(content)}\n\n"
        f"Target role: {target_role or '(not specified)'}\n\n"
        f"Job description (optional): {job_description or '(none provided)'}"
    )
    return _call(prompts.ANALYSIS_SYSTEM_PROMPT, user_content, prompts.analysis_tool_schema())


def generate_resume_content(
    content: dict, analysis: dict, target_role: str | None, job_description: str | None,
    critique_feedback: dict | None = None,
) -> dict:
    user_content = (
        f"Current resume content:\n{json.dumps(content)}\n\n"
        f"Analysis:\n{json.dumps(analysis)}\n\n"
        f"Target role: {target_role or '(not specified)'}\n\n"
        f"Job description (optional): {job_description or '(none provided)'}"
    )
    if critique_feedback:
        user_content += (
            f"\n\nA prior draft had these integrity/quality issues — fix them in this revision, "
            f"still never fabricating anything:\n{json.dumps(critique_feedback)}"
        )
    result = _call(prompts.GENERATION_SYSTEM_PROMPT, user_content, prompts.generation_tool_schema())
    return result.get("content", content)


def critique_resume(original_content: dict, revised_content: dict) -> dict:
    user_content = (
        f"Original resume content:\n{json.dumps(original_content)}\n\n"
        f"Revised resume content:\n{json.dumps(revised_content)}"
    )
    return _call(prompts.CRITIC_SYSTEM_PROMPT, user_content, prompts.critique_tool_schema())


def run_generation_pipeline(
    content: dict, target_role: str | None = None, job_description: str | None = None,
) -> dict:
    """
    Runs stages 1-3 with at most one bounded revision retry if the critic
    flags a high-severity issue. Returns
    {content, analysis, critique, retried: bool}.
    """
    analysis = analyze_resume_inputs(content, target_role, job_description)
    revised = generate_resume_content(content, analysis, target_role, job_description)
    critique = critique_resume(content, revised)
    retried = False

    has_high_severity = any(
        issue.get("severity") == CRITIQUE_SEVERITY_RETRY_THRESHOLD for issue in critique.get("issues", [])
    )
    if has_high_severity and MAX_GENERATION_RETRIES > 0:
        revised = generate_resume_content(
            content, analysis, target_role, job_description, critique_feedback=critique
        )
        critique = critique_resume(content, revised)
        retried = True

    return {"content": revised, "analysis": analysis, "critique": critique, "retried": retried}


def analyze_ats(content: dict) -> dict:
    user_content = f"Resume content:\n{json.dumps(content)}"
    tool = prompts.ats_tool_schema()
    # overall_score is specified as the average of the 7 category scores
    # (see ATS_SYSTEM_PROMPT) — if the model omits it, derive it rather
    # than failing the whole analysis over one missing-but-computable field.
    result = _call(prompts.ATS_SYSTEM_PROMPT, user_content, tool, _required_override=["categories"])
    categories = result.get("categories")
    if not isinstance(categories, dict):
        raise ResumePipelineError("Claude response for 'ats_analysis' had a malformed 'categories' field.")
    if "overall_score" not in result:
        scores = [cat.get("score", 0) for cat in categories.values() if isinstance(cat, dict)]
        result["overall_score"] = round(sum(scores) / len(scores)) if scores else 0
    return result


def tailor_resume_to_job(content: dict, job_description: str) -> dict:
    user_content = f"Resume content:\n{json.dumps(content)}\n\nJob description:\n{job_description}"
    return _call(prompts.TAILOR_SYSTEM_PROMPT, user_content, prompts.tailor_tool_schema(), max_tokens=4096)


def improve_bullet_text(current_text: str, action: str, context: str | None = None) -> str:
    instruction = prompts.IMPROVE_FIELD_ACTION_INSTRUCTIONS.get(
        action, "Improve this text while keeping every fact exactly as given."
    )
    user_content = (
        f"Instruction: {instruction}\n\n"
        f"Current text: {current_text}\n\n"
        f"Context (optional, for reference only — do not add facts from it unless already implied "
        f"by the current text): {context or '(none)'}"
    )
    try:
        return call_for_text(prompts.IMPROVE_FIELD_SYSTEM_PROMPT, user_content, max_tokens=300).strip()
    except ClaudeCallError as exc:
        raise ResumePipelineError(str(exc)) from exc
