import pytest
from openrouter_cli import OpenRouterKeyManager, load_models, format_chat_history

def test_key_manager():
    """Test OpenRouterKeyManager functionality."""
    manager = OpenRouterKeyManager()
    assert isinstance(manager.keys, list)
    assert isinstance(manager.get_random_key(), (str, type(None)))

def test_load_models():
    """Test model loading functionality."""
    models = load_models()
    assert isinstance(models, list)
    if models:
        assert all(isinstance(m, dict) for m in models)
        assert all('name' in m for m in models)

def test_format_chat_history():
    """Test chat history formatting."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    formatted = format_chat_history(messages)
    assert "You: Hello" in formatted
    assert "Assistant: Hi there!" in formatted
