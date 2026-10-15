# Exam Challenge MCP Server

A minimal stateless MCP-over-HTTP endpoint implementing `initialize`, `notifications/initialized`, `tools/list`, and `tools/call`.

## Deploy to Render

1. Create a new public GitHub repository and upload these four files to the repository root.
2. In Render, choose **New → Blueprint** and connect that repository, or create a **New Web Service**.
3. For a Web Service, choose Python and use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Wait for the service to deploy. The MCP endpoint is `https://YOUR-SERVICE.onrender.com/mcp`.
5. Use the exact `/mcp` URL as the grader's MCP server URL.

## Contract

`solve_challenge` has no required input properties. Each `tools/call` reads `X-Exam-Challenge` from that HTTP request's headers and returns the first 16 lowercase hex characters of:

`SHA-256(challenge + ":" + "23f2005137@ds.study.iitm.ac.in")`

No challenge is cached, so every request uses its own header value.

## Local run

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Then send MCP JSON-RPC POST requests to `http://localhost:8000/mcp`.
