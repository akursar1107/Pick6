"""
Common utilities for sports data sandbox scripts.

This module provides shared helper functions used across all sandbox scripts
for dependency checking, data display, error handling, and output formatting.
"""

import sys
from typing import Any, Optional
import pandas as pd


def check_library_installed(library_name: str, install_command: str) -> bool:
    """
    Check if a required library is installed.

    If the library is not installed, displays installation instructions
    and returns False. This allows scripts to gracefully handle missing
    dependencies without exposing stack traces.

    Args:
        library_name: Name of the library to check (e.g., 'nflreadpy')
        install_command: pip install command (e.g., 'pip install nflreadpy')

    Returns:
        bool: True if library is installed, False otherwise

    Example:
        if not check_library_installed('nflreadpy', 'pip install nflreadpy'):
            sys.exit(1)
    """
    try:
        __import__(library_name)
        return True
    except ImportError:
        print(f"\n{'='*70}")
        print(f"ERROR: {library_name} is not installed")
        print(f"{'='*70}")
        print(f"\nTo install this library, run:")
        print(f"  {install_command}")
        print(f"\nOr install all sandbox dependencies:")
        print(f"  pip install -r backend/requirements.txt")
        print(f"\n{'='*70}\n")
        return False


def display_dataframe_sample(
    df: pd.DataFrame, title: str, max_rows: int = 5, columns: Optional[list] = None
) -> None:
    """
    Display a formatted sample of a pandas DataFrame.

    Provides consistent, readable output across all sandbox scripts with
    section headers, row counts, and optional column filtering.

    Args:
        df: pandas DataFrame to display
        title: Descriptive title for the data being displayed
        max_rows: Maximum number of rows to display (default: 5)
        columns: Optional list of specific columns to display (default: all)

    Example:
        display_dataframe_sample(games_df, "NFL Games - Week 1", max_rows=10)
    """
    print_section_header(title)

    if df is None or df.empty:
        print("⚠️  No data available")
        print()
        return

    print(f"📊 Total records: {len(df)}")
    print()

    # Select specific columns if provided
    display_df = df[columns] if columns else df

    # Display sample rows
    if len(df) <= max_rows:
        print(display_df.to_string(index=False))
    else:
        print(f"Showing first {max_rows} of {len(df)} records:")
        print()
        print(display_df.head(max_rows).to_string(index=False))

    print()


def handle_api_error(error: Exception, context: str) -> None:
    """
    Standardized error handling and display for API failures.

    Provides informative error messages without exposing full stack traces,
    helping developers understand what went wrong and potential solutions.

    Args:
        error: The exception that was raised
        context: Description of what operation failed (e.g., "fetching NFL games")

    Example:
        try:
            data = api.get_games()
        except Exception as e:
            handle_api_error(e, "fetching NFL games")
    """
    print(f"\n{'='*70}")
    print(f"❌ ERROR: Failed while {context}")
    print(f"{'='*70}")
    print(f"\nError Type: {type(error).__name__}")
    print(f"Error Details: {str(error)}")
    print(f"\nPossible causes:")
    print(f"  • API rate limits or throttling")
    print(f"  • Network connectivity issues")
    print(f"  • Invalid parameters or query")
    print(f"  • API service temporarily unavailable")
    print(f"  • Authentication or permission issues")
    print(f"\nTroubleshooting:")
    print(f"  • Check your internet connection")
    print(f"  • Verify API parameters are correct")
    print(f"  • Try again in a few moments")
    print(f"  • Check library documentation for API changes")
    print(f"\n{'='*70}\n")


def print_section_header(title: str, width: int = 70) -> None:
    """
    Print a formatted section header for output organization.

    Creates visually distinct sections in script output to improve
    readability when exploring multiple data sources or operations.

    Args:
        title: Section title to display
        width: Total width of the header (default: 70)

    Example:
        print_section_header("Game Data Retrieval")
    """
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)
    print()


def validate_dataframe_response(
    df: pd.DataFrame, operation: str, min_rows: int = 1
) -> bool:
    """
    Validate that a DataFrame response contains expected data.

    Helper function to check if API responses are valid and contain
    sufficient data before processing.

    Args:
        df: DataFrame to validate
        operation: Description of the operation (for error messages)
        min_rows: Minimum expected number of rows (default: 1)

    Returns:
        bool: True if DataFrame is valid, False otherwise

    Example:
        if not validate_dataframe_response(games_df, "game retrieval"):
            return
    """
    if df is None:
        print(f"⚠️  Warning: {operation} returned None")
        print("   This may indicate an API error or invalid parameters")
        print()
        return False

    if df.empty:
        print(f"⚠️  Warning: {operation} returned no data")
        print("   This may indicate:")
        print("   • No games scheduled for the specified period")
        print("   • Invalid query parameters")
        print("   • Data not yet available")
        print()
        return False

    if len(df) < min_rows:
        print(f"⚠️  Warning: {operation} returned only {len(df)} row(s)")
        print(f"   Expected at least {min_rows} row(s)")
        print()
        return False

    return True


def print_data_structure_info(df: pd.DataFrame, title: str = "Data Structure") -> None:
    """
    Display information about DataFrame structure and columns.

    Useful for exploring new APIs and understanding available data fields.

    Args:
        df: DataFrame to analyze
        title: Title for the structure information section

    Example:
        print_data_structure_info(games_df, "NFL Games Data Structure")
    """
    print_section_header(title)

    if df is None or df.empty:
        print("⚠️  No data available to analyze")
        print()
        return

    print(f"📋 Available columns ({len(df.columns)}):")
    print()

    for col in df.columns:
        dtype = df[col].dtype
        non_null = df[col].notna().sum()
        null_count = df[col].isna().sum()

        print(f"  • {col}")
        print(f"    Type: {dtype}")
        print(f"    Non-null: {non_null}/{len(df)} ({100*non_null/len(df):.1f}%)")

        if null_count > 0:
            print(f"    ⚠️  Null values: {null_count}")

        # Show sample value if available
        sample_val = df[col].dropna().iloc[0] if non_null > 0 else None
        if sample_val is not None:
            sample_str = str(sample_val)
            if len(sample_str) > 50:
                sample_str = sample_str[:47] + "..."
            print(f"    Sample: {sample_str}")

        print()
