from google.adk.agents import LlmAgent


def get_profiler(model):
    return LlmAgent(
        name="ProfilerAgent",
        model=model,
        instruction="""
        You are the Context Profiler. Read the unstructured {resume_text}.
        Extract the core technical skills, frameworks, and desired roles.
        Format this strictly as a concise list called 'Skill Matrix'.
        """,
        output_key="skill_matrix",
    )
