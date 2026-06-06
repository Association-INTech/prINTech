import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the login page before each test
    await page.goto('/login');
  });

  test('should successfully log in with valid credentials', async ({ page }) => {
    // Fill in the login form
    await page.getByLabel('Email').fill('testuser@example.com');
    await page.getByLabel('Password').fill('CorrectPassword123!');
    
    // Intercept the login API request to ensure it behaves correctly (or mock it if running isolated tests)
    const loginPromise = page.waitForResponse(response => 
      response.url().includes('/user/login/') && response.status() === 200
    );

    // Click the submit button
    await page.getByRole('button', { name: /log in|submit/i }).click();

    // Wait for the login network response
    await loginPromise;

    // Verify redirection to the main/dashboard page
    await expect(page).toHaveURL(/\/dashboard|\/home|^\/$/);

    // Verify localStorage has tokens set by your AuthService
    const accessToken = await page.evaluate(() => localStorage.getItem('access_token')); // match your AuthService key
    const refreshToken = await page.evaluate(() => localStorage.getItem('refresh_token'));
    
    expect(accessToken).toBeTruthy();
    expect(refreshToken).toBeTruthy();
  });

  test('should display error message on invalid login', async ({ page }) => {
    await page.getByLabel('Email').fill('wrong@example.com');
    await page.getByLabel('Password').fill('WrongPassword!');
    
    await page.getByRole('button', { name: /log in|submit/i }).click();

    // Verify an error message or alert appears on screen
    const errorAlert = page.locator('.error-message, [role="alert"]');
    await expect(errorAlert).toBeVisible();
    await expect(errorAlert).toContainText(/invalid/i);
  });
});