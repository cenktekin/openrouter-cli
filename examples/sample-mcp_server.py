import asyncio
import json
import logging
import uuid
from datetime import datetime
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from sse_starlette.sse import EventSourceResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# Create FastAPI app
app = FastAPI(title="Simple MCP Server")

# Store active connections
connections = {}

# Define available tools
tools = [
    {
        "name": "echo",
        "description": "Echoes back the input text",
        "input_schema": {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to echo"
                }
            }
        }
    },
    {
        "name": "fetch",
        "description": "Fetches content from a URL",
        "input_schema": {
            "type": "object",
            "required": ["url"],
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to fetch"
                }
            }
        }
    }
]

@app.get("/sse")
async def sse(request: Request):
    """SSE endpoint for client connections"""
    session_id = str(uuid.uuid4())
    logger.info(f"New SSE connection: {session_id}")

    # Create event queue for this connection
    queue = asyncio.Queue()
    connections[session_id] = queue

    # Send initial connection message with session ID
    await queue.put({
        "event": "connection",
        "id": str(uuid.uuid4()),
        "data": json.dumps({
            "status": "connected",
            "session_id": session_id,
            "message": "Connection established"
        })
    })

    # Send tools list
    await queue.put({
        "event": "tools",
        "id": str(uuid.uuid4()),
        "data": json.dumps({
            "tools": tools
        })
    })

    async def event_generator():
        try:
            while True:
                # Wait for message from queue
                message = await queue.get()

                if message.get("event") == "close":
                    break

                yield message

                # Small delay to avoid CPU spinning
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        finally:
            # Clean up on disconnect
            if session_id in connections:
                del connections[session_id]
            logger.info(f"SSE connection closed: {session_id}")

    return EventSourceResponse(event_generator())

@app.post("/messages")
async def messages(request: Request):
    """Handle messages from clients"""
    try:
        # Parse request body
        data = await request.json()
        logger.info(f"Received message: {data}")

        # Check for session_id
        session_id = data.get("session_id")
        if not session_id:
            return JSONResponse({"error": "session_id is required"}, status_code=400)

        # Check if session exists
        if session_id not in connections:
            return JSONResponse({"error": "Invalid session_id"}, status_code=400)

        # Get queue for this session
        queue = connections[session_id]

        # Process request based on type
        req_type = data.get("type")
        if not req_type:
            return JSONResponse({"error": "type is required"}, status_code=400)

        # Handle list_tools request
        if req_type == "list_tools":
            return JSONResponse({"tools": tools})

        # Handle call_tool request
        elif req_type == "call_tool":
            tool_name = data.get("tool")
            arguments = data.get("arguments", {})

            if not tool_name:
                return JSONResponse({"error": "tool name is required"}, status_code=400)

            # Find the tool
            tool = next((t for t in tools if t["name"] == tool_name), None)
            if not tool:
                return JSONResponse({"error": f"Tool '{tool_name}' not found"}, status_code=404)

            # Execute the tool
            result = await execute_tool(tool_name, arguments)

            # Send event via SSE
            await queue.put({
                "event": "tool_result",
                "id": str(uuid.uuid4()),
                "data": json.dumps({
                    "tool": tool_name,
                    "result": result,
                    "request_id": data.get("request_id")
                })
            })

            # Return immediate response
            return JSONResponse({"result": result})

        # Unknown request type
        else:
            return JSONResponse({"error": f"Unknown request type: {req_type}"}, status_code=400)

    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

async def execute_tool(tool_name, args):
    """Execute a tool with the given arguments"""
    try:
        if tool_name == "echo":
            text = args.get("text", "")
            return {
                "status": "success",
                "text": text,
                "echo": text
            }

        elif tool_name == "fetch":
            url = args.get("url")
            if not url:
                return {"error": "url is required"}

            return {
                "status": "success",
                "url": url,
                "content": f"Content fetched from {url} at {datetime.now().isoformat()}"
            }

        else:
            return {"error": f"Tool '{tool_name}' not implemented"}

    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    print("Starting MCP server at http://localhost:8000/sse")
    uvicorn.run(app, host="0.0.0.0", port=8000)
