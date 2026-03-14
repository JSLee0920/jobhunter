from google.adk.agents import LlmAgent


def get_scout(model, mcp_tool):
    return LlmAgent(
        name="ScoutAgent",
        model=model,
        instruction="""
        You are the Market Scout. Take the {skill_matrix} from the Profiler.
        Using the provided 'target_role' and 'target_location' from the context, 
        call the 'search_job' tool to find a matching position.
        Return the exact job description, company name, and location from the tool's output.
        """,
        tools=[mcp_tool],
        output_key="job_match",
    )
