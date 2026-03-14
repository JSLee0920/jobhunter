import io
import uuid
import PyPDF2
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from google.adk.agents import SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import McpTool
from google.genai import types

from agents.profiler import get_profiler
from agents.scout import get_scout
from agents.diplomat import get_diplomat
from agents.compliance import get_compliance

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

llm_model = Gemini(model="gemini-2.5-flash")

job_mcp_tool = McpTool(
    name="JobBoardOrchestrator", command="uv", args=["run", "tools/job_mcp_server.py"]
)

career_swarm = SequentialAgent(
    name="CareerSyncPipeline",
    sub_agents=[
        get_profiler(llm_model),
        get_scout(llm_model, job_mcp_tool),
        get_diplomat(llm_model),
        get_compliance(llm_model),
    ],
)

session_service = InMemorySessionService()


@app.post("/api/swarm")
async def execute_swarm(
    target_role: str = Form(...),
    target_location: str = Form(...),
    resume: UploadFile = File(...),
):
    if resume.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    print(f"\n[System] Mission received. Target: {target_role} in {target_location}")

    try:
        pdf_bytes = await resume.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        # Protects against None returns from image-based PDFs
        resume_text = "".join((page.extract_text() or "") for page in pdf_reader.pages)

        if not resume_text.strip():
            raise ValueError(
                "PDF contains no readable text. Please upload a text-based PDF."
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")

    session_id = str(uuid.uuid4())
    user_id = f"user_{str(uuid.uuid4())[:8]}"

    runner = Runner(
        agent=career_swarm, app_name="CareerSync", session_service=session_service
    )

    print("[Profiler] Thinking: Extracting matrix from local PDF...")

    initial_input = f"target_role: {target_role} | target_location: {target_location} | resume_text: {resume_text}"
    content = types.Content(
        role="user", parts=[types.Part.from_text(text=initial_input)]
    )

    final_cover_letter = None

    try:
        events = runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        )

        async for event in events:
            if getattr(event, "is_final_response", lambda: False)():
                content_obj = getattr(event, "content", None)
                if content_obj:
                    parts_list = getattr(content_obj, "parts", [])
                    if parts_list and len(parts_list) > 0:
                        final_cover_letter = str(parts_list[0].text)
                break

        if not final_cover_letter:
            raise HTTPException(
                status_code=500,
                detail="Swarm executed but failed to generate a final response.",
            )

    except Exception as e:
        print(f"[System Error] {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Swarm Error: {str(e)}")

    print("[System] Swarm completed. Dispatching to UI.")
    return {"status": "success", "cover_letter": final_cover_letter}
