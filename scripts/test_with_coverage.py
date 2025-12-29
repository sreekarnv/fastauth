"""Helper scripts for development tasks."""

import shutil
import sys
from pathlib import Path

import pytest


def run_tests_with_coverage():
    """Run tests with coverage reports."""

    args = [
        "--cov=fastauth",
        "--cov-report=html",
        "--cov-report=xml",
        "--cov-report=term-missing:skip-covered",
    ]

    args.extend(sys.argv[1:])
    exit_code = pytest.main(args)
    try:
        test_results = Path("test-results")
        if test_results.exists():
            folders = sorted([f for f in test_results.iterdir() if f.is_dir()])
            if folders:
                latest_folder = folders[-1]
                htmlcov = Path("htmlcov")
                if htmlcov.exists():
                    target_htmlcov = latest_folder / "htmlcov"
                    if target_htmlcov.exists():
                        shutil.rmtree(target_htmlcov)
                    shutil.move(str(htmlcov), str(target_htmlcov))

                coverage_xml = Path("coverage.xml")
                if coverage_xml.exists():
                    shutil.move(str(coverage_xml), str(latest_folder / "coverage.xml"))

                coverage_file = Path(".coverage")
                if coverage_file.exists():
                    shutil.move(str(coverage_file), str(latest_folder / ".coverage"))

                print(f"\nCoverage reports moved to: {latest_folder}")
    except Exception as e:
        print(f"Warning: Could not move coverage files: {e}")

    sys.exit(exit_code)


if __name__ == "__main__":
    run_tests_with_coverage()
