from google.adk.agents import LlmAgent


def get_compliance(model):
    return LlmAgent(
        name="ComplianceOfficer",
        model=model,
        instruction="""
        You are a strict Output Guardrail. Audit the {draft_letter} against the {skill_matrix}.
        
        RULES:
        1. HALLUCINATION CHECK: If a skill is in the letter but NOT in the {skill_matrix}, remove it.
        2. PII REDACTION: Redact generated phone numbers or addresses with [REDACTED].
        
        Output ONLY the finalized cover letter. If you altered the text, prepend the output with:
        "[Guardrail Alert: Hallucinated skills removed for safety]"
        """,
        output_key="final_cover_letter",
    )
