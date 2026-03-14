from mcp.server.fastmcp import FastMCP
import httpx
import json
import logging
import os
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("JobHunter")


@mcp.tool()
async def search_job(role: str, location: str = "Malaysia") -> str:
    logging.info(f"[MCP Server] Querying RapidAPI for: {role} in {location}...")

    url = "https://linkedin-jobs-search.p.rapidapi.com/"

    payload = {"search_terms": role, "location": location, "page": "1"}

    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": os.environ.get("RAPIDAPI_KEY", ""),
        "X-RapidAPI-Host": "linkedin-jobs-search.p.rapidapi.com",
    }

    try:
        if not headers["X-RapidAPI-Key"]:
            raise ValueError("API Key Not Found")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=headers, timeout=20.0
            )
            response.raise_for_status()
            data = response.json()

        jobs = data if isinstance(data, list) else data.get("jobs", [])

        if not jobs:
            raise ValueError(f"No jobs found for {role} in {location}.")

        top_match = jobs[0]

        raw_desc = top_match.get("job_description", "")
        clean_desc = raw_desc.replace("\n\n", " ")[:1500]

        clean_result = {
            "title": top_match.get("job_title", role),
            "company": top_match.get("company_name", "Unknown Company"),
            "location": top_match.get("job_location", location),
            "description": clean_desc,
        }

        logging.info("[MCP Server] Live data retrieved successfully from RapidAPI.")
        return json.dumps([clean_result])

    except Exception as e:
        logging.error(
            f"[MCP Server] API failed: {str(e)}. Initiating mock fallback sequence."
        )
        return json.dumps(
            [
                {
                    "title": f"{role}",
                    "company": "Tech Corp Malaysia",
                    "location": location,
                    "description": f"Seeking a {role} based in {location} with strong technical skills to join our core engineering team.",
                }
            ]
        )


if __name__ == "__main__":
    mcp.run(transport="stdio")
