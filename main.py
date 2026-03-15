import io
import json
import logging
import os
import uuid

import PyPDF2
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google.adk.agents import SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.genai import types
from mcp import StdioServerParameters

from agents.compliance import get_compliance
from agents.diplomat import get_diplomat
from agents.profiler import get_profiler
from agents.scout import get_scout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

allowed_origins = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.on_event("startup")
def validate_env():
    required_keys = ["RAPIDAPI_KEY"]
    missing = [k for k in required_keys if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {missing}")


llm_model = Gemini(model="gemini-2.5-flash")

job_mcp_tool = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=["run", "tools/job_mcp_server.py"],
        ),
        timeout=30.0,
    )
)

session_service = InMemorySessionService()


def repair_json_string(text: str) -> str:
    result = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            next_char = text[i + 1]
            if next_char in '"\\/bfnrtu':
                if next_char == "u":
                    if i + 5 < len(text) and all(
                        c in "0123456789abcdefABCDEF" for c in text[i + 2 : i + 6]
                    ):
                        result.append(text[i : i + 6])
                        i += 6
                    else:
                        result.append("\\\\u")
                        i += 2
                else:
                    result.append(text[i : i + 2])
                    i += 2
            else:
                result.append("\\\\")
                result.append(next_char)
                i += 2
        elif text[i] in "\n\r\t":
            result.append(" ")
            i += 1
        elif ord(text[i]) < 32:
            result.append(f"\\u{ord(text[i]):04x}")
            i += 1
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


def extract_json_from_response(response_str: str) -> list:
    text = response_str.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
    text = repair_json_string(text)
    outer = json.loads(text)
    if isinstance(outer, list):
        return outer
    if isinstance(outer, dict):
        if "search_job_response" in outer:
            resp = outer["search_job_response"]
            structured = resp.get("structuredContent", {})
            if structured.get("result"):
                result_text = repair_json_string(structured["result"])
                return json.loads(result_text)
            if resp.get("content") and len(resp["content"]) > 0:
                content_text = repair_json_string(resp["content"][0].get("text", "[]"))
                return json.loads(content_text)
            raise ValueError(
                "Unexpected response structure: missing result and content"
            )
        if "result" in outer:
            result = outer["result"]
            if isinstance(result, str):
                result = repair_json_string(result)
                return json.loads(result)
            return result
    raise ValueError("Unexpected response type")


async def parse_pdf(resume: UploadFile) -> str:
    if resume.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    try:
        pdf_bytes = await resume.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        resume_text = "".join((page.extract_text() or "") for page in pdf_reader.pages)

        if not resume_text.strip():
            raise ValueError(
                "PDF contains no readable text. Please upload a text-based PDF."
            )
        return resume_text
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF parsing failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")


@app.post("/api/search")
async def search_jobs(
    target_role: str = Form(...),
    target_location: str = Form(...),
    resume: UploadFile = File(...),
):
    resume_text = await parse_pdf(resume)
    session_id = str(uuid.uuid4())
    user_id = f"user_{str(uuid.uuid4())[:8]}"

    await session_service.create_session(
        app_name="JobHunter",
        user_id=user_id,
        session_id=session_id,
        state={
            "target_role": target_role,
            "target_location": target_location,
            "resume_text": resume_text,
        },
    )

    search_pipeline = SequentialAgent(
        name="SearchPipeline",
        sub_agents=[
            get_profiler(llm_model),
            get_scout(llm_model, job_mcp_tool),
        ],
    )

    runner = Runner(
        agent=search_pipeline, app_name="JobHunter", session_service=session_service
    )

    content = types.Content(
        role="user", parts=[types.Part.from_text(text="Find jobs.")]
    )

    jobs_json = None
    try:
        events = runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        )
        async for event in events:
            content_obj = getattr(event, "content", None)
            if content_obj:
                parts_list = getattr(content_obj, "parts", [])
                if parts_list and len(parts_list) > 0:
                    jobs_json = str(parts_list[0].text)

        if not jobs_json:
            raise HTTPException(status_code=500, detail="No jobs found.")
        try:
            jobs_data = extract_json_from_response(jobs_json)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to parse jobs JSON: {str(e)}"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse jobs: {str(e)} | Raw: {jobs_json[:500]}",
            )

        return jobs_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search Error: {str(e)}")


@app.post("/api/generate")
async def generate_cover_letter(
    resume: UploadFile = File(...),
    selected_job: str = Form(...),
):
    resume_text = await parse_pdf(resume)
    session_id = str(uuid.uuid4())
    user_id = f"user_{str(uuid.uuid4())[:8]}"

    await session_service.create_session(
        app_name="JobHunter",
        user_id=user_id,
        session_id=session_id,
        state={
            "resume_text": resume_text,
            "job_match": selected_job,  # Inject selected job as if Scout found it
        },
    )

    generate_pipeline = SequentialAgent(
        name="GeneratePipeline",
        sub_agents=[
            get_profiler(llm_model),
            get_diplomat(llm_model),
            get_compliance(llm_model),
        ],
    )

    runner = Runner(
        agent=generate_pipeline, app_name="JobHunter", session_service=session_service
    )

    content = types.Content(
        role="user", parts=[types.Part.from_text(text="Generate cover letter.")]
    )

    final_cover_letter = None
    try:
        events = runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        )
        async for event in events:
            content_obj = getattr(event, "content", None)
            if content_obj:
                parts_list = getattr(content_obj, "parts", [])
                if parts_list and len(parts_list) > 0:
                    final_cover_letter = str(parts_list[0].text)

        if not final_cover_letter:
            raise HTTPException(status_code=500, detail="Generation failed.")

        final_cover_letter = final_cover_letter.replace(
            "[Guardrail Alert: Hallucinated skills removed for safety]", ""
        ).strip()
        return {"cover_letter": final_cover_letter}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation Error: {str(e)}")
