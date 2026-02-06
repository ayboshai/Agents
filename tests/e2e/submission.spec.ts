import { expect, test } from '@playwright/test';

const validLead = {
  name: 'Иван Петров',
  phone: '+7 (965) 990-31-60',
  message: 'Нужна автоматизация процессов склада и интеграция с маркетплейсами.',
};

test.describe('No-LARP hardening', () => {
  test('submission flow triggers POST /api/leads and shows visible success state', async ({ page }) => {
    await page.goto('/');

    const submitRequestPromise = page.waitForRequest(
      (request) => request.url().includes('/api/leads') && request.method() === 'POST',
    );

    // Verify labels are localized (Centralization check)
    await page.getByLabel('Имя').fill(validLead.name);
    await page.getByLabel('Телефон').fill(validLead.phone);
    await page.getByLabel('Сообщение').fill(validLead.message);
    await page.locator('form').getByRole('button', { name: 'Оставить заявку' }).click();

    const submitRequest = await submitRequestPromise;
    const payload = submitRequest.postDataJSON() as Record<string, string>;

    expect(payload).toMatchObject({
      name: validLead.name,
      phone: validLead.phone,
      message: validLead.message,
    });

    const submitResponse = await submitRequest.response();
    expect(submitResponse, 'POST /api/leads must resolve via real API handler').not.toBeNull();
    expect(submitResponse?.status()).toBeGreaterThanOrEqual(200);
    expect(submitResponse?.status()).toBeLessThan(300);

    await expect(
      page.getByText(/заявка (отправлена|принята|успешно)/i),
      'User must see a success state after submission',
    ).toBeVisible();
  });

  test('empty required fields expose ARIA-compliant validation errors', async ({ page }) => {
    await page.goto('/');
    await page.locator('form').getByRole('button', { name: 'Оставить заявку' }).click();

    const nameInput = page.getByLabel('Имя');
    const phoneInput = page.getByLabel('Телефон');
    const messageInput = page.getByLabel('Сообщение');

    await expect(nameInput).toHaveAttribute('aria-invalid', 'true');
    await expect(phoneInput).toHaveAttribute('aria-invalid', 'true');
    await expect(messageInput).toHaveAttribute('aria-invalid', 'true');

    // Check for the summary alert (filter out Next.js route announcer)
    await expect(
      page.getByRole('alert').filter({ hasText: /имя|телефон|сообщение/i })
    ).toBeVisible();
  });

  test('home page exports required SEO tags', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveTitle(/.+/);

    const description = page.locator('meta[name="description"]');
    await expect(description).toHaveCount(1);
    await expect(description).toHaveAttribute('content', /.+/);

    const ogTitle = page.locator('meta[property="og:title"]');
    const ogDescription = page.locator('meta[property="og:description"]');

    await expect(ogTitle).toHaveCount(1);
    await expect(ogTitle).toHaveAttribute('content', /.+/);
    await expect(ogDescription).toHaveCount(1);
    await expect(ogDescription).toHaveAttribute('content', /.+/);
  });

  test('unknown case slug returns 404 and shows friendly not-found page', async ({ page }) => {
    const response = await page.goto('/cases/fake-slug');

    expect(response?.status()).toBe(404);
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/(404|not found|не найдено)/i);
  });
});
