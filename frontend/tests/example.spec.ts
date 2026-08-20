import { test, expect } from '@playwright/test';

test('redirects anonymous users to login', async ({ page }) => {
  await page.route('**/api/v1/token/refresh/', async (route) => {
    await route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Token is invalid or expired' })
    });
  });

  await page.goto('/');
  await expect(page).toHaveURL(/\/login/);
});
