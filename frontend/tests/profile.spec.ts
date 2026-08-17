import { test, expect } from '@playwright/test';

const accessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQxMDI0NDQ4MDAsInVzZXJfaWQiOiIxIn0.signature';

test.describe('User Profile & Security', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/token/refresh/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ access: accessToken })
      });
    });

    await page.route('**/api/v1/user/me/', async (route) => {
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

    await page.route('**/api/v1/user/me/change-password/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Password updated successfully' })
      });
    });

    await page.goto('/profile');
  });

  test('should display current user details correctly', async ({ page }) => {
    await expect(page.getByText('testuser@example.com')).toBeVisible();
    await expect(page.getByText('42')).toBeVisible();
  });

  test('should change password successfully', async ({ page }) => {
    await page.getByRole('button', { name: 'Modifier le mot de passe' }).click();
    await page.getByLabel('Ancien mot de passe').fill('CorrectPassword123!');
    await page.getByLabel('Nouveau mot de passe').fill('NewSecurePassword123!');
    await page.getByLabel('Confirmer le nouveau mot de passe').fill('NewSecurePassword123!');
    await page.getByRole('button', { name: 'Enregistrer' }).click();
    await expect(page.getByLabel('Ancien mot de passe')).not.toBeVisible();
  });
});
