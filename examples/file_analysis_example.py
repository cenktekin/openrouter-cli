#!/usr/bin/env python3
"""
Example script demonstrating file analysis functionality with OpenRouter CLI.
"""

import asyncio
import os
from pathlib import Path
from tools.file_operations.ai_ops import AIPoweredFileOperations
from openrouter_cli import OpenRouterKeyManager

async def analyze_single_file(analyzer: AIPoweredFileOperations, file_path: str):
    """Analyze a single file with progress tracking."""
    print(f"\nAnalyzing file: {file_path}")

    try:
        # Get file size
        file_size = os.path.getsize(file_path)
        print(f"File size: {file_size / 1024:.1f} KB")

        # Analyze file
        result = await analyzer.analyze_file(
            file_path,
            "Analyze this file and provide a detailed summary"
        )

        # Print results
        print("\nAnalysis Results:")
        print("-" * 50)
        print(result["analysis"])
        print("-" * 50)

        # Print metadata
        print("\nMetadata:")
        print(f"Model used: {result['model']}")
        print(f"Processing time: {result['processing_time']:.2f} seconds")
        print(f"Cache hit: {result['cache_hit']}")

    except Exception as e:
        print(f"Error analyzing file: {str(e)}")

async def batch_analyze_files(analyzer: AIPoweredFileOperations, pattern: str):
    """Analyze multiple files with progress tracking."""
    # Get list of files
    files = list(Path(".").glob(pattern))
    if not files:
        print(f"No files found matching pattern: {pattern}")
        return

    print(f"\nFound {len(files)} files to analyze")

    # Process files
    results = await analyzer.batch_analyze_files(
        [str(f) for f in files],
        "Compare these files and identify common themes"
    )

    # Print results
    print("\nBatch Analysis Results:")
    print("-" * 50)
    for file_path, result in results.items():
        print(f"\nFile: {file_path}")
        print("-" * 30)
        print(result["analysis"])
        print(f"Processing time: {result['processing_time']:.2f} seconds")
        print(f"Cache hit: {result['cache_hit']}")

async def main():
    # Initialize key manager
    key_manager = OpenRouterKeyManager()
    if not key_manager.has_keys():
        print("No API keys found. Please set up your API keys first.")
        return

    # Create analyzer
    analyzer = AIPoweredFileOperations(
        base_dir=".",
        api_key=key_manager.get_random_key(),
        allowed_extensions=[
            ".txt", ".md", ".pdf", ".jpg", ".jpeg", ".png",
            ".py", ".js", ".java", ".cpp", ".h"
        ],
        max_file_size=10 * 1024 * 1024  # 10MB
    )

    while True:
        print("\nOpenRouter File Analysis")
        print("1. Analyze single file")
        print("2. Batch analyze files")
        print("3. Clear cache")
        print("4. Exit")

        choice = input("\nSelect option (1-4): ").strip()

        if choice == "1":
            file_path = input("\nEnter file path: ").strip()
            if os.path.exists(file_path):
                await analyze_single_file(analyzer, file_path)
            else:
                print("File not found")

        elif choice == "2":
            pattern = input("\nEnter file pattern (e.g., *.pdf): ").strip()
            await batch_analyze_files(analyzer, pattern)

        elif choice == "3":
            await analyzer.clear_cache()
            print("Cache cleared")

        elif choice == "4":
            break

        else:
            print("Invalid option")

if __name__ == "__main__":
    asyncio.run(main())
