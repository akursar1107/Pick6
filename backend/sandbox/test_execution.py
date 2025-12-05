"""
Execution test for all sandbox scripts.

This script attempts to execute each sandbox script to verify:
1. Scripts run without syntax errors
2. Dependency checking works correctly
3. Error handling is graceful
4. Output is properly formatted

Note: This test may fail if sports data libraries are not installed,
but it will verify that the error handling is working correctly.
"""

import subprocess
import sys
from pathlib import Path

# ANSI color codes
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


def test_script_execution(script_path):
    """
    Test execution of a sandbox script.

    Returns:
        tuple: (success: bool, exit_code: int, has_output: bool, error_msg: str)
    """
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
            encoding="utf-8",
            errors="replace",
        )

        # Check if script executed (even if it exited with error due to missing deps)
        has_output = len(result.stdout) > 0 or len(result.stderr) > 0

        # Exit code 1 is acceptable if it's due to missing dependencies
        if result.returncode == 1:
            # Check if it's a graceful dependency error
            output = result.stdout + result.stderr
            if "is not installed" in output or "pip install" in output:
                return (
                    True,
                    result.returncode,
                    has_output,
                    "Missing dependencies (handled gracefully)",
                )

        # Exit code 0 means successful execution
        if result.returncode == 0:
            return True, result.returncode, has_output, None

        # Other exit codes indicate problems
        error_msg = result.stderr[:200] if result.stderr else "Unknown error"
        return False, result.returncode, has_output, error_msg

    except subprocess.TimeoutExpired:
        return False, -1, False, "Script timed out (may be waiting for input)"
    except Exception as e:
        return False, -1, False, str(e)


def main():
    """Main execution test function"""
    print_header("SANDBOX SCRIPT EXECUTION TESTS")
    print_info("Testing that all scripts execute without critical errors")
    print_info("Note: Missing dependencies are acceptable if handled gracefully\n")

    sandbox_dir = Path(__file__).parent
    scripts = [
        "nfl_sandbox.py",
        "nba_sandbox.py",
        "mlb_sandbox.py",
        "nhl_sandbox.py",
        "cfb_sandbox.py",
    ]

    results = {"passed": [], "failed": [], "warnings": []}

    for script in scripts:
        script_path = sandbox_dir / script
        print_info(f"Testing {script}...")

        success, exit_code, has_output, error_msg = test_script_execution(script_path)

        if success:
            if exit_code == 0:
                print_success(f"{script} executed successfully")
                results["passed"].append(script)
            else:
                print_warning(f"{script} exited with code {exit_code}: {error_msg}")
                results["warnings"].append((script, error_msg))
        else:
            print_error(f"{script} failed: {error_msg}")
            results["failed"].append((script, error_msg))

        print()

    # Print summary
    print_header("EXECUTION TEST SUMMARY")
    print(f"Passed: {GREEN}{len(results['passed'])}{RESET}")
    print(f"Warnings: {YELLOW}{len(results['warnings'])}{RESET}")
    print(f"Failed: {RED}{len(results['failed'])}{RESET}\n")

    if results["warnings"]:
        print(f"{YELLOW}Warnings (acceptable if dependencies missing):{RESET}")
        for script, msg in results["warnings"]:
            print(f"  - {script}: {msg}")
        print()

    if results["failed"]:
        print(f"{RED}Failed (critical errors):{RESET}")
        for script, msg in results["failed"]:
            print(f"  - {script}: {msg}")
        print()
        return False

    print(f"{GREEN}All scripts execute without critical errors!{RESET}")
    print(
        f"{YELLOW}Note: Some scripts may require library installation to run fully{RESET}\n"
    )
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
