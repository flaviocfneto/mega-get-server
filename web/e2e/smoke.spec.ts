import {expect, test} from '@playwright/test';
import {installApiMocks} from './helpers/api-mocks';

test.beforeEach(async ({page}) => {
  await installApiMocks(page);
});

test('smoke: app loads and exposes main controls', async ({page}) => {
  await page.goto('/');

  await expect(page.getByRole('button', {name: 'Download'})).toBeVisible();
  await expect(page.getByRole('button', {name: 'Analytics'})).toBeVisible();
  await expect(page.getByTitle('Settings')).toBeVisible();
});
