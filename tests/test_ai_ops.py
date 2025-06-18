"""
Unit tests for AI-powered file operations.
"""

import os
import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from tools.file_operations.ai_ops import AIPoweredFileOperations

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return str(tmp_path)

@pytest.fixture
def ai_ops(temp_dir):
    """Create an AIPoweredFileOperations instance for testing."""
    return AIPoweredFileOperations(
        base_dir=temp_dir,
        api_key="test_api_key",
        allowed_extensions=[".jpg", ".png", ".pdf"],
        max_file_size=1024 * 1024  # 1MB for testing
    )

@pytest.fixture
def sample_image(temp_dir):
    """Create a sample image file for testing."""
    image_path = os.path.join(temp_dir, "test.jpg")
    with open(image_path, "wb") as f:
        f.write(b"fake image data")
    return image_path

@pytest.fixture
def sample_pdf(temp_dir):
    """Create a sample PDF file for testing."""
    pdf_path = os.path.join(temp_dir, "test.pdf")
    with open(pdf_path, "wb") as f:
        f.write(b"fake pdf data")
    return pdf_path

def test_init(ai_ops, temp_dir):
    """Test initialization of AIPoweredFileOperations."""
    assert ai_ops.base_dir == temp_dir
    assert ai_ops.api_key == "test_api_key"
    assert ai_ops.max_file_size == 1024 * 1024
    assert ai_ops.allowed_extensions == [".jpg", ".png", ".pdf"]
    assert os.path.exists(ai_ops.cache_dir)
    assert ai_ops.model_config["image"] == "openai/gpt-4-vision-preview"
    assert ai_ops.model_config["pdf"] == "anthropic/claude-3-opus-20240229"

def test_get_cache_path(ai_ops, sample_image):
    """Test cache path generation."""
    cache_path = ai_ops._get_cache_path(sample_image, "image")
    assert cache_path.endswith("_image.json")
    assert os.path.dirname(cache_path) == ai_ops.cache_dir

def test_get_cached_result(ai_ops, temp_dir):
    """Test retrieving cached results."""
    # Create a test cache file
    cache_path = os.path.join(ai_ops.cache_dir, "test_cache.json")
    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "result": {"test": "data"}
    }
    with open(cache_path, "w") as f:
        json.dump(cache_data, f)

    # Test valid cache
    result = ai_ops._get_cached_result(cache_path)
    assert result == {"test": "data"}

    # Test expired cache
    cache_data["timestamp"] = (datetime.now() - timedelta(days=2)).isoformat()
    with open(cache_path, "w") as f:
        json.dump(cache_data, f)
    result = ai_ops._get_cached_result(cache_path)
    assert result is None

def test_save_to_cache(ai_ops, temp_dir):
    """Test saving results to cache."""
    cache_path = os.path.join(ai_ops.cache_dir, "test_save.json")
    test_result = {"test": "data"}

    ai_ops._save_to_cache(cache_path, test_result)

    assert os.path.exists(cache_path)
    with open(cache_path, "r") as f:
        saved_data = json.load(f)
    assert "timestamp" in saved_data
    assert saved_data["result"] == test_result

def test_prepare_image_data(ai_ops, sample_image):
    """Test image data preparation."""
    image_data = ai_ops._prepare_image_data(sample_image)
    assert image_data["type"] == "image_url"
    assert "url" in image_data["image_url"]
    assert image_data["image_url"]["url"].startswith("data:image/jpeg;base64,")

def test_prepare_pdf_data(ai_ops, sample_pdf):
    """Test PDF data preparation."""
    pdf_data = ai_ops._prepare_pdf_data(sample_pdf)
    assert pdf_data["type"] == "file"
    assert "filename" in pdf_data["file"]
    assert "file_data" in pdf_data["file"]
    assert pdf_data["file"]["file_data"].startswith("data:application/pdf;base64,")

@patch("requests.post")
def test_analyze_image(mock_post, ai_ops, sample_image):
    """Test image analysis."""
    # Mock API response
    mock_response = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": "Test analysis"}}]}
    mock_post.return_value = mock_response

    result = ai_ops.analyze_image(sample_image)
    assert "choices" in result
    assert result["choices"][0]["message"]["content"] == "Test analysis"

    # Verify API call
    mock_post.assert_called_once()
    call_args = mock_post.call_args[1]
    assert call_args["headers"]["Authorization"] == "Bearer test_api_key"
    assert call_args["json"]["model"] == ai_ops.model_config["image"]

@patch("requests.post")
def test_analyze_pdf(mock_post, ai_ops, sample_pdf):
    """Test PDF analysis."""
    # Mock API response
    mock_response = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": "Test analysis"}}]}
    mock_post.return_value = mock_response

    result = ai_ops.analyze_pdf(sample_pdf)
    assert "choices" in result
    assert result["choices"][0]["message"]["content"] == "Test analysis"

    # Verify API call
    mock_post.assert_called_once()
    call_args = mock_post.call_args[1]
    assert call_args["headers"]["Authorization"] == "Bearer test_api_key"
    assert call_args["json"]["model"] == ai_ops.model_config["pdf"]

def test_batch_analyze_images(ai_ops, temp_dir):
    """Test batch image analysis."""
    # Create multiple test images
    image_paths = []
    for i in range(3):
        path = os.path.join(temp_dir, f"test_{i}.jpg")
        with open(path, "wb") as f:
            f.write(b"fake image data")
        image_paths.append(path)

    with patch.object(ai_ops, "analyze_image") as mock_analyze:
        mock_analyze.return_value = {"test": "result"}
        results = ai_ops.batch_analyze_images(image_paths)

        assert len(results) == 3
        assert all(path in results for path in image_paths)
        assert mock_analyze.call_count == 3

def test_batch_analyze_pdfs(ai_ops, temp_dir):
    """Test batch PDF analysis."""
    # Create multiple test PDFs
    pdf_paths = []
    for i in range(3):
        path = os.path.join(temp_dir, f"test_{i}.pdf")
        with open(path, "wb") as f:
            f.write(b"fake pdf data")
        pdf_paths.append(path)

    with patch.object(ai_ops, "analyze_pdf") as mock_analyze:
        mock_analyze.return_value = {"test": "result"}
        results = ai_ops.batch_analyze_pdfs(pdf_paths)

        assert len(results) == 3
        assert all(path in results for path in pdf_paths)
        assert mock_analyze.call_count == 3

def test_clear_cache(ai_ops, temp_dir):
    """Test cache clearing."""
    # Create test cache files
    cache_files = [
        "test1_image.json",
        "test2_image.json",
        "test1_pdf.json",
        "test2_pdf.json"
    ]
    for file in cache_files:
        path = os.path.join(ai_ops.cache_dir, file)
        with open(path, "w") as f:
            json.dump({"test": "data"}, f)

    # Test clearing specific type
    ai_ops.clear_cache("image")
    remaining_files = list(Path(ai_ops.cache_dir).glob("*.json"))
    assert len(remaining_files) == 2
    assert all("pdf" in str(f) for f in remaining_files)

    # Test clearing all
    ai_ops.clear_cache()
    assert len(list(Path(ai_ops.cache_dir).glob("*.json"))) == 0

def test_error_handling(ai_ops, temp_dir):
    """Test error handling in various scenarios."""
    # Test invalid file path
    result = ai_ops.analyze_image("nonexistent.jpg")
    assert "error" in result

    # Test file outside base directory
    outside_path = os.path.join(os.path.dirname(temp_dir), "outside.jpg")
    result = ai_ops.analyze_image(outside_path)
    assert "error" in result

    # Test invalid file type
    invalid_path = os.path.join(temp_dir, "test.txt")
    with open(invalid_path, "w") as f:
        f.write("test data")
    result = ai_ops.analyze_image(invalid_path)
    assert "error" in result

    # Test file too large
    large_path = os.path.join(temp_dir, "large.jpg")
    with open(large_path, "wb") as f:
        f.write(b"x" * (ai_ops.max_file_size + 1))
    result = ai_ops.analyze_image(large_path)
    assert "error" in result
