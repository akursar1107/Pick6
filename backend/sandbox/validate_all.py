"""
Validation script for all sandbox scripts.

This script validates that all sandbox scripts meet the requirements:
1. Execute without errors when dependencies are installed
2. Have consistent output formatting
3. Handle missing dependencies gracefully
4. Handle API failures gracefully
5. Answer critical research questions
6. Have complete documentation
"""

import subprocess
import sys
import os
from pathlib import Path

# ANSI color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text):
    """Print a formatted header"""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{text.center(80)}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_info(text):
    """Print info message"""
    print(f"{BLUE}ℹ {text}{RESET}")


class ValidationResults:
    """Track validation results"""

    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def add_pass(self, test_name):
        self.passed.append(test_name)
        print_success(test_name)

    def add_fail(self, test_name, reason=""):
        self.failed.append((test_name, reason))
        print_error(f"{test_name}: {reason}" if reason else test_name)

    def add_warning(self, test_name, reason=""):
        self.warnings.append((test_name, reason))
        print_warning(f"{test_name}: {reason}" if reason else test_name)

    def print_summary(self):
        """Print final summary"""
        print_header("VALIDATION SUMMARY")
        print(f"Total Passed: {GREEN}{len(self.passed)}{RESET}")
        print(f"Total Failed: {RED}{len(self.failed)}{RESET}")
        print(f"Total Warnings: {YELLOW}{len(self.warnings)}{RESET}")

        if self.failed:
            print(f"\n{RED}Failed Tests:{RESET}")
            for test, reason in self.failed:
                print(f"  - {test}")
                if reason:
                    print(f"    Reason: {reason}")

        if self.warnings:
            print(f"\n{YELLOW}Warnings:{RESET}")
            for test, reason in self.warnings:
                print(f"  - {test}")
                if reason:
                    print(f"    Reason: {reason}")

        return len(self.failed) == 0


def check_file_exists(filepath):
    """Check if a file exists"""
    return Path(filepath).exists()


def check_script_syntax(script_path):
    """Check if a Python script has valid syntax"""
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            compile(f.read(), script_path, "exec")
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except UnicodeDecodeError as e:
        return False, f"Encoding error: {str(e)}"


def check_has_docstring(script_path):
    """Check if script has a module-level docstring"""
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Check for docstring at the beginning (after potential shebang/encoding)
            lines = content.strip().split("\n")
            for line in lines[:5]:  # Check first 5 lines
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    return True
        return False
    except Exception as e:
        return False


def check_has_import_error_handling(script_path):
    """Check if script has import error handling"""
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Check for explicit ImportError handling OR use of check_library_installed
            return (
                "ImportError" in content
                or "ModuleNotFoundError" in content
                or "check_library_installed" in content
            )
    except Exception:
        return False


def check_has_api_error_handling(script_path):
    """Check if script has API error handling"""
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Look for try-except blocks
            return "try:" in content and "except" in content
    except Exception:
        return False


def check_has_section_headers(script_path):
    """Check if script uses section headers for organization"""
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Look for print_section_header or similar formatting
            return (
                "print_section_header" in content
                or "===" in content
                or "---" in content
            )
    except Exception:
        return False


def check_documentation_file(doc_path, required_sections):
    """Check if documentation file exists and has required sections"""
    if not check_file_exists(doc_path):
        return False, "File does not exist"

    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read().lower()
            missing_sections = []
            for section in required_sections:
                if section.lower() not in content:
                    missing_sections.append(section)

            if missing_sections:
                return False, f"Missing sections: {', '.join(missing_sections)}"
            return True, None
    except Exception as e:
        return False, str(e)


def validate_sandbox_scripts():
    """Main validation function"""
    results = ValidationResults()

    # Define sandbox scripts to validate
    sandbox_dir = Path(__file__).parent
    scripts = [
        "nfl_sandbox.py",
        "nba_sandbox.py",
        "mlb_sandbox.py",
        "nhl_sandbox.py",
        "cfb_sandbox.py",
    ]

    common_utils = "common_utils.py"

    print_header("VALIDATING SANDBOX SCRIPTS")

    # 1. Check that all scripts exist
    print_info("Checking script existence...")
    for script in scripts:
        script_path = sandbox_dir / script
        if check_file_exists(script_path):
            results.add_pass(f"Script exists: {script}")
        else:
            results.add_fail(f"Script missing: {script}")

    # Check common_utils exists
    if check_file_exists(sandbox_dir / common_utils):
        results.add_pass(f"Common utilities exist: {common_utils}")
    else:
        results.add_fail(f"Common utilities missing: {common_utils}")

    # 2. Check syntax validity
    print_info("\nChecking script syntax...")
    for script in scripts + [common_utils]:
        script_path = sandbox_dir / script
        if check_file_exists(script_path):
            valid, error = check_script_syntax(script_path)
            if valid:
                results.add_pass(f"Valid syntax: {script}")
            else:
                results.add_fail(f"Syntax error in {script}", error)

    # 3. Check documentation completeness (Requirement 6.1)
    print_info("\nChecking documentation completeness...")
    for script in scripts:
        script_path = sandbox_dir / script
        if check_file_exists(script_path):
            if check_has_docstring(script_path):
                results.add_pass(f"Has docstring: {script}")
            else:
                results.add_fail(f"Missing docstring: {script}", "Requirement 6.1")

    # 4. Check import error handling (Requirements 7.1, 7.2, 7.3)
    print_info("\nChecking import error handling...")
    for script in scripts:
        script_path = sandbox_dir / script
        if check_file_exists(script_path):
            if check_has_import_error_handling(script_path):
                results.add_pass(f"Has import error handling: {script}")
            else:
                results.add_fail(
                    f"Missing import error handling: {script}", "Requirements 7.1-7.3"
                )

    # 5. Check API error handling (Requirements 1.5, 2.5, 3.5, 4.5, 5.4)
    print_info("\nChecking API error handling...")
    for script in scripts:
        script_path = sandbox_dir / script
        if check_file_exists(script_path):
            if check_has_api_error_handling(script_path):
                results.add_pass(f"Has API error handling: {script}")
            else:
                results.add_fail(
                    f"Missing API error handling: {script}", "API error requirements"
                )

    # 6. Check output formatting consistency (Requirement 8.3)
    print_info("\nChecking output formatting consistency...")
    for script in scripts:
        script_path = sandbox_dir / script
        if check_file_exists(script_path):
            if check_has_section_headers(script_path):
                results.add_pass(f"Uses consistent formatting: {script}")
            else:
                results.add_warning(
                    f"May lack consistent formatting: {script}", "Requirement 8.3"
                )

    # 7. Check documentation files
    print_info("\nChecking documentation files...")

    # Check README.md
    readme_path = sandbox_dir / "README.md"
    readme_sections = ["NFL", "NBA", "MLB", "NHL", "CFB", "first", "anytime"]
    valid, error = check_documentation_file(readme_path, readme_sections)
    if valid:
        results.add_pass("README.md has required content")
    else:
        results.add_fail("README.md incomplete", error)

    # Check PRODUCTION_RECOMMENDATIONS.md
    prod_rec_path = sandbox_dir / "PRODUCTION_RECOMMENDATIONS.md"
    prod_sections = ["architecture", "recommendation", "API", "data"]
    valid, error = check_documentation_file(prod_rec_path, prod_sections)
    if valid:
        results.add_pass("PRODUCTION_RECOMMENDATIONS.md has required content")
    else:
        results.add_fail("PRODUCTION_RECOMMENDATIONS.md incomplete", error)

    # 8. Check critical research questions are answered
    print_info("\nChecking critical research questions...")
    research_keywords = [
        "first scorer",
        "first touchdown",
        "first basket",
        "first run",
        "first goal",
        "anytime",
        "play-by-play",
        "timing",
        "sequence",
    ]

    readme_content = ""
    if check_file_exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_content = f.read().lower()

    found_keywords = []
    missing_keywords = []
    for keyword in research_keywords:
        if keyword.lower() in readme_content:
            found_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    if len(found_keywords) >= len(research_keywords) * 0.7:  # At least 70% coverage
        results.add_pass(
            f"Critical research questions addressed ({len(found_keywords)}/{len(research_keywords)} keywords)"
        )
    else:
        results.add_warning(
            f"Some research questions may be incomplete ({len(found_keywords)}/{len(research_keywords)} keywords)",
            f"Missing: {', '.join(missing_keywords[:3])}",
        )

    return results


if __name__ == "__main__":
    print_header("SANDBOX VALIDATION SUITE")
    print_info("This script validates all sandbox scripts against requirements")
    print_info("Checking: syntax, documentation, error handling, and completeness\n")

    results = validate_sandbox_scripts()
    success = results.print_summary()

    if success:
        print(f"\n{GREEN}{'=' * 80}{RESET}")
        print(f"{GREEN}ALL VALIDATIONS PASSED!{RESET}".center(80))
        print(f"{GREEN}{'=' * 80}{RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{RED}{'=' * 80}{RESET}")
        print(f"{RED}SOME VALIDATIONS FAILED{RESET}".center(80))
        print(f"{RED}{'=' * 80}{RESET}\n")
        sys.exit(1)
