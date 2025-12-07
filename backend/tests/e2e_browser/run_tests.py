#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Standalone runner for browser-use AI tests.
Runs tests without loading the backend app configuration.

Usage:
    python backend/tests/e2e_browser/run_tests.py

Set ANTHROPIC_API_KEY environment variable before running.
"""
import asyncio
import os
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Check for API key
if not os.getenv("ANTHROPIC_API_KEY"):
    print("[WARNING] ANTHROPIC_API_KEY not set - tests will be skipped")
    print("Set it with: export ANTHROPIC_API_KEY=your-api-key")
    sys.exit(0)

print("=" * 60)
print("Browser-Use AI Exploratory Tests")
print("=" * 60)
print(f"Frontend URL: {os.getenv('FRONTEND_URL', 'http://localhost:8001')}")
print(f"API Key: {'Set' if os.getenv('ANTHROPIC_API_KEY') else 'Not set'}")
print("=" * 60)

try:
    from browser_use import Agent
    from langchain_anthropic import ChatAnthropic
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("Install with: pip install browser-use langchain-anthropic")
    sys.exit(1)


def get_llm():
    """Create Anthropic LLM instance."""
    return ChatAnthropic(
        model=os.getenv("BROWSER_USE_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=4096,
        temperature=0
    )


async def test_login_page():
    """Test the login/home page."""
    base_url = os.getenv("FRONTEND_URL", "http://localhost:8001")

    task = f"""
    Navigate to {base_url}

    Explore the MedCAT Trainer login/home page:

    1. Verify the page loads successfully
    2. Look for the MedCATTrainer title or branding
    3. Find any login form elements
    4. Note any navigation elements
    5. Check for accessibility issues

    Report your findings briefly.
    """

    print("\n[TEST] Running: Login Page Exploration")
    agent = Agent(task=task, llm=get_llm())
    result = await agent.run()

    print("\n[RESULTS]:")
    print(result)
    return result


async def test_navigation():
    """Test the navigation structure."""
    base_url = os.getenv("FRONTEND_URL", "http://localhost:8001")

    task = f"""
    Navigate to {base_url}

    Explore the navigation:

    1. Identify all menu items
    2. Try clicking on different pages
    3. Note the URL structure
    4. Check for breadcrumbs

    Report your findings briefly.
    """

    print("\n[TEST] Running: Navigation Exploration")
    agent = Agent(task=task, llm=get_llm())
    result = await agent.run()

    print("\n[RESULTS]:")
    print(result)
    return result


async def main():
    """Run all tests."""
    print("\n[START] Starting AI Exploratory Tests...\n")

    tests = [
        ("Login Page", test_login_page),
        ("Navigation", test_navigation),
    ]

    results = {}
    for name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            print(f"Test: {name}")
            print("=" * 60)
            result = await test_func()
            results[name] = {"status": "PASS", "result": result}
        except Exception as e:
            print(f"[ERROR] {e}")
            results[name] = {"status": "FAIL", "error": str(e)}

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, data in results.items():
        status = "[PASS]" if data["status"] == "PASS" else "[FAIL]"
        print(f"{status} - {name}")

    print("\n" + "=" * 60)
    passed = sum(1 for d in results.values() if d["status"] == "PASS")
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
