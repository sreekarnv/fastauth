"""
Pytest configuration for test report generation.

Generates timestamped test reports in test-results folder:
- HTML report
- JUnit XML report
- Test log file
- Coverage report (when --cov is used)
"""

from datetime import datetime
from pathlib import Path


def pytest_configure(config):
    """Configure pytest to generate timestamped test reports."""
    # Create timestamp for this test run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create test results directory
    results_dir = Path("test-results") / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)

    # Configure HTML report
    if not hasattr(config.option, "htmlpath") or not config.option.htmlpath:
        config.option.htmlpath = str(results_dir / "report.html")
        config.option.self_contained_html = True

    # Configure JUnit XML report
    if not hasattr(config.option, "xmlpath") or not config.option.xmlpath:
        config.option.xmlpath = str(results_dir / "junit.xml")

    # Configure log file
    if not hasattr(config.option, "log_file") or not config.option.log_file:
        config.option.log_file = str(results_dir / "pytest.log")
        config.option.log_file_level = "INFO"
        config.option.log_file_format = "%(asctime)s [%(levelname)s] %(message)s"
        config.option.log_file_date_format = "%Y-%m-%d %H:%M:%S"

    # Configure coverage report (if --cov is used)
    if hasattr(config.option, "cov_report") and config.option.cov_report:
        # Override coverage paths to use timestamped folder
        config.option.htmlcov = str(results_dir / "htmlcov")
        config.option.cov_report = {
            "html": str(results_dir / "htmlcov"),
            "xml": str(results_dir / "coverage.xml"),
        }

        # Also set coverage data file in timestamped folder
        if hasattr(config.option, "cov_source"):
            config.option.cov_config = {"data_file": str(results_dir / ".coverage")}

    # Store results directory for reference
    config._results_dir = results_dir

    print(f"\n[TEST REPORTS] Results will be saved to: {results_dir}")


def pytest_sessionfinish(session, exitstatus):
    """Print summary after test session completes."""
    if hasattr(session.config, "_results_dir"):
        results_dir = session.config._results_dir
        print(f"\n[TEST REPORTS] Reports generated in: {results_dir}")
        print(f"   - HTML Report: {results_dir / 'report.html'}")
        print(f"   - JUnit XML: {results_dir / 'junit.xml'}")
        print(f"   - Test Log: {results_dir / 'pytest.log'}")

        if session.config.option.cov_report:
            print(f"   - Coverage HTML: {results_dir / 'htmlcov' / 'index.html'}")
            print(f"   - Coverage XML: {results_dir / 'coverage.xml'}")
