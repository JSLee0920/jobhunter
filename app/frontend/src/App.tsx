import React, { useState } from "react";
import axios, { AxiosError } from "axios";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface Job {
  title: string;
  company: string;
  location: string;
  description: string;
}

interface GenerateResponse {
  cover_letter: string;
}

interface ErrorDetail {
  detail: string;
}

function App() {
  const [role, setRole] = useState<string>("");
  const [location, setLocation] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [coverLetter, setCoverLetter] = useState<string>("");
  const [isError, setIsError] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>("");

  const handleSearch = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!file) {
      setErrorMessage("Please upload a PDF resume to continue.");
      setIsError(true);
      return;
    }
    if (file.type !== "application/pdf") {
      setErrorMessage("Invalid file format. Only PDF files are accepted.");
      setIsError(true);
      return;
    }

    setLoading(true);
    setJobs([]);
    setSelectedJob(null);
    setCoverLetter("");
    setIsError(false);
    setErrorMessage("");

    const formData = new FormData();
    formData.append("target_role", role);
    formData.append("target_location", location || "Malaysia");
    formData.append("resume", file);

    try {
      const res = await axios.post<Job[]>(`${API_URL}/api/search`, formData);
      setJobs(res.data);
    } catch (err) {
      const axiosError = err as AxiosError<ErrorDetail>;
      const serverMessage = axiosError.response?.data?.detail;
      setErrorMessage(serverMessage || axiosError.message);
      setIsError(true);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (job: Job) => {
    if (!file) return;

    setSelectedJob(job);
    setLoading(true);
    setCoverLetter("");
    setIsError(false);
    setErrorMessage("");

    const formData = new FormData();
    formData.append("resume", file);
    formData.append("selected_job", JSON.stringify(job));

    try {
      const res = await axios.post<GenerateResponse>(`${API_URL}/api/generate`, formData);
      setCoverLetter(res.data.cover_letter);
    } catch (err) {
      const axiosError = err as AxiosError<ErrorDetail>;
      const serverMessage = axiosError.response?.data?.detail;
      setErrorMessage(serverMessage || axiosError.message);
      setIsError(true);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <span className="logo-text">Job Hunter</span>
        </div>
      </header>

      <main className="main">
        <section className="hero">
          <h1 className="hero-title">Find Your Dream Job</h1>
          <p className="hero-subtitle">Upload your resume, discover matching opportunities, and get personalized cover letters instantly.</p>
        </section>

        <div className="form-wrapper">
          <form onSubmit={handleSearch} className="search-form">
            <div className="input-group">
              <label className="input-label">Target Role</label>
              <input
                type="text"
                placeholder="e.g., Full Stack Developer"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                required
                className="input-field"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Location</label>
              <input
                type="text"
                placeholder="e.g., Kuala Lumpur or Remote"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="input-field"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Resume (PDF)</label>
              <div className={`file-upload ${file ? "uploaded" : ""}`}>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={handleFileChange}
                  required
                  id="resume-upload"
                  className="file-input"
                />
                <label htmlFor="resume-upload" className="file-label">
                  <svg className="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" />
                  </svg>
                  <span className="file-text">{file ? file.name : "Drop your resume or click to browse"}</span>
                </label>
              </div>
            </div>

            <button type="submit" disabled={loading} className={`submit-btn ${loading ? "loading" : ""}`}>
              {loading && !selectedJob ? (
                <>
                  <span className="spinner"></span>
                  <span>Searching...</span>
                </>
              ) : (
                "Find Matching Jobs"
              )}
            </button>
          </form>
        </div>

        {isError && (
          <div className="alert error">
            <svg className="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <span>{errorMessage}</span>
          </div>
        )}

        {jobs.length > 0 && !coverLetter && (
          <section className="jobs-section">
            <h2 className="section-title">
              <span className="section-badge">{jobs.length}</span>
              Matching Jobs Found
            </h2>
            <div className="jobs-grid">
              {jobs.map((job, index) => (
                <div
                  key={index}
                  className={`job-card ${selectedJob === job ? "selected" : ""}`}
                  onClick={() => !loading && handleGenerate(job)}
                >
                  <div className="job-header">
                    <h3 className="job-title">{job.title}</h3>
                    <div className="job-meta">
                      <span className="job-company">{job.company}</span>
                      <span className="job-location">
                        <svg className="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                          <circle cx="12" cy="10" r="3"/>
                        </svg>
                        {job.location}
                      </span>
                    </div>
                  </div>
                  <p className="job-description">{job.description.substring(0, 180)}...</p>
                  <button className="generate-btn">
                    {loading && selectedJob === job ? (
                      <>
                        <span className="spinner-sm"></span>
                        <span>Generating...</span>
                      </>
                    ) : (
                      "Generate Cover Letter"
                    )}
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

        {coverLetter && (
          <section className="result-section">
            <h2 className="section-title">Your Cover Letter</h2>
            <div className="cover-letter-card">
              <div className="cover-letter-content">
                {coverLetter}
              </div>
            </div>
            <div className="result-actions">
              <button onClick={() => setCoverLetter("")} className="back-btn">
                <svg className="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="19" y1="12" x2="5" y2="12"/>
                  <polyline points="12 19 5 12 12 5"/>
                </svg>
                Back to Jobs
              </button>
              <button onClick={() => navigator.clipboard.writeText(coverLetter)} className="copy-btn">
                <svg className="icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
                Copy to Clipboard
              </button>
            </div>
          </section>
        )}
      </main>

      <footer className="footer">
        <p>Powered by AI | Job Hunter</p>
      </footer>
    </div>
  );
}

export default App;
