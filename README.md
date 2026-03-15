# Job Hunter

An AI-powered job search application that matches your resume with job listings and generates personalized cover letters using Google's Agent Development Kit (ADK) and Gemini.

## Features

- **Resume Parsing**: Upload your PDF resume and extract relevant skills and experience
- **Job Matching**: AI-powered job search based on your profile and preferences
- **Cover Letter Generation**: Automatically generates tailored cover letters for selected jobs
- **Multi-Agent Pipeline**: Uses sequential agents for profiling, scouting, diplomacy, and compliance

## Architecture

The application consists of:

- **Backend**: FastAPI server with ADK-powered agent pipeline
- **Frontend**: React + TypeScript + Vite application
- **Agents**:
  - **Profiler**: Extracts skills and experience from resume
  - **Scout**: Searches for matching jobs using MCP tools
  - **Diplomat**: Generates cover letters based on profile and job
  - **Compliance**: Ensures cover letter accuracy and safety

## Prerequisites

- Python 3.13+
- Node.js 18+
- uv package manager
- RapidAPI key for job search API

## Environment Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd gemini-nexus-hackathon
   ```

2. Create a `.env` file in the root directory:
   ```
   RAPIDAPI_KEY=your_rapidapi_key
   ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
   ```

## Backend Setup

1. Install Python dependencies:
   ```bash
   uv sync
   ```

2. Activate the virtual environment:
   ```bash
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. Run the FastAPI server:
   ```bash
   uv run main.py
   ```

   Or using uvicorn:
   ```bash
   uv run uvicorn main:app --reload --port 8000
   ```

## Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd app/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file in `app/frontend`:
   ```
   VITE_API_URL=http://localhost:8000
   ```

4. Run the development server:
   ```bash
   npm run dev
   ```

5. Open your browser at `http://localhost:5173`

## API Endpoints

### `POST /api/search`

Search for jobs matching your profile.

**Request (multipart/form-data)**:
- `target_role`: Target job role (e.g., "Full Stack Developer")
- `target_location`: Job location preference (e.g., "Remote", "Kuala Lumpur")
- `resume`: PDF resume file

**Response**: Array of job objects containing title, company, location, and description

### `POST /api/generate`

Generate a cover letter for a selected job.

**Request (multipart/form-data)**:
- `resume`: PDF resume file
- `selected_job`: JSON string of the selected job object

**Response**: Cover letter object with `cover_letter` field

## Tech Stack

### Backend
- FastAPI
- Google ADK (Agent Development Kit)
- Google Gemini 2.5 Flash
- MCP (Model Context Protocol)
- PyPDF2

### Frontend
- React
- TypeScript
- Vite
- Axios

## Project Structure

```
gemini-nexus-hackathon/
├── agents/
│   ├── profiler.py      # Resume profiling agent
│   ├── scout.py         # Job search agent
│   ├── diplomat.py      # Cover letter generation agent
│   └── compliance.py    # Safety/compliance agent
├── tools/
│   └── job_mcp_server.py  # MCP server for job search
├── app/frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   └── main.tsx
│   └── package.json
├── main.py              # FastAPI application entry point
├── pyproject.toml
├── .env.example
└── README.md
```

## License

MIT