import { expect, test } from '@playwright/test';

test.describe('CMAS-OS template E2E', () => {
  test('home page is reachable', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.status()).toBe(200);

    await expect(page.getByRole('heading', { level: 1 })).toHaveText('CMAS-OS Template');
  });

  test('health endpoint responds OK', async ({ request }) => {
    const res = await request.get('/health');
    expect(res.status()).toBe(200);
    expect(await res.text()).toBe('OK');
  });
});

