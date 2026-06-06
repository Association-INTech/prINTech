import { test, expect } from '@playwright/test';

test.describe('User Profile & Security', () => {
  
  test.beforeEach(async ({ page }) => {
    // This will already be authenticated thanks to storageState configuration
    await page.goto('/profile');
  });

  test('should display current user details correctly', async ({ page }) => {
    // Assert user profile information fetched from /user/me/ is rendered
    const emailField = page.locator('#profile-email');
    await expect(emailField).toContainText('testuser@example.com');
  });

  test('should change password successfully', async ({ page }) => {
    // Navigate to change password view or open modal
    await page.getByRole('button', { name: /change password/i }).click();

    // Fill the inputs matching ChangePasswordRequest interface
    await page.getByLabel('Old Password').fill('CorrectPassword123!');
    await page.getByLabel('New Password').fill('BrandNewPassword2026!');
    await page.getByLabel('Confirm Password').fill('BrandNewPassword2026!');

    // Intercept response matching ChangePasswordResponse
    const changePwdPromise = page.waitForResponse(response =>
      response.url().includes('/change-password') && response.status() === 200
    );

    await page.getByRole('button', { name: /update password|save/i }).click();

    const response = await changePwdPromise;
    const responseBody = await response.json();
    
    // Assert feedback message is shown
    expect(responseBody.message).toBeTruthy();
    await expect(page.getByText(/password updated successfully|success/i)).toBeVisible();
  });
});