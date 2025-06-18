import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from tools.file_operations.mcp_client import MCPClient

@pytest.fixture
def mock_session():
    """Create a mock MCP session."""
    session = AsyncMock()
    session.initialize = AsyncMock()
    session.list_tools = AsyncMock()
    session.call_tool = AsyncMock()
    return session

@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client."""
    client = MagicMock()
    client.chat.completions.create = MagicMock()
    return client

@pytest.fixture
def mcp_client(mock_openai):
    """Create an MCP client instance with mocked dependencies."""
    with patch("openai.OpenAI", return_value=mock_openai):
        client = MCPClient(
            api_key="test_key",
            base_dir="/test/dir",
            model="test-model"
        )
        return client

@pytest.mark.asyncio
async def test_client_initialization(mcp_client):
    """Test MCP client initialization."""
    assert mcp_client.api_key == "test_key"
    assert str(mcp_client.base_dir) == "/test/dir"
    assert mcp_client.model == "test-model"
    assert mcp_client.max_retries == 3
    assert mcp_client.timeout == 30
    assert mcp_client.messages == []

@pytest.mark.asyncio
async def test_connect_to_server(mcp_client, mock_session):
    """Test connecting to MCP server."""
    mock_tools = [
        MagicMock(
            name="test_tool",
            description="Test tool",
            inputSchema={"properties": {}, "required": []}
        )
    ]
    mock_session.list_tools.return_value = MagicMock(tools=mock_tools)

    with patch("mcp.ClientSession", return_value=mock_session):
        server_config = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/test/dir"],
            "env": None
        }
        await mcp_client.connect_to_server(server_config)

        assert mcp_client.session == mock_session
        mock_session.initialize.assert_called_once()
        mock_session.list_tools.assert_called_once()

@pytest.mark.asyncio
async def test_connect_to_server_retry(mcp_client, mock_session):
    """Test server connection with retries."""
    mock_session.initialize.side_effect = [
        Exception("Connection failed"),
        Exception("Connection failed"),
        None  # Success on third try
    ]

    with patch("mcp.ClientSession", return_value=mock_session):
        server_config = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/test/dir"],
            "env": None
        }
        await mcp_client.connect_to_server(server_config)
        assert mock_session.initialize.call_count == 3

@pytest.mark.asyncio
async def test_connect_to_server_max_retries_exceeded(mcp_client, mock_session):
    """Test server connection with max retries exceeded."""
    mock_session.initialize.side_effect = Exception("Connection failed")

    with patch("mcp.ClientSession", return_value=mock_session):
        server_config = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/test/dir"],
            "env": None
        }
        with pytest.raises(Exception, match="Failed to connect to MCP server"):
            await mcp_client.connect_to_server(server_config)
        assert mock_session.initialize.call_count == mcp_client.max_retries

@pytest.mark.asyncio
async def test_convert_tool_format(mcp_client):
    """Test converting MCP tool format to OpenAI format."""
    mock_tool = MagicMock(
        name="test_tool",
        description="Test tool",
        inputSchema={
            "properties": {"param1": {"type": "string"}},
            "required": ["param1"]
        }
    )

    result = mcp_client.convert_tool_format(mock_tool)

    assert result["type"] == "function"
    assert result["function"]["name"] == "test_tool"
    assert result["function"]["description"] == "Test tool"
    assert "param1" in result["function"]["parameters"]["properties"]
    assert "param1" in result["function"]["parameters"]["required"]

@pytest.mark.asyncio
async def test_process_query(mcp_client, mock_session):
    """Test processing a query with tool calls."""
    # Mock tool response
    mock_tool = MagicMock(
        name="test_tool",
        description="Test tool",
        inputSchema={"properties": {}, "required": []}
    )
    mock_session.list_tools.return_value = MagicMock(tools=[mock_tool])

    # Mock OpenAI response with tool call
    mock_message = MagicMock()
    mock_message.tool_calls = [
        MagicMock(
            id="call_123",
            function=MagicMock(
                name="test_tool",
                arguments=json.dumps({"param": "value"})
            )
        )
    ]
    mock_message.content = "Test response"

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mcp_client.openai.chat.completions.create.return_value = MagicMock(
        choices=[mock_choice]
    )

    # Mock tool call result
    mock_session.call_tool.return_value = MagicMock(content="Tool result")

    with patch("mcp.ClientSession", return_value=mock_session):
        result = await mcp_client.process_query("Test query")

        assert "[Calling tool test_tool with args {'param': 'value'}]" in result
        assert "Tool result" in result
        assert "Test response" in result

@pytest.mark.asyncio
async def test_process_query_timeout(mcp_client, mock_session):
    """Test query processing with timeout."""
    mcp_client.openai.chat.completions.create.side_effect = asyncio.TimeoutError()

    with pytest.raises(asyncio.TimeoutError):
        await mcp_client.process_query("Test query")

@pytest.mark.asyncio
async def test_process_query_multiple_tool_calls(mcp_client, mock_session):
    """Test processing query with multiple tool calls."""
    mock_tools = [
        MagicMock(
            name="tool1",
            description="First tool",
            inputSchema={"properties": {}, "required": []}
        ),
        MagicMock(
            name="tool2",
            description="Second tool",
            inputSchema={"properties": {}, "required": []}
        )
    ]
    mock_session.list_tools.return_value = MagicMock(tools=mock_tools)

    mock_message = MagicMock()
    mock_message.tool_calls = [
        MagicMock(
            id="call_1",
            function=MagicMock(
                name="tool1",
                arguments=json.dumps({"param1": "value1"})
            )
        ),
        MagicMock(
            id="call_2",
            function=MagicMock(
                name="tool2",
                arguments=json.dumps({"param2": "value2"})
            )
        )
    ]
    mock_message.content = "Test response"

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mcp_client.openai.chat.completions.create.return_value = MagicMock(
        choices=[mock_choice]
    )

    mock_session.call_tool.side_effect = [
        MagicMock(content="Tool 1 result"),
        MagicMock(content="Tool 2 result")
    ]

    with patch("mcp.ClientSession", return_value=mock_session):
        result = await mcp_client.process_query("Test query")

        assert "[Calling tool tool1 with args {'param1': 'value1'}]" in result
        assert "[Calling tool tool2 with args {'param2': 'value2'}]" in result
        assert "Tool 1 result" in result
        assert "Tool 2 result" in result

@pytest.mark.asyncio
async def test_process_query_tool_error(mcp_client, mock_session):
    """Test handling tool execution errors."""
    mock_tool = MagicMock(
        name="error_tool",
        description="Tool that raises error",
        inputSchema={"properties": {}, "required": []}
    )
    mock_session.list_tools.return_value = MagicMock(tools=[mock_tool])

    mock_message = MagicMock()
    mock_message.tool_calls = [
        MagicMock(
            id="call_1",
            function=MagicMock(
                name="error_tool",
                arguments=json.dumps({"param": "value"})
            )
        )
    ]
    mock_message.content = "Test response"

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mcp_client.openai.chat.completions.create.return_value = MagicMock(
        choices=[mock_choice]
    )

    mock_session.call_tool.side_effect = Exception("Tool execution failed")

    with patch("mcp.ClientSession", return_value=mock_session):
        result = await mcp_client.process_query("Test query")

        assert "[Calling tool error_tool with args {'param': 'value'}]" in result
        assert "Error calling tool error_tool" in result

@pytest.mark.asyncio
async def test_process_query_invalid_tool_args(mcp_client, mock_session):
    """Test handling invalid tool arguments."""
    mock_tool = MagicMock(
        name="test_tool",
        description="Test tool",
        inputSchema={"properties": {}, "required": []}
    )
    mock_session.list_tools.return_value = MagicMock(tools=[mock_tool])

    mock_message = MagicMock()
    mock_message.tool_calls = [
        MagicMock(
            id="call_1",
            function=MagicMock(
                name="test_tool",
                arguments="invalid json"
            )
        )
    ]
    mock_message.content = "Test response"

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mcp_client.openai.chat.completions.create.return_value = MagicMock(
        choices=[mock_choice]
    )

    with patch("mcp.ClientSession", return_value=mock_session):
        with pytest.raises(json.JSONDecodeError):
            await mcp_client.process_query("Test query")

@pytest.mark.asyncio
async def test_handle_tool_calls(mcp_client, mock_session):
    """Test handling tool calls."""
    mock_message = MagicMock()
    mock_message.tool_calls = [
        MagicMock(
            id="call_123",
            function=MagicMock(
                name="test_tool",
                arguments=json.dumps({"param": "value"})
            )
        )
    ]

    mock_session.call_tool.return_value = MagicMock(content="Tool result")
    mcp_client.session = mock_session

    result = await mcp_client._handle_tool_calls(mock_message)

    assert "[Calling tool test_tool with args {'param': 'value'}]" in result
    assert "Tool result" in result

@pytest.mark.asyncio
async def test_cleanup(mcp_client):
    """Test cleanup of resources."""
    mock_exit_stack = AsyncMock()
    mcp_client.exit_stack = mock_exit_stack

    await mcp_client.cleanup()
    mock_exit_stack.aclose.assert_called_once()

@pytest.mark.asyncio
async def test_context_manager(mcp_client):
    """Test async context manager functionality."""
    async with mcp_client as client:
        assert client == mcp_client
