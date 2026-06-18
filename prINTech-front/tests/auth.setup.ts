import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('testuser@example.com');
  await page.getByLabel('Password').fill('CorrectPassword123!');
  await page.getByRole('button', { name: /log in/i }).click();

  // Wait for application navigation after login
  await page.waitForURL(/\/dashboard|\/home/);

  // Save storage state (cookies + local storage)
  await page.context().storageState({ path: authFile });
});