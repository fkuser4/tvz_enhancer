import src.tvz_enhancer.main as main
import pytest


def test_main():
    """Test to ensure main.py runs without errors."""
    try:
        main.main()  # Call the main() function directly
    except Exception as e:
        pytest.fail(f"main.py failed to execute: {e}")