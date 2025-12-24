---
title: Automated Research Report Generation
emoji: 📝
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Automated Research and Report Generation System

An intelligent multi-agent system that autonomously conducts research and generates comprehensive reports on any topic using LangGraph, FastAPI, and LLMs.

## Features

- **Multi-Agent Research**: Creates specialized analyst personas based on your research topic
- **Autonomous Research**: Agents conduct web research using Tavily Search and Wikipedia
- **Human-in-the-Loop**: Provides feedback to refine analyst perspectives
- **Report Generation**: Exports professional reports in DOCX and PDF formats
- **User Authentication**: Secure login/signup system with session management
- **Real-time Progress**: Track report generation progress with visual feedback

## Required Secrets

Configure these in your Hugging Face Space Settings → Variables and secrets:

- `GOOGLE_API_KEY` - Google Gemini API key for LLM and embeddings
- `GROQ_API_KEY` - Groq API key for alternative LLM provider
- `TAVILY_API_KEY` - Tavily Search API key for web research
- `LLM_PROVIDER` - Set to "google" or "groq" (default: "google")

## How to Use

1. Visit the Space URL
2. Sign up for an account or log in
3. Enter your research topic in the dashboard
4. Wait for AI agents to conduct research (may take a few minutes)
5. Provide feedback to refine analysts if needed
6. Download generated report in DOCX or PDF format

## Technology Stack

- **Backend**: FastAPI + Uvicorn
- **AI Framework**: LangGraph for multi-agent orchestration
- **LLM Providers**: Google Gemini, Groq
- **Research Tools**: Tavily Search API, Wikipedia
- **Document Generation**: python-docx, ReportLab
- **Database**: SQLite (ephemeral in HF Spaces)
- **Authentication**: Session-based with bcrypt password hashing

## Limitations in Hugging Face Spaces

⚠️ **Data Persistence**: Generated reports and user accounts are reset when the Space restarts (SQLite is ephemeral).

⚠️ **Long-running Tasks**: Report generation may take 3-5 minutes depending on topic complexity.

## Architecture

The system uses a multi-agent workflow:
1. **Analyst Creation**: Generates specialized researcher personas
2. **Parallel Research**: Each analyst conducts independent research
3. **Expert Interviews**: Simulated interviews with domain experts
4. **Report Compilation**: Aggregates findings into structured report
5. **Document Export**: Formats and exports final report

## Local Development

For persistent data and full functionality, deploy locally:

```bash
# Clone repository
git clone <your-repo>
cd automated-research-report-generation

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_API_KEY="your-key"
export GROQ_API_KEY="your-key"
export TAVILY_API_KEY="your-key"

# Run application
uvicorn research_and_analyst.api.main:app --host 0.0.0.0 --port 8000
```

Visit http://localhost:8000

## License

[Your License]

## Support

For issues or questions, please open an issue on GitHub.
