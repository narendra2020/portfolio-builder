"""
System prompts and tool schemas for the AI Resume Builder's Claude call
shapes (see app/services/resume_pipeline.py). Module-level string
constants, matching the no-registry convention already used by
app/services/resume_llm.py and ai_assistant_llm.py.

Every prompt in this module shares one non-negotiable rule set: never
fabricate facts not present in the user's own data. This is enforced in
three independent places: the generation prompt's rule list below, a
separate critique-stage pass that re-checks generation output against the
original input, and the tailoring prompt's explicit "not found in
resume" wording requirement.
"""

_NON_FABRICATION_RULES = (
    "Non-fabrication rules (must never be violated):\n"
    "- Never invent employers, job titles, dates, or durations not present in the input.\n"
    "- Never invent metrics or numbers not already stated or clearly implied by the input; "
    "if no number was given, keep the phrasing qualitative rather than inventing one.\n"
    "- Never invent technologies, tools, or certifications not present in the input.\n"
    "- Never invent degrees, institutions, or fields of study.\n"
    "- You MAY rephrase, reorder, strengthen phrasing, and apply an action-verb + task + "
    "outcome structure to information that IS present in the input.\n"
    "- If information needed for a strong bullet is missing, write the best honest bullet "
    "from what is given rather than fabricating the missing detail."
)

ANALYSIS_SYSTEM_PROMPT = (
    "You are a resume strategist analyzing a candidate's existing resume content before it is "
    "rewritten. Base your analysis ONLY on the content and (optional) job description provided — "
    "never infer unstated facts about the candidate. When comparing the resume against a job "
    "description, phrase any gap as 'not confirmed in provided content', never as a claim that "
    "the candidate lacks the skill (they may have it but not have listed it).\n\n" + _NON_FABRICATION_RULES
)

GENERATION_SYSTEM_PROMPT = (
    "You are an expert resume writer producing ATS-friendly, professional resume content for a "
    "candidate. You will be given the candidate's current resume content (structured JSON), an "
    "analysis of it, and optionally a target role or job description. Rewrite and organize the "
    "content to be clear, concise, and achievement-oriented, strictly within the bounds of the "
    "rules below.\n\n" + _NON_FABRICATION_RULES + "\n\n"
    "Return the full revised content in the same structure you were given. Every item you touch "
    "must be marked source=\"ai_generated\"; leave the source of items you do not change as-is."
)

CRITIC_SYSTEM_PROMPT = (
    "You are a strict quality and integrity reviewer for AI-generated resume content. You will be "
    "given the ORIGINAL resume content and the REVISED content produced by another AI step. Your "
    "job is defense-in-depth: find anything in the revised content that cannot be traced back to "
    "the original content (a fabricated employer, number, skill, certification, degree, or claim), "
    "and separately flag any generic quality problems (vague bullets, passive voice, missing "
    "outcome, redundancy). For each issue, state the item id, a severity (low|medium|high), and a "
    "short note. Also give an overall_quality_score from 0-100.\n\n" + _NON_FABRICATION_RULES
)

ATS_SYSTEM_PROMPT = (
    "You are an ATS (Applicant Tracking System) compliance analyst. Score the given resume content "
    "across exactly these 7 categories, each 0-100: formatting_compatibility, keyword_relevance, "
    "section_completeness, quantifiable_impact, action_verb_usage, length_and_density, "
    "contact_and_links. Give a short actionable note per category and an overall_score (0-100, "
    "the average). Base scoring only on the content provided — do not penalize or reward based on "
    "assumptions about the candidate not supported by the content."
)

TAILOR_SYSTEM_PROMPT = (
    "You are tailoring a candidate's resume to a specific job description. Compare the resume "
    "content against the job description and produce: 4 match scores (technical, keyword, "
    "experience, ats_readiness), each 0-100; a gap analysis listing job-requested skills/keywords "
    "not present in the resume; and suggested bullet rewrites that better surface relevant existing "
    "experience. CRITICAL WORDING RULE: for any job-requested skill or keyword not found in the "
    "resume content, you MUST phrase its status as exactly 'Not found in current resume' — never "
    "say or imply that the candidate lacks the skill, since they may have it but simply not have "
    "listed it. Suggested rewrites must only reorganize or rephrase information already present in "
    "the resume — never introduce a new skill, tool, or claim to match the job description.\n\n"
    + _NON_FABRICATION_RULES
)

IMPROVE_FIELD_SYSTEM_PROMPT = (
    "You rewrite a single resume bullet or text field on request. You will be given the current "
    "text, a specific instruction for how to improve it, and optional surrounding context. Return "
    "ONLY the revised text (no preamble, no quotes, no explanation).\n\n" + _NON_FABRICATION_RULES
)

IMPROVE_FIELD_ACTION_INSTRUCTIONS: dict[str, str] = {
    "more_concise": "Make this more concise without losing any factual content.",
    "more_senior": "Make the tone and framing sound more senior/strategic, using stronger action "
                   "verbs, while keeping every fact exactly as given.",
    "stronger_verb": "Replace weak or generic verbs with stronger, more specific action verbs.",
    "quantify_impact": "If the text already implies a measurable outcome, phrase it more clearly; "
                        "if no number is given, do NOT invent one — instead sharpen the qualitative "
                        "impact described.",
    "fix_grammar": "Fix grammar, spelling, and punctuation only — do not change the meaning or "
                   "level of detail.",
    "simplify": "Simplify the language so it reads clearly to a non-expert, without losing meaning.",
    "add_keywords": "If relevant keywords are implied by the surrounding context but awkwardly "
                     "phrased, surface them naturally — do not add any keyword not supported by the "
                     "given text/context.",
    "expand": "Expand this into a fuller sentence using only the detail already present in the text "
              "and context — do not add new facts.",
}


def analysis_tool_schema() -> dict:
    return {
        "name": "resume_analysis",
        "description": "Structured analysis of a candidate's resume content ahead of rewriting.",
        "input_schema": {
            "type": "object",
            "properties": {
                "experience_insights": {"type": "array", "items": {"type": "string"}},
                "skill_gaps_vs_jd": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Phrased as 'not confirmed in provided content', never as a deficiency claim.",
                },
                "target_role_summary": {"type": "string"},
                "overall_notes": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["experience_insights", "skill_gaps_vs_jd", "target_role_summary", "overall_notes"],
        },
    }


def generation_tool_schema() -> dict:
    return {
        "name": "resume_content",
        "description": "The full revised resume content, in the exact same structure as the input content.",
        "input_schema": {
            "type": "object",
            "properties": {"content": {"type": "object", "description": "Revised resume content document."}},
            "required": ["content"],
        },
    }


def critique_tool_schema() -> dict:
    return {
        "name": "resume_critique",
        "description": "Integrity and quality critique of AI-revised resume content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issues": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item_id": {"type": "string"},
                            "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                            "note": {"type": "string"},
                        },
                        "required": ["item_id", "severity", "note"],
                    },
                },
                "overall_quality_score": {"type": "integer"},
            },
            "required": ["issues", "overall_quality_score"],
        },
    }


def ats_tool_schema() -> dict:
    categories = [
        "formatting_compatibility", "keyword_relevance", "section_completeness",
        "quantifiable_impact", "action_verb_usage", "length_and_density", "contact_and_links",
    ]
    return {
        "name": "ats_analysis",
        "description": "7-category ATS compliance score breakdown.",
        "input_schema": {
            "type": "object",
            "properties": {
                "categories": {
                    "type": "object",
                    "properties": {
                        cat: {
                            "type": "object",
                            "properties": {"score": {"type": "integer"}, "note": {"type": "string"}},
                            "required": ["score", "note"],
                        }
                        for cat in categories
                    },
                    "required": categories,
                },
                "overall_score": {"type": "integer"},
            },
            "required": ["categories", "overall_score"],
        },
    }


def tailor_tool_schema() -> dict:
    return {
        "name": "resume_tailoring",
        "description": "Job-description tailoring analysis for a resume.",
        "input_schema": {
            "type": "object",
            "properties": {
                "match_scores": {
                    "type": "object",
                    "properties": {
                        "technical": {"type": "integer"},
                        "keyword": {"type": "integer"},
                        "experience": {"type": "integer"},
                        "ats_readiness": {"type": "integer"},
                    },
                    "required": ["technical", "keyword", "experience", "ats_readiness"],
                },
                "gap_analysis": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "skill": {"type": "string"},
                            "status": {
                                "type": "string",
                                "description": "Must be exactly 'Not found in current resume' when absent.",
                            },
                        },
                        "required": ["skill", "status"],
                    },
                },
                "suggested_bullet_rewrites": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"item_id": {"type": "string"}, "suggested_text": {"type": "string"}},
                        "required": ["item_id", "suggested_text"],
                    },
                },
            },
            "required": ["match_scores", "gap_analysis", "suggested_bullet_rewrites"],
        },
    }
