# OpenRouter CLI

A command-line interface for interacting with OpenRouter's AI models.

This tool provides a rich set of features for chat, file analysis, and MCP, all through a user-friendly CLI interface.

![Main Application](images/app.png)

## Features

### Core Features
- **Interactive Chat**: Chat with various AI models through OpenRouter
- **Model Selection**: Choose from a wide range of available models
- **Key Rotation**: Support for multiple API keys with automatic rotation
- **Schema Management**: Define and validate response formats
- **Response Formatting**: Multiple output formats (JSON, pretty, compact)

### File Analysis
- **Image Analysis**: Analyze images with AI vision models
- **PDF Processing**: Extract and summarize PDF documents
- **Text Analysis**: Process and analyze text files
- **Code Review**: Analyze and review code files

### Advanced Features
- **Batch Processing**: Process multiple files concurrently
- **Caching System**: Automatic caching of analysis results
- **Custom Prompts**: Support for custom analysis prompts
- **Progress Tracking**: Real-time progress monitoring
- **Multiple Models**: Support for various OpenRouter models

### File Operations
- **Supported Formats**:
  - Images (`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tiff`)
  - PDFs (`.pdf`)
  - Text Files (`.txt`, `.md`)
  - Code Files (`.py`, `.js`, `.java`, `.cpp`, etc.)
- **File Management**:
  - Size limits and validation
  - Extension filtering
  - Path safety checks
  - Cache management

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mexyusef/openrouter-cli.git
cd openrouter-cli
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenRouter API key(s):
```bash
# Single key
export OPENROUTER_API_KEY="your_api_key"

# Or multiple keys in ~/OPENROUTER_API_KEYS.json
{
    "keys": [
        {"key": "key1", "description": "Primary key"},
        {"key": "key2", "description": "Backup key"}
    ]
}
```

## Usage

### Interactive Chat

```bash
# Start interactive chat
python openrouter_cli.py

# Available commands:
/exit          - Quit the chat
/clear         - Clear chat history
/model         - Switch AI model
/copy          - Copy last response
/copy all      - Copy entire conversation
/help          - Show help message
/schema list   - Show available schemas
/schema use    - Use a specific schema
/schema show   - Show current schema
/format        - Set response format (json/pretty/compact)
```

### File Analysis

```python
from openrouter_cli.tools.file_operations.ai_ops import AIPoweredFileOperations

# Initialize the analyzer
analyzer = AIPoweredFileOperations(
    base_dir=".",
    api_key="your_api_key",
    allowed_extensions=[".txt", ".pdf", ".jpg"],
    max_file_size=10 * 1024 * 1024  # 10MB
)

# Analyze an image
result = await analyzer.analyze_file(
    "image.jpg",
    "Describe what you see in this image"
)

# Process multiple files
results = await analyzer.batch_analyze_files(
    ["doc1.pdf", "doc2.pdf"],
    "Compare these documents"
)
```

### Command Line Interface

```bash
# Analyze a file
python -m openrouter_cli.tools.file_operations.cli analyze image.jpg

# Batch process files
python -m openrouter_cli.tools.file_operations.cli batch "*.pdf"

# Clear cache
python -m openrouter_cli.tools.file_operations.cli clear-cache
```

## Configuration

Create a `config.yaml` file:

```yaml
api:
  key: ${OPENROUTER_API_KEY}
  url: "https://openrouter.ai/api/v1/chat/completions"
  timeout: 30

files:
  base_dir: "."
  cache_dir: ".ai_cache"
  max_size: 10  # MB
  allowed_extensions:
    images:
      - ".jpg"
      - ".png"
    pdfs:
      - ".pdf"

models:
  image:
    default: "openai/gpt-4-vision-preview"
  pdf:
    default: "anthropic/claude-3-opus-20240229"
```

## Docker Support

Run using Docker:

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

## Security Features

- Path traversal protection
- File type restrictions
- File size limits
- Secure API key handling
- Access control validation
- Key rotation support

## Error Handling

All operations return a dictionary with either:
- Success: Operation details and results
- Error: Error message and details

Example:
```python
result = await analyzer.analyze_file("image.jpg")
if "error" in result:
    print(f"Error: {result['error']}")
else:
    print(f"Analysis: {result['analysis']}")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Dependencies

- openai: For OpenRouter API integration
- rich: For enhanced console output
- pyyaml: For configuration management
- cryptography: For secure operations
- tqdm: For progress tracking
- pyperclip: For clipboard operations
- python-dotenv: For environment variable management

## Requirements

- Python 3.7+
- OpenRouter API key(s)
- Operating system with file system support
- Sufficient permissions for file operations
