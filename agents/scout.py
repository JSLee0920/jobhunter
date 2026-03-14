from google.adk.agents import LlmAgent


def get_scout(model, mcp_tool):
    return LlmAgent(
        name="ScoutAgent",
        model=model,
        instruction="""
        You are the Market Scout. Take the {skill_matrix} from the Profiler.
        Call your JobHunter tool using the user's {target_role} and {target_location}.
        Return the exact job description, company name, and location from the tool's output.
        """,
        tools=[mcp_tool],
        output_key="job_match",
    )
