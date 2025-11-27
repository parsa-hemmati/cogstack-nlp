"""
AI-driven exploratory E2E tests using browser-use library.

These tests use Claude to autonomously explore the application UI,
discovering edge cases and issues that scripted tests might miss.

Requirements:
- ANTHROPIC_API_KEY environment variable must be set
- Docker services must be running (frontend at localhost:8080)
- Run with: pytest tests/e2e_browser/ -v
"""
import pytest
from browser_use import Agent


@pytest.mark.asyncio
async def test_timeline_exploration(llm, base_url, test_patient_id):
    """
    AI explores the patient timeline view, testing:
    - Zoom controls (in, out, reset)
    - Pan/drag functionality
    - Concept marker interactions
    - Keyboard navigation
    """
    task = f"""
    Navigate to {base_url}/timeline/{test_patient_id}

    Explore the patient timeline interface:

    1. ZOOM CONTROLS:
       - Find and click the zoom in button multiple times
       - Find and click the zoom out button multiple times
       - Find and click the reset/fit button
       - Verify the timeline scale changes appropriately

    2. PAN/NAVIGATION:
       - Try dragging the timeline left and right
       - Use arrow keys if available
       - Verify the visible date range updates

    3. CONCEPT MARKERS:
       - Click on different colored markers on the timeline
       - Verify a popover or detail panel appears
       - Check that concept information is displayed

    4. KEYBOARD ACCESSIBILITY:
       - Press Tab to navigate through controls
       - Press Enter to activate focused elements
       - Press Escape to close any open dialogs

    Report your findings including:
    - What worked correctly
    - Any UI issues or bugs discovered
    - Accessibility problems
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
    print("AI TIMELINE EXPLORATION FINDINGS:")
    print(f"{'='*60}")
    print(result)
    print(f"{'='*60}\n")


@pytest.mark.asyncio
async def test_search_flow_exploration(llm, base_url):
    """
    AI explores the patient search functionality, testing:
    - Search input behavior
    - Filter interactions
    - Result display
    - Navigation to patient details
    """
    task = f"""
    Navigate to {base_url}/search

    Explore the patient search functionality:

    1. SEARCH INPUT:
       - Find the search input field
       - Type a medical term like "diabetes" or "hypertension"
       - Observe autocomplete suggestions if any

    2. FILTERS:
       - Look for filter options (meta-annotations, date range, etc.)
       - Toggle available filters
       - Verify filters affect search results

    3. EXECUTE SEARCH:
       - Submit the search
       - Wait for results to load
       - Verify patient cards/rows appear

    4. RESULT INTERACTION:
       - Click on a patient result
       - Verify navigation to patient detail or timeline
       - Check that patient information is displayed

    5. EMPTY/ERROR STATES:
       - Search for something unlikely to have results
       - Verify appropriate empty state message
       - Test invalid input handling

    Report your findings including:
    - Search workflow completeness
    - UI responsiveness
    - Error handling quality
    - Accessibility of search features
    """

    agent = Agent(task=task, llm=llm)
    result = await agent.run()

    result_lower = result.lower() if result else ""
    assert "crash" not in result_lower, f"Browser crashed: {result}"

    print(f"\n{'='*60}")
    print("AI SEARCH FLOW EXPLORATION FINDINGS:")
    print(f"{'='*60}")
    print(result)
    print(f"{'='*60}\n")


@pytest.mark.asyncio
async def test_export_workflow_exploration(llm, base_url, test_patient_id):
    """
    AI explores the export functionality, testing:
    - Export button locations
    - Format selection
    - Download behavior
    - Export content verification
    """
    task = f"""
    Navigate to {base_url}/timeline/{test_patient_id}

    Explore the export functionality:

    1. FIND EXPORT OPTIONS:
       - Look for an export button, toolbar, or menu
       - Identify available export formats (CSV, JSON, PDF, FHIR)

    2. TEST CSV EXPORT:
       - Click on CSV export option
       - Verify a download starts or dialog appears
       - Note the filename format

    3. TEST JSON EXPORT:
       - Click on JSON export option
       - Verify download behavior
       - Note any differences from CSV

    4. TEST PDF EXPORT (if available):
       - Click on PDF export
       - This may take longer - wait for generation
       - Verify PDF downloads

    5. TEST FHIR EXPORT (if available):
       - Look for FHIR R4 export option
       - Test the export
       - Note the format

    6. EXPORT SETTINGS:
       - Look for any export configuration options
       - Test de-identification toggle if present
       - Test date range selection if present

    Report your findings including:
    - Available export formats
    - Export workflow usability
    - Any failures or timeouts
    - Missing features or suggestions
    """

    agent = Agent(task=task, llm=llm)
    result = await agent.run()

    result_lower = result.lower() if result else ""
    assert "crash" not in result_lower, f"Browser crashed: {result}"

    print(f"\n{'='*60}")
    print("AI EXPORT WORKFLOW EXPLORATION FINDINGS:")
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
       - Open any dialogs/modals using keyboard
       - Verify focus is trapped inside the modal
       - Press Escape to close - verify focus returns appropriately

    3. SCREEN READER HINTS:
       - Look for aria-label attributes on buttons/icons
       - Check for aria-live regions for dynamic content
       - Verify form inputs have associated labels

    4. COLOR & CONTRAST:
       - Look for any text that might be hard to read
       - Check button states (disabled, hover, active)
       - Note any information conveyed only by color

    5. RESPONSIVE BEHAVIOR:
       - If possible, check mobile viewport behavior
       - Verify touch targets are large enough
       - Check text scaling

    Navigate to at least these pages:
    - Home page
    - Search page
    - Timeline page (if accessible)

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
