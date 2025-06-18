import pytest
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from tools.file_operations.mcp_ops import MCPFileOperations

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path

@pytest.fixture
def mock_client():
    """Create a mock MCP client."""
    client = AsyncMock()
    client.process_query = AsyncMock(return_value="Test analysis")
    return client

@pytest.fixture
def mcp_ops(temp_dir, mock_client):
    """Create an MCP file operations instance with mocked dependencies."""
    with patch("tools.file_operations.mcp_ops.MCPClient", return_value=mock_client):
        ops = MCPFileOperations(
            base_dir=str(temp_dir),
            api_key="test_key",
            allowed_extensions=[".txt", ".md"],
            max_file_size=1024,
            cache_dir=str(temp_dir / ".cache")
        )
        ops._client = mock_client
        return ops

@pytest.mark.asyncio
async def test_initialization(mcp_ops, temp_dir):
    """Test MCP file operations initialization."""
    assert mcp_ops.api_key == "test_key"
    assert str(mcp_ops.base_dir) == str(temp_dir)
    assert mcp_ops.allowed_extensions == [".txt", ".md"]
    assert mcp_ops.max_file_size == 1024
    assert str(mcp_ops.cache_dir) == str(temp_dir / ".cache")
    assert mcp_ops.cache_ttl == 24 * 60 * 60

@pytest.mark.asyncio
async def test_client_property(mcp_ops, mock_client):
    """Test client property creation and caching."""
    # First call should create new client
    client = await mcp_ops.client
    assert client == mock_client

    # Second call should return cached client
    client2 = await mcp_ops.client
    assert client2 == mock_client
    assert client == client2

@pytest.mark.asyncio
async def test_analyze_file(mcp_ops, temp_dir):
    """Test file analysis with caching."""
    # Create test file
    test_file = temp_dir / "test.txt"
    test_file.write_text("Test content")

    # Test analysis
    result = await mcp_ops.analyze_file(
        test_file,
        "Test prompt",
        use_cache=True
    )

    assert result["file_path"] == str(test_file)
    assert result["analysis"] == "Test analysis"
    assert "timestamp" in result

    # Verify cache
    cache_file = mcp_ops.cache_dir / f"{test_file.name}.json"
    assert cache_file.exists()

    # Test cached result
    result2 = await mcp_ops.analyze_file(
        test_file,
        "Test prompt",
        use_cache=True
    )
    assert result2 == result

@pytest.mark.asyncio
async def test_analyze_file_validation(mcp_ops, temp_dir):
    """Test file analysis validation."""
    # Test non-existent file
    with pytest.raises(FileNotFoundError):
        await mcp_ops.analyze_file(
            temp_dir / "nonexistent.txt",
            "Test prompt"
        )

    # Test disallowed file type
    test_file = temp_dir / "test.py"
    test_file.write_text("Test content")
    with pytest.raises(ValueError):
        await mcp_ops.analyze_file(test_file, "Test prompt")

    # Test file too large
    test_file = temp_dir / "test.txt"
    test_file.write_text("x" * 2048)  # 2KB
    with pytest.raises(ValueError):
        await mcp_ops.analyze_file(test_file, "Test prompt")

@pytest.mark.asyncio
async def test_batch_analyze_files(mcp_ops, temp_dir):
    """Test batch file analysis."""
    # Create test files
    files = []
    for i in range(3):
        file = temp_dir / f"test{i}.txt"
        file.write_text(f"Test content {i}")
        files.append(file)

    # Test batch analysis
    results = await mcp_ops.batch_analyze_files(
        files,
        "Test prompt",
        use_cache=True
    )

    assert len(results) == 3
    for result in results:
        assert "file_path" in result
        assert "analysis" in result
        assert "timestamp" in result

@pytest.mark.asyncio
async def test_cache_management(mcp_ops, temp_dir):
    """Test cache management functions."""
    # Create test file and cache
    test_file = temp_dir / "test.txt"
    test_file.write_text("Test content")

    # Create cache entry
    cache_data = {
        "file_path": str(test_file),
        "analysis": "Test analysis",
        "timestamp": datetime.now().isoformat()
    }
    cache_file = mcp_ops.cache_dir / f"{test_file.name}.json"
    cache_file.write_text(json.dumps(cache_data))

    # Test cache retrieval
    result = mcp_ops._get_cached_result(test_file)
    assert result == cache_data

    # Test cache expiration
    expired_data = {
        "file_path": str(test_file),
        "analysis": "Test analysis",
        "timestamp": (datetime.now() - timedelta(days=2)).isoformat()
    }
    cache_file.write_text(json.dumps(expired_data))
    result = mcp_ops._get_cached_result(test_file)
    assert result is None

    # Test cache clearing
    await mcp_ops.clear_cache()
    assert not cache_file.exists()

    # Test specific file cache clearing
    cache_file.write_text(json.dumps(cache_data))
    await mcp_ops.clear_cache(test_file)
    assert not cache_file.exists()

@pytest.mark.asyncio
async def test_cleanup(mcp_ops, mock_client):
    """Test cleanup of resources."""
    await mcp_ops.cleanup()
    assert mcp_ops._client is None
    mock_client.cleanup.assert_called_once()

@pytest.mark.asyncio
async def test_context_manager(mcp_ops):
    """Test async context manager functionality."""
    async with mcp_ops as ops:
        assert ops == mcp_ops

@pytest.mark.asyncio
async def test_analyze_file_concurrent_access(mcp_ops, temp_dir):
    """Test concurrent access to file analysis."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Test content")

    async def analyze():
        return await mcp_ops.analyze_file(test_file, "Test prompt")

    # Run multiple analyses concurrently
    results = await asyncio.gather(*[analyze() for _ in range(5)])

    # All results should be identical
    assert all(r == results[0] for r in results)

    # Cache should exist
    cache_file = mcp_ops.cache_dir / f"{test_file.name}.json"
    assert cache_file.exists()

@pytest.mark.asyncio
async def test_analyze_file_custom_prompt(mcp_ops, temp_dir):
    """Test file analysis with custom prompt."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Test content")

    custom_prompt = "Analyze this file in detail and provide a summary."
    result = await mcp_ops.analyze_file(test_file, custom_prompt)

    assert result["file_path"] == str(test_file)
    assert "timestamp" in result
    mcp_ops._client.process_query.assert_called_once()

@pytest.mark.asyncio
async def test_batch_analyze_files_partial_failure(mcp_ops, temp_dir):
    """Test batch analysis with partial failures."""
    # Create test files
    files = []
    for i in range(3):
        file = temp_dir / f"test{i}.txt"
        file.write_text(f"Test content {i}")
        files.append(file)

    # Make one file too large
    files[1].write_text("x" * 2048)  # 2KB

    # Test batch analysis
    results = await mcp_ops.batch_analyze_files(files, "Test prompt")

    assert len(results) == 3
    assert "error" in results[1]
    assert "analysis" in results[0]
    assert "analysis" in results[2]

@pytest.mark.asyncio
async def test_batch_analyze_files_empty_list(mcp_ops):
    """Test batch analysis with empty file list."""
    results = await mcp_ops.batch_analyze_files([], "Test prompt")
    assert len(results) == 0

@pytest.mark.asyncio
async def test_cache_management_concurrent(mcp_ops, temp_dir):
    """Test concurrent cache operations."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Test content")

    # Create initial cache
    await mcp_ops.analyze_file(test_file, "Test prompt")

    async def clear_cache():
        await mcp_ops.clear_cache()

    async def analyze_file():
        return await mcp_ops.analyze_file(test_file, "Test prompt")

    # Run cache operations concurrently
    await asyncio.gather(
        clear_cache(),
        analyze_file(),
        analyze_file()
    )

    # Cache should be recreated
    cache_file = mcp_ops.cache_dir / f"{test_file.name}.json"
    assert cache_file.exists()

@pytest.mark.asyncio
async def test_cache_management_invalid_json(mcp_ops, temp_dir):
    """Test handling invalid JSON in cache."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Test content")

    # Create invalid cache file
    cache_file = mcp_ops.cache_dir / f"{test_file.name}.json"
    cache_file.write_text("invalid json")

    # Should handle invalid cache gracefully
    result = await mcp_ops.analyze_file(test_file, "Test prompt")
    assert result["file_path"] == str(test_file)
    assert "analysis" in result

@pytest.mark.asyncio
async def test_analyze_file_symlink(mcp_ops, temp_dir):
    """Test analysis of symlinked files."""
    # Create original file
    original_file = temp_dir / "original.txt"
    original_file.write_text("Original content")

    # Create symlink
    symlink_file = temp_dir / "symlink.txt"
    symlink_file.symlink_to(original_file)

    # Test analysis of symlink
    result = await mcp_ops.analyze_file(symlink_file, "Test prompt")
    assert result["file_path"] == str(symlink_file)
    assert "analysis" in result

@pytest.mark.asyncio
async def test_analyze_file_permission_error(mcp_ops, temp_dir):
    """Test handling permission errors."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Test content")

    # Make file read-only
    test_file.chmod(0o444)

    try:
        with pytest.raises(PermissionError):
            await mcp_ops.analyze_file(test_file, "Test prompt")
    finally:
        # Restore permissions
        test_file.chmod(0o644)

@pytest.mark.asyncio
async def test_analyze_file_unicode_content(mcp_ops, temp_dir):
    """Test analysis of files with Unicode content."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Test content with Unicode: 你好世界")

    result = await mcp_ops.analyze_file(test_file, "Test prompt")
    assert result["file_path"] == str(test_file)
    assert "analysis" in result
