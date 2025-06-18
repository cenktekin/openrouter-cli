#!/usr/bin/env python3
"""
Test runner script for MCP file operations tests.
Provides options for running tests with different configurations and reporting.
"""

import argparse
import sys
import os
import pytest
import json
from datetime import datetime
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Run MCP file operations tests")
    parser.add_argument(
        "--config",
        type=str,
        default="test_config.yaml",
        help="Path to test configuration file"
    )
    parser.add_argument(
        "--report",
        type=str,
        choices=["json", "html", "xml"],
        help="Generate test report in specified format"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "--parallel",
        "-p",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--filter",
        type=str,
        help="Filter tests by name pattern"
    )
    return parser.parse_args()

def setup_test_env(config_path):
    """Set up test environment variables."""
    os.environ["TEST_CONFIG"] = str(config_path)
    os.environ["TEST_MODE"] = "true"

def generate_report(args, results):
    """Generate test report in specified format."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path("test_reports")
    report_dir.mkdir(exist_ok=True)

    if args.report == "json":
        report_file = report_dir / f"test_report_{timestamp}.json"
        with open(report_file, "w") as f:
            json.dump(results, f, indent=2)
    elif args.report == "html":
        pytest.main(["--html", str(report_dir / f"test_report_{timestamp}.html")])
    elif args.report == "xml":
        pytest.main(["--junitxml", str(report_dir / f"test_report_{timestamp}.xml")])

def main():
    args = parse_args()

    # Set up test environment
    setup_test_env(args.config)

    # Build pytest arguments
    pytest_args = []

    if args.verbose:
        pytest_args.append("-v")

    if args.parallel:
        pytest_args.extend(["-n", "auto"])

    if args.coverage:
        pytest_args.extend([
            "--cov=tools.file_operations",
            "--cov-report=term-missing",
            "--cov-report=html"
        ])

    if args.filter:
        pytest_args.append(f"-k {args.filter}")

    # Add test files
    pytest_args.extend([
        "test_mcp_client.py",
        "test_mcp_ops.py"
    ])

    # Run tests
    results = pytest.main(pytest_args)

    # Generate report if requested
    if args.report:
        generate_report(args, {
            "timestamp": datetime.now().isoformat(),
            "config": args.config,
            "coverage": args.coverage,
            "parallel": args.parallel,
            "filter": args.filter,
            "results": results
        })

    return results

if __name__ == "__main__":
    sys.exit(main())
