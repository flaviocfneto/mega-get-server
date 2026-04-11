import {expect, test} from '@playwright/test';
import {installApiMocks} from './helpers/api-mocks';

test.describe('visual regression', () => {
  test('home shell', async ({page}) => {
    test.setTimeout(60_000);
    await installApiMocks(page);
    await page.goto('/');
    await expect(page.getByRole('button', {name: 'Download'})).toBeVisible();
    await expect(page).toHaveScreenshot('home.png', {
      fullPage: true,
    });
  });
});
