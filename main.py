import hashlib
import json
import os
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI(title="Exam MCP Server")

EMAIL = "23f2005137@ds.study.iitm.ac.in"
PROTOCOL_VERSION = "2025-03-26"


def rpc_result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def rpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


@app.get("/")
async def health():
    return {"status": "ok", "mcp_endpoint": "/mcp"}


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
            status_code=400,
        )

    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
        return JSONResponse(
            {"jsonrpc": "2.0", "id": body.get("id") if isinstance(body, dict) else None,
             "error": {"code": -32600, "message": "Invalid Request"}},
            status_code=400,
        )

    method = body.get("method")
    request_id = body.get("id")
    params = body.get("params") or {}

    # Notifications have no id and must not receive a JSON-RPC response.
    if method == "notifications/initialized" and "id" not in body:
        return Response(status_code=202)

    if method == "initialize":
        requested_version = params.get("protocolVersion", PROTOCOL_VERSION)
        # Use the version requested by the client; this minimal stateless endpoint
        # implements the core initialize/tools/list/tools/call JSON-RPC exchange.
        return JSONResponse(rpc_result(request_id, {
            "protocolVersion": requested_version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "exam-challenge-mcp", "version": "1.0.0"},
            "instructions": "Call solve_challenge; the challenge is supplied in HTTP headers.",
        }))

    if method == "ping":
        return JSONResponse(rpc_result(request_id, {}))

    if method == "tools/list":
        return JSONResponse(rpc_result(request_id, {
            "tools": [{
                "name": "solve_challenge",
                "description": "Return the challenge-specific SHA-256 response using the registered exam email.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            }]
        }))

    if method == "tools/call":
        tool_name = params.get("name")
        if tool_name != "solve_challenge":
            return JSONResponse(rpc_error(request_id, -32602, "Unknown tool"))
        challenge = request.headers.get("X-Exam-Challenge")
        if challenge is None:
            return JSONResponse(rpc_error(request_id, -32602, "Missing X-Exam-Challenge header"))
        normalized_email = EMAIL.strip().lower()
        text = hashlib.sha256(f"{challenge}:{normalized_email}".encode("utf-8")).hexdigest()[:16]
        return JSONResponse(rpc_result(request_id, {
            "content": [{"type": "text", "text": text}],
            "isError": False,
        }))

    if method == "resources/list":
        return JSONResponse(rpc_result(request_id, {"resources": []}))

    if method == "prompts/list":
        return JSONResponse(rpc_result(request_id, {"prompts": []}))

    if "id" not in body:
        return Response(status_code=202)

    return JSONResponse(rpc_error(request_id, -32601, f"Method not found: {method}"))


# Some clients probe the endpoint with GET as part of Streamable HTTP discovery.
@app.get("/mcp")
async def mcp_get():
    return Response(
        content="MCP endpoint ready. Send JSON-RPC requests using POST.",
        media_type="text/plain",
        status_code=200,
    )
