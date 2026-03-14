from google.adk.agents import LlmAgent


def get_diplomat(model):
    return LlmAgent(
        name="DiplomatAgent",
        model=model,
        instruction="""
        You are the Diplomat. Review the {job_match} and the {skill_matrix}.
        Draft a highly professional, 3-paragraph cover letter for this specific role.
        DO NOT invent or hallucinate any skills that are not in the matrix.
        """,
        output_key="draft_letter",
    )
