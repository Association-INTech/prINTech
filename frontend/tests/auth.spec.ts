import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept API calls to prevent real network requests failing the E2E tests
    await page.route('**/api/v1/token/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQxMDI0NDQ4MDAsInVzZXJfaWQiOiIxIn0.signature',
          refresh: 'mock-refresh-token'
        })
      });
    });

    await page.route('**/api/v1/user/me**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '1',
          username: 'testuser',
          email: 'testuser@example.com',
          credit: 42,
          is_staff: false,
          profile_picture: null
        })
      });
    });

    await page.route('**/api/v1/printers/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.goto('/login');
  });

  test('should successfully log in with valid credentials', async ({ page }) => {
    await page.getByLabel('Adresse e-mail').fill('testuser@example.com');
    await page.getByLabel('Mot de passe').fill('CorrectPassword123!');
    
    // Click the submission button
    await page.getByRole('button', { name: 'Se connecter' }).click();
    
    // Verify successful redirection to home page
    await expect(page).toHaveURL('/');
  });

  test('should display error message on invalid login', async ({ page }) => {
    // Override token route to simulate a 401 Unauthorized response
    await page.unroute('**/api/v1/token/');
    await page.route('**/api/v1/token/', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'No active account found with the given credentials.' })
      });
    });

    await page.getByLabel('Adresse e-mail').fill('wrong@example.com');
    await page.getByLabel('Mot de passe').fill('WrongPassword!');
    await page.getByRole('button', { name: 'Se connecter' }).click();
    
    // Assert against the alert container text
    const errorMessage = page.getByRole('alert');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText('Adresse e-mail ou mot de passe invalide.');
  });
});