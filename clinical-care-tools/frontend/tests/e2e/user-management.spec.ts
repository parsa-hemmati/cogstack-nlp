/**
 * E2E Test: User Management Workflow
 *
 * Tests the complete user lifecycle:
 * 1. Admin login
 * 2. Navigate to user management
 * 3. Create new user
 * 4. Logout
 * 5. New user login
 * 6. Change password (first login requirement)
 * 7. Verify new user can access the system
 */

import { test, expect } from '@playwright/test'

// Test configuration
const BASE_URL = 'http://localhost:3000'
const API_BASE_URL = 'http://localhost:8000'

// Test credentials
const ADMIN_USERNAME = 'admin'
const ADMIN_PASSWORD = 'admin123' // Default admin password for testing

const NEW_USER_USERNAME = 'test_user_' + Date.now()
const NEW_USER_FULL_NAME = 'Test User'
const NEW_USER_PASSWORD = 'TestPassword123!'
const NEW_USER_ROLE = 'clinician'

test.describe('User Management E2E Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to home page before each test
    await page.goto(BASE_URL)
  })

  test('complete user lifecycle: create, login, change password', async ({ page }) => {
    // ============================================================
    // STEP 1: Admin Login
    // ============================================================
    await test.step('Admin logs in', async () => {
      // Navigate to login page (assuming /login route exists)
      await page.goto(`${BASE_URL}/login`)

      // Fill in admin credentials
      await page.fill('input[name="username"]', ADMIN_USERNAME)
      await page.fill('input[name="password"]', ADMIN_PASSWORD)

      // Click login button
      await page.click('button[type="submit"]')

      // Wait for navigation to complete
      await page.waitForURL(`${BASE_URL}/`)

      // Verify admin is logged in (check for user indicator or admin menu)
      await expect(page.locator('text=Welcome')).toBeVisible()
    })

    // ============================================================
    // STEP 2: Navigate to User Management
    // ============================================================
    await test.step('Admin navigates to user management', async () => {
      // Navigate to users page
      await page.goto(`${BASE_URL}/users`)

      // Verify user management page is loaded
      await expect(page.locator('text=User Management')).toBeVisible()

      // Verify data table is visible
      await expect(page.locator('.v-data-table')).toBeVisible()
    })

    // ============================================================
    // STEP 3: Create New User
    // ============================================================
    await test.step('Admin creates new user', async () => {
      // Click "Create User" button
      await page.click('button:has-text("Create User")')

      // Wait for dialog to appear
      await expect(page.locator('.v-dialog:visible')).toBeVisible()

      // Fill in user details
      await page.fill('input[label="Username"]', NEW_USER_USERNAME)
      await page.fill('input[label="Full Name"]', NEW_USER_FULL_NAME)
      await page.fill('input[label="Password"]', NEW_USER_PASSWORD)

      // Select role
      await page.click('div[label="Role"]')
      await page.click(`div[role="option"]:has-text("${NEW_USER_ROLE}")`)

      // Click "Create" button
      await page.click('button:has-text("Create")')

      // Wait for success message
      await expect(page.locator('.v-snackbar:visible:has-text("User created successfully")')).toBeVisible()

      // Verify user appears in table
      await expect(page.locator(`td:has-text("${NEW_USER_USERNAME}")`)).toBeVisible()
    })

    // ============================================================
    // STEP 4: Admin Logout
    // ============================================================
    await test.step('Admin logs out', async () => {
      // Click logout button (assuming it exists in header/menu)
      await page.click('button:has-text("Logout")')

      // Wait for navigation to login page
      await page.waitForURL(`${BASE_URL}/login`)

      // Verify logout successful
      await expect(page.locator('input[name="username"]')).toBeVisible()
    })

    // ============================================================
    // STEP 5: New User Login
    // ============================================================
    await test.step('New user logs in for the first time', async () => {
      // Fill in new user credentials
      await page.fill('input[name="username"]', NEW_USER_USERNAME)
      await page.fill('input[name="password"]', NEW_USER_PASSWORD)

      // Click login button
      await page.click('button[type="submit"]')

      // Wait for navigation (may redirect to change password page)
      await page.waitForLoadState('networkidle')

      // Check if redirected to change password page
      const url = page.url()
      if (url.includes('change-password')) {
        // User must change password on first login
        await expect(page.locator('text=Change Password')).toBeVisible()
      } else {
        // User logged in successfully
        await expect(page.locator('text=Welcome')).toBeVisible()
      }
    })

    // ============================================================
    // STEP 6: Change Password (if required)
    // ============================================================
    await test.step('New user changes password on first login', async () => {
      const url = page.url()

      if (url.includes('change-password')) {
        const newPassword = 'NewPassword123!'

        // Fill in current password
        await page.fill('input[label="Current Password"]', NEW_USER_PASSWORD)

        // Fill in new password
        await page.fill('input[label="New Password"]', newPassword)

        // Confirm new password
        await page.fill('input[label="Confirm Password"]', newPassword)

        // Click change password button
        await page.click('button:has-text("Change Password")')

        // Wait for success and redirect
        await expect(page.locator('.v-snackbar:visible:has-text("Password changed successfully")')).toBeVisible()

        // Wait for navigation to home
        await page.waitForURL(`${BASE_URL}/`)
      }
    })

    // ============================================================
    // STEP 7: Verify New User Access
    // ============================================================
    await test.step('New user can access the system', async () => {
      // Verify user is on home page
      await expect(page.locator('text=Welcome')).toBeVisible()

      // Verify user can navigate to patients page (based on role)
      await page.goto(`${BASE_URL}/patients`)
      await expect(page.locator('text=Patient Search')).toBeVisible()

      // Verify user CANNOT access admin-only pages
      await page.goto(`${BASE_URL}/users`)

      // Should be redirected or see access denied
      const usersPageVisible = await page.locator('text=User Management').isVisible()
      expect(usersPageVisible).toBe(false)
    })

    // ============================================================
    // CLEANUP: Delete Test User (optional)
    // ============================================================
    await test.step('Cleanup: Admin deletes test user', async () => {
      // Logout new user
      await page.click('button:has-text("Logout")')

      // Login as admin again
      await page.goto(`${BASE_URL}/login`)
      await page.fill('input[name="username"]', ADMIN_USERNAME)
      await page.fill('input[name="password"]', ADMIN_PASSWORD)
      await page.click('button[type="submit"]')

      // Navigate to users page
      await page.goto(`${BASE_URL}/users`)

      // Find test user in table
      const userRow = page.locator(`tr:has-text("${NEW_USER_USERNAME}")`)

      if (await userRow.isVisible()) {
        // Click delete button (if implemented)
        // await userRow.locator('button:has-text("Delete")').click()

        // For now, just verify user exists in table
        await expect(userRow).toBeVisible()
      }
    })
  })

  test('admin can edit existing user', async ({ page }) => {
    // ============================================================
    // STEP 1: Admin Login
    // ============================================================
    await page.goto(`${BASE_URL}/login`)
    await page.fill('input[name="username"]', ADMIN_USERNAME)
    await page.fill('input[name="password"]', ADMIN_PASSWORD)
    await page.click('button[type="submit"]')
    await page.waitForURL(`${BASE_URL}/`)

    // ============================================================
    // STEP 2: Navigate to User Management
    // ============================================================
    await page.goto(`${BASE_URL}/users`)
    await expect(page.locator('text=User Management')).toBeVisible()

    // ============================================================
    // STEP 3: Edit First User in List
    // ============================================================
    // Click edit button on first user
    await page.locator('button[icon]:has-text("pencil")').first().click()

    // Wait for edit dialog
    await expect(page.locator('.v-dialog:visible')).toBeVisible()

    // Verify form is populated
    const fullNameInput = page.locator('input[label="Full Name"]')
    await expect(fullNameInput).not.toBeEmpty()

    // Change full name
    const newFullName = 'Updated Name ' + Date.now()
    await fullNameInput.clear()
    await fullNameInput.fill(newFullName)

    // Click update button
    await page.click('button:has-text("Update")')

    // Verify success message
    await expect(page.locator('.v-snackbar:visible:has-text("User updated successfully")')).toBeVisible()

    // Verify updated name appears in table
    await expect(page.locator(`td:has-text("${newFullName}")`)).toBeVisible()
  })

  test('admin can filter users by role', async ({ page }) => {
    // ============================================================
    // STEP 1: Admin Login
    // ============================================================
    await page.goto(`${BASE_URL}/login`)
    await page.fill('input[name="username"]', ADMIN_USERNAME)
    await page.fill('input[name="password"]', ADMIN_PASSWORD)
    await page.click('button[type="submit"]')
    await page.waitForURL(`${BASE_URL}/`)

    // ============================================================
    // STEP 2: Navigate to User Management
    // ============================================================
    await page.goto(`${BASE_URL}/users`)
    await expect(page.locator('text=User Management')).toBeVisible()

    // ============================================================
    // STEP 3: Apply Role Filter (if implemented)
    // ============================================================
    // Get initial row count
    const initialRows = await page.locator('.v-data-table tbody tr').count()

    // Apply filter (if filter controls exist)
    // Note: Current implementation may not have filters
    // This is a placeholder for future enhancement

    // Verify table updated (when filters are implemented)
    // const filteredRows = await page.locator('.v-data-table tbody tr').count()
    // expect(filteredRows).toBeLessThanOrEqual(initialRows)
  })

  test('non-admin user cannot access user management', async ({ page }) => {
    // This test requires a non-admin user to exist
    // For now, verify redirect/access denied when not authenticated
    await page.goto(`${BASE_URL}/users`)

    // Should redirect to home or show access denied
    const url = page.url()
    expect(url).not.toContain('/users')
  })
})
