"""
Command-line interface for AI-powered file operations.
"""

import os
import sys
import json
import yaml
import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict
from .ai_ops import AIPoweredFileOperations

def load_config(config_path: Optional[str] = None) -> Dict:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Replace environment variables
        if config.get('api', {}).get('key', '').startswith('${'):
            env_var = config['api']['key'][2:-1]
            config['api']['key'] = os.getenv(env_var)

        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def setup_logging(config: Dict):
    """Set up logging configuration."""
    log_config = config.get('logging', {})
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_config.get('file', 'ai_ops.log')),
            logging.StreamHandler()
        ]
    )

def setup_parser(config: Dict) -> argparse.ArgumentParser:
    """Set up command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="AI-powered file operations using OpenRouter's API"
    )

    # Global options
    parser.add_argument(
        "--api-key",
        help="OpenRouter API key (default: from config or OPENROUTER_API_KEY)",
        default=config.get('api', {}).get('key')
    )
    parser.add_argument(
        "--base-dir",
        help="Base directory for file operations",
        default=config.get('files', {}).get('base_dir', '.')
    )
    parser.add_argument(
        "--cache-dir",
        help="Directory for caching analysis results",
        default=config.get('files', {}).get('cache_dir', '.ai_cache')
    )
    parser.add_argument(
        "--max-size",
        help="Maximum file size in MB",
        type=int,
        default=config.get('files', {}).get('max_size', 10)
    )
    parser.add_argument(
        "--workers",
        help="Maximum number of concurrent workers",
        type=int,
        default=config.get('processing', {}).get('max_workers', 4)
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file",
        default=None
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Analyze image command
    image_parser = subparsers.add_parser("image", help="Analyze an image")
    image_parser.add_argument("path", help="Path to the image file")
    image_parser.add_argument(
        "--prompt",
        help="Custom prompt for image analysis",
        default=config.get('prompts', {}).get('image', "What's in this image?")
    )
    image_parser.add_argument(
        "--model",
        help="Model type to use (default, ocr, description)",
        default="default"
    )
    image_parser.add_argument(
        "--no-cache",
        help="Disable result caching",
        action="store_true"
    )

    # Analyze PDF command
    pdf_parser = subparsers.add_parser("pdf", help="Analyze a PDF document")
    pdf_parser.add_argument("path", help="Path to the PDF file")
    pdf_parser.add_argument(
        "--prompt",
        help="Custom prompt for document analysis",
        default=config.get('prompts', {}).get('pdf', "What are the main points in this document?")
    )
    pdf_parser.add_argument(
        "--model",
        help="Model type to use (default, summary, extraction)",
        default="default"
    )
    pdf_parser.add_argument(
        "--no-cache",
        help="Disable result caching",
        action="store_true"
    )

    # Batch analyze images command
    batch_image_parser = subparsers.add_parser(
        "batch-images",
        help="Analyze multiple images"
    )
    batch_image_parser.add_argument(
        "paths",
        nargs="+",
        help="Paths to image files"
    )
    batch_image_parser.add_argument(
        "--prompt",
        help="Custom prompt for image analysis",
        default=config.get('prompts', {}).get('image', "What's in this image?")
    )
    batch_image_parser.add_argument(
        "--model",
        help="Model type to use (default, ocr, description)",
        default="default"
    )
    batch_image_parser.add_argument(
        "--no-cache",
        help="Disable result caching",
        action="store_true"
    )

    # Batch analyze PDFs command
    batch_pdf_parser = subparsers.add_parser(
        "batch-pdfs",
        help="Analyze multiple PDFs"
    )
    batch_pdf_parser.add_argument(
        "paths",
        nargs="+",
        help="Paths to PDF files"
    )
    batch_pdf_parser.add_argument(
        "--prompt",
        help="Custom prompt for document analysis",
        default=config.get('prompts', {}).get('pdf', "What are the main points in this document?")
    )
    batch_pdf_parser.add_argument(
        "--model",
        help="Model type to use (default, summary, extraction)",
        default="default"
    )
    batch_pdf_parser.add_argument(
        "--no-cache",
        help="Disable result caching",
        action="store_true"
    )

    # Cache management commands
    cache_parser = subparsers.add_parser("cache", help="Cache management")
    cache_subparsers = cache_parser.add_subparsers(dest="cache_command")

    # Clear cache command
    clear_parser = cache_subparsers.add_parser("clear", help="Clear cache")
    clear_parser.add_argument(
        "--type",
        help="Type of cache to clear (image, pdf, or all)",
        default="all"
    )

    # Show cache stats command
    cache_subparsers.add_parser("stats", help="Show cache statistics")

    return parser

def format_result(result: dict, config: Dict) -> str:
    """Format analysis result for display."""
    if "error" in result:
        return f"Error: {result['error']}"

    if "choices" in result and result["choices"]:
        content = result["choices"][0]["message"]["content"]

        # Add file info if enabled
        if config.get('output', {}).get('show_file_info', True):
            content = f"File: {result.get('file', 'Unknown')}\n{content}"

        # Add timestamp if enabled
        if config.get('output', {}).get('show_timestamps', True):
            from datetime import datetime
            content = f"[{datetime.now().isoformat()}] {content}"

        return content

    return json.dumps(result, indent=config.get('output', {}).get('indent', 2))

def main():
    """Main entry point for the CLI."""
    # Load initial config
    config = load_config()

    # Parse command line arguments
    parser = setup_parser(config)
    args = parser.parse_args()

    # Reload config if specified
    if args.config:
        config = load_config(args.config)
        parser = setup_parser(config)
        args = parser.parse_args()

    # Setup logging
    setup_logging(config)

    if not args.api_key:
        print("Error: OpenRouter API key is required")
        print("Set it using --api-key, config file, or OPENROUTER_API_KEY environment variable")
        sys.exit(1)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize AI operations
    ai_ops = AIPoweredFileOperations(
        base_dir=args.base_dir,
        api_key=args.api_key,
        max_file_size=args.max_size * 1024 * 1024,
        cache_dir=args.cache_dir,
        max_workers=args.workers,
        model_config=config.get('models', {}),
        cache_ttl=config.get('processing', {}).get('cache_ttl', 86400)
    )

    try:
        if args.command == "image":
            result = ai_ops.analyze_image(
                args.path,
                prompt=args.prompt,
                use_cache=not args.no_cache,
                model_type=args.model
            )
            print(format_result(result, config))

        elif args.command == "pdf":
            result = ai_ops.analyze_pdf(
                args.path,
                prompt=args.prompt,
                use_cache=not args.no_cache,
                model_type=args.model
            )
            print(format_result(result, config))

        elif args.command == "batch-images":
            results = ai_ops.batch_analyze_images(
                args.paths,
                prompt=args.prompt,
                use_cache=not args.no_cache,
                model_type=args.model
            )
            for path, result in results.items():
                print(f"\n{os.path.basename(path)}:")
                print(format_result(result, config))

        elif args.command == "batch-pdfs":
            results = ai_ops.batch_analyze_pdfs(
                args.paths,
                prompt=args.prompt,
                use_cache=not args.no_cache,
                model_type=args.model
            )
            for path, result in results.items():
                print(f"\n{os.path.basename(path)}:")
                print(format_result(result, config))

        elif args.command == "cache":
            if args.cache_command == "clear":
                ai_ops.clear_cache(args.type if args.type != "all" else None)
                print(f"Cleared {args.type} cache")

            elif args.cache_command == "stats":
                stats = ai_ops.get_cache_stats()
                if "error" in stats:
                    print(f"Error: {stats['error']}")
                else:
                    print("\nCache Statistics:")
                    print(f"Total files: {stats['total_files']}")
                    print(f"Image cache: {stats['image_cache']}")
                    print(f"PDF cache: {stats['pdf_cache']}")
                    print(f"Total size: {stats['total_size'] / 1024:.2f} KB")
                    if stats['oldest_cache']:
                        print(f"Oldest cache: {stats['oldest_cache']}")
                    if stats['newest_cache']:
                        print(f"Newest cache: {stats['newest_cache']}")

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
