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

    url = "https://jsearch.p.rapidapi.com/search"

    querystring = {"query": f"{role} in {location}", "page": "1", "num_pages": "1"}

    headers = {
        "X-RapidAPI-Key": os.environ.get("RAPIDAPI_KEY", ""),
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    try:
        if not headers["X-RapidAPI-Key"]:
            raise ValueError("API Key Not Found")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers=headers, params=querystring, timeout=20.0
            )
            response.raise_for_status()
            api_response = response.json()

        jobs = api_response.get("data", [])

        if not jobs:
            raise ValueError(f"No jobs found for {role} in {location}.")

        top_matches = []
        for job in jobs:
            desc = job.get("job_description", "")
            company = job.get("employer_name", "")

            if desc and len(desc) > 150 and not company.startswith("Org_"):
                raw_desc = desc
                clean_desc = raw_desc.replace("\n\n", " ")[:1500]
                top_matches.append(
                    {
                        "title": job.get("job_title", role),
                        "company": company,
                        "location": job.get("job_city", location),
                        "description": clean_desc,
                    }
                )
            if len(top_matches) >= 3:
                break

        if not top_matches and jobs:
            job = jobs[0]
            top_matches.append(
                {
                    "title": job.get("job_title", role),
                    "company": job.get("employer_name", "Unknown Company"),
                    "location": job.get("job_city", location),
                    "description": job.get("job_description", "")[:1500],
                }
            )

        logging.info("[MCP Server] Live data retrieved successfully from JSearch.")
        return json.dumps(top_matches)

    except httpx.TimeoutException:
        logging.error("[MCP Server] Request timed out")
        return json.dumps(
            [
                {
                    "title": "ERROR",
                    "company": "Timeout",
                    "location": "N/A",
                    "description": "Job search timed out. Please try again.",
                }
            ]
        )
    except httpx.HTTPStatusError as e:
        logging.error(f"[MCP Server] HTTP error: {e.response.status_code}")
        return json.dumps(
            [
                {
                    "title": "ERROR",
                    "company": "API Error",
                    "location": "N/A",
                    "description": f"Job search API returned error {e.response.status_code}. Please try again.",
                }
            ]
        )
    except Exception as e:
        error_msg = f"API Crash Reason: {str(e)}"
        logging.error(f"[MCP Server] {error_msg}")
        return json.dumps(
            [
                {
                    "title": "SYSTEM ERROR",
                    "company": "Debug Corp",
                    "location": "Backend",
                    "description": error_msg,
                }
            ]
        )


if __name__ == "__main__":
    mcp.run(transport="stdio")
