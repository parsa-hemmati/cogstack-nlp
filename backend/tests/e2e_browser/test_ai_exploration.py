"""
AI-driven exploratory E2E tests using browser-use library.

These tests use Claude to autonomously explore the MedCAT Trainer application UI,
discovering edge cases and issues that scripted tests might miss.

Requirements:
- ANTHROPIC_API_KEY environment variable must be set
- Docker services must be running (medcat-trainer at localhost:8001)
- Run with: pytest tests/e2e_browser/ -v
"""
import pytest
from browser_use import Agent


@pytest.mark.asyncio
async def test_login_page_exploration(llm, base_url):
    """
    AI explores the MedCAT Trainer login page, testing:
    - Login form presence and behavior
    - Input field validation
    - Error message display
    """
    task = f"""
    Navigate to {base_url}

    Explore the MedCAT Trainer login/home page:

    1. PAGE LOAD:
       - Verify the page loads successfully
       - Look for the MedCATTrainer title or branding
       - Note the overall layout and structure

    2. LOGIN FORM (if present):
       - Find username/email input field
       - Find password input field
       - Find login/submit button
       - Try entering test credentials (test/test)
       - Observe the response or error messages

    3. NAVIGATION:
       - Look for any navigation elements (menu, links)
       - Check for signup/register option if available
       - Look for help or documentation links

    4. RESPONSIVE ELEMENTS:
       - Note any interactive elements on the page
       - Check for loading indicators
       - Observe any animations or transitions

    Report your findings including:
    - What UI elements are present
    - Any usability issues discovered
    - Accessibility observations
    - Suggestions for improvement
    """

    agent = Agent(task=task, llm=llm)
    result = await agent.run()

    # Basic validation - AI should complete without critical errors
    result_lower = result.lower() if result else ""
    assert "crash" not in result_lower, f"Browser crashed: {result}"
    assert "fatal error" not in result_lower, f"Fatal error: {result}"

    # Log AI findings for review
    print(f"\n{'='*60}")
    print("AI LOGIN PAGE EXPLORATION FINDINGS:")
    print(f"{'='*60}")
    print(result)
    print(f"{'='*60}\n")


@pytest.mark.asyncio
async def test_navigation_exploration(llm, base_url):
    """
    AI explores the MedCAT Trainer navigation structure, testing:
    - Menu items and navigation paths
    - Page transitions
    - Breadcrumb functionality
    """
    task = f"""
    Navigate to {base_url}

    Explore the navigation structure of MedCAT Trainer:

    1. MAIN NAVIGATION:
       - Identify the main navigation menu
       - List all visible menu items
       - Note which items are clickable

    2. EXPLORE PAGES:
       - Click on different navigation items
       - Observe page transitions
       - Note any loading states

    3. SUB-NAVIGATION:
       - Look for any sub-menus or dropdowns
       - Explore nested navigation options
       - Check for breadcrumb navigation

    4. URL PATTERNS:
       - Note the URL structure as you navigate
       - Check for clean, readable URLs
       - Verify back/forward browser buttons work

    5. RESPONSIVENESS:
       - Check how navigation behaves
       - Look for mobile menu indicators
       - Test keyboard navigation (Tab key)

    Report your findings including:
    - Complete navigation map
    - Any broken or non-functional links
    - Navigation usability issues
    - Suggestions for improvement
    """

    agent = Agent(task=task, llm=llm)
    result = await agent.run()

    result_lower = result.lower() if result else ""
    assert "crash" not in result_lower, f"Browser crashed: {result}"

    print(f"\n{'='*60}")
    print("AI NAVIGATION EXPLORATION FINDINGS:")
    print(f"{'='*60}")
    print(result)
    print(f"{'='*60}\n")


@pytest.mark.asyncio
async def test_ui_components_exploration(llm, base_url):
    """
    AI explores UI components looking for:
    - Form elements and validation
    - Buttons and interactive elements
    - Modal dialogs and popups
    - Data display components
    """
    task = f"""
    Navigate to {base_url}

    Perform a comprehensive UI component audit:

    1. FORM ELEMENTS:
       - Find all input fields (text, password, etc.)
       - Look for dropdown/select elements
       - Find checkboxes and radio buttons
       - Check for form validation messages

    2. BUTTONS AND ACTIONS:
       - Identify all buttons on the page
       - Note button states (enabled, disabled, loading)
       - Check hover effects and click feedback
       - Look for icon buttons

    3. MODALS AND DIALOGS:
       - Try to trigger any modal dialogs
       - Check dialog close mechanisms (X button, Escape key)
       - Verify modal backdrop behavior

    4. DATA DISPLAYS:
       - Look for tables or data grids
       - Find any charts or visualizations
       - Check loading states for data
       - Look for empty states

    5. FEEDBACK ELEMENTS:
       - Find any notification/toast messages
       - Look for progress indicators
       - Check for error message displays
       - Find success confirmations

    Report your findings including:
    - Inventory of UI components found
    - Component interaction issues
    - Missing or incomplete functionality
    - UI/UX improvement suggestions
    """

    agent = Agent(task=task, llm=llm)
    result = await agent.run()

    result_lower = result.lower() if result else ""
    assert "crash" not in result_lower, f"Browser crashed: {result}"

    print(f"\n{'='*60}")
    print("AI UI COMPONENTS EXPLORATION FINDINGS:")
    print(f"{'='*60}")
    print(result)
    print(f"{'='*60}\n")


@pytest.mark.asyncio
async def test_accessibility_exploration(llm, base_url):
    """
    AI specifically tests accessibility features across the application.
    """
    task = f"""
    Navigate to {base_url}

    Perform a comprehensive accessibility audit:

    1. KEYBOARD NAVIGATION:
       - Start at the page top
       - Press Tab repeatedly to navigate through all interactive elements
       - Note any elements that can't be reached via keyboard
       - Check that focus indicators are visible

    2. FOCUS MANAGEMENT:
       - Verify focus order is logical
       - Check focus is visible on all interactive elements
       - Look for any focus traps

    3. SCREEN READER HINTS:
       - Look for aria-label attributes on buttons/icons
       - Check for aria-live regions for dynamic content
       - Verify form inputs have associated labels
       - Check for alt text on images

    4. COLOR & CONTRAST:
       - Look for any text that might be hard to read
       - Check button states (disabled, hover, active)
       - Note any information conveyed only by color

    5. SEMANTIC STRUCTURE:
       - Check for proper heading hierarchy (h1, h2, etc.)
       - Look for landmark regions (header, main, footer)
       - Verify lists are properly marked up

    Report your accessibility findings including:
    - WCAG violations discovered
    - Missing accessibility features
    - Good accessibility practices observed
    - Priority recommendations for fixes
    """

    agent = Agent(task=task, llm=llm)
    result = await agent.run()

    result_lower = result.lower() if result else ""
    assert "crash" not in result_lower, f"Browser crashed: {result}"

    print(f"\n{'='*60}")
    print("AI ACCESSIBILITY EXPLORATION FINDINGS:")
    print(f"{'='*60}")
    print(result)
    print(f"{'='*60}\n")
