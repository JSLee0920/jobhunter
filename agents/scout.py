from google.adk.agents import LlmAgent


def get_scout(model, mcp_tool):
    return LlmAgent(
        name="ScoutAgent",
        model=model,
        instruction="""
        You are the Market Scout. Take the {skill_matrix} from the Profiler.
        Using the provided 'target_role' and 'target_location' from the context, 
        call the 'search_job' tool to find a matching position.
        IMPORTANT: Return ONLY the raw JSON output from the tool. DO NOT format it as markdown or add any text. Just pass through the exact JSON string returned by the tool.
        """,
        tools=[mcp_tool],
        output_key="job_match",
    )
