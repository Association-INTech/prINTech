import { test, expect } from '@playwright/test';

test.describe('User Profile & Security', () => {
  test.beforeEach(async ({ page }) => {
    // Inject valid localStorage entries matching your AuthService keys precisely
    await page.addInitScript(() => {
      const futureJwt = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyBleHAiOjQxMDI0NDQ4MDAsInVzZXJfaWQiOjF9.signature';
      localStorage.setItem('access_token', futureJwt);
      localStorage.setItem('refresh_token', 'mock-refresh-token');
      localStorage.setItem('current_user', JSON.stringify({
        id: 1,
        email: 'testuser@example.com',
        is_staff: false
      }));
    });

    // Intercept the HTTP profile fetch initialized by profile component hooks or interceptors
    await page.route('**/api/v1/user/me/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          email: 'testuser@example.com',
          is_staff: false
        })
      });
    });

    // Mock the password change endpoint response
    await page.route('**/api/v1/user/change-password/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Password updated successfully' })
      });
    });

    await page.goto('/profile');
  });

  test('should display current user details correctly', async ({ page }) => {
    const emailText = page.getByText('testuser@example.com');
    await expect(emailText).toBeVisible();
  });

  test('should change password successfully', async ({ page }) => {
    // This button will now successfully show because user info initializes correctly
    await page.getByRole('button', { name: 'Modifier le mot de passe' }).click();

    // Fill out the modal fields
    await page.getByLabel('Ancien mot de passe').fill('CorrectPassword123!');
    await page.getByLabel('Nouveau mot de passe').fill('NewSecurePassword123!');
    await page.getByLabel('Confirmer le nouveau mot de passe').fill('NewSecurePassword123!');

    // Target the correct submit button label
    await page.getByRole('button', { name: 'Enregistrer' }).click();

    // Confirm the modal closes
    await expect(page.getByLabel('Ancien mot de passe')).not.toBeVisible();
  });
});