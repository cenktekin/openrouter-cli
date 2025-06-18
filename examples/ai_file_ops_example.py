"""
Example script demonstrating the usage of AIPoweredFileOperations.
"""

import os
import json
from pathlib import Path
from tools.file_operations.ai_ops import AIPoweredFileOperations

def main():
    # Initialize the AI-powered file operations tool
    ai_ops = AIPoweredFileOperations(
        base_dir=".",  # Current directory
        api_key=os.getenv("OPENROUTER_API_KEY"),  # Get API key from environment
        allowed_extensions=[".jpg", ".png", ".pdf"],
        max_file_size=10 * 1024 * 1024,  # 10MB
        cache_dir=".ai_cache"  # Custom cache directory
    )

    # Example 1: Analyze a single image
    print("\nExample 1: Analyzing a single image")
    image_path = "sample.jpg"
    if os.path.exists(image_path):
        result = ai_ops.analyze_image(
            image_path,
            prompt="Describe this image in detail, including any text visible in it."
        )
        if "error" not in result:
            print(f"Image analysis: {result['choices'][0]['message']['content']}")
        else:
            print(f"Error: {result['error']}")

    # Example 2: Analyze a PDF document
    print("\nExample 2: Analyzing a PDF document")
    pdf_path = "sample.pdf"
    if os.path.exists(pdf_path):
        result = ai_ops.analyze_pdf(
            pdf_path,
            prompt="Summarize the main points of this document and extract any key figures or statistics."
        )
        if "error" not in result:
            print(f"PDF analysis: {result['choices'][0]['message']['content']}")
        else:
            print(f"Error: {result['error']}")

    # Example 3: Batch process multiple images
    print("\nExample 3: Batch processing images")
    image_dir = "images"
    if os.path.exists(image_dir):
        image_paths = [
            str(p) for p in Path(image_dir).glob("*.jpg")
        ] + [
            str(p) for p in Path(image_dir).glob("*.png")
        ]

        if image_paths:
            results = ai_ops.batch_analyze_images(
                image_paths,
                prompt="What objects and people are visible in this image?"
            )

            print(f"\nProcessed {len(results)} images:")
            for path, result in results.items():
                if "error" not in result:
                    print(f"\n{os.path.basename(path)}:")
                    print(result['choices'][0]['message']['content'])
                else:
                    print(f"\n{os.path.basename(path)}: Error - {result['error']}")

    # Example 4: Batch process multiple PDFs
    print("\nExample 4: Batch processing PDFs")
    pdf_dir = "documents"
    if os.path.exists(pdf_dir):
        pdf_paths = [str(p) for p in Path(pdf_dir).glob("*.pdf")]

        if pdf_paths:
            results = ai_ops.batch_analyze_pdfs(
                pdf_paths,
                prompt="Extract the key findings and conclusions from this document."
            )

            print(f"\nProcessed {len(results)} PDFs:")
            for path, result in results.items():
                if "error" not in result:
                    print(f"\n{os.path.basename(path)}:")
                    print(result['choices'][0]['message']['content'])
                else:
                    print(f"\n{os.path.basename(path)}: Error - {result['error']}")

    # Example 5: Cache management
    print("\nExample 5: Cache management")
    # Clear image analysis cache
    ai_ops.clear_cache("image")
    print("Cleared image analysis cache")

    # Clear all caches
    ai_ops.clear_cache()
    print("Cleared all caches")

if __name__ == "__main__":
    main()
