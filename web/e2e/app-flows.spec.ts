import {expect, test} from '@playwright/test';
import {installApiMocks} from './helpers/api-mocks';

test.describe('app flows (mocked API)', () => {
  test.beforeEach(async ({page}) => {
    await installApiMocks(page);
  });

  test('switches between Transfers, History and Queue, Analytics, and Logs & Terminal via primary nav', async ({page}) => {
    await page.setViewportSize({width: 1280, height: 720});
    await page.goto('/');

    const primary = page.getByRole('navigation', {name: 'Primary'});
    await expect(primary.getByRole('button', {name: 'Analytics'})).toBeVisible();
    await primary.getByRole('button', {name: 'History and Queue'}).click();
    await expect(page.getByRole('heading', {name: 'History and Queue Management'})).toBeVisible();
    await expect(page.getByPlaceholder('Paste MEGA.nz export link here…')).toHaveCount(0);

    await primary.getByRole('button', {name: 'Analytics'}).click();
    await expect(page.getByText('Total downloaded')).toBeVisible();

    await primary.getByRole('button', {name: 'Logs & Terminal'}).click();
    await expect(page.getByRole('tab', {name: /System log/i})).toBeVisible();

    await primary.getByRole('button', {name: 'Transfers'}).click();
    await expect(page.getByPlaceholder('Paste MEGA.nz export link here…')).toBeVisible();
  });

  test('hash #/system/terminal opens MEGA Terminal', async ({page}) => {
    await page.setViewportSize({width: 1280, height: 720});
    await page.goto('/#/system/terminal');
    await expect(page.getByPlaceholder('Enter MEGAcmd command...')).toBeVisible();
  });

  test('primary nav uses bottom bar on narrow viewport', async ({page}) => {
    await page.setViewportSize({width: 390, height: 844});
    await page.goto('/');

    const primary = page.getByRole('navigation', {name: 'Primary'});
    await expect(primary.getByRole('button', {name: 'History and Queue'})).toBeVisible();
    await primary.getByRole('button', {name: 'History and Queue'}).click();
    await expect(page.getByRole('heading', {name: 'History and Queue Management'})).toBeVisible();
  });

  test('opens Settings and shows dialog', async ({page}) => {
    await page.goto('/');
    await page.getByTitle('Settings').click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('heading', {name: 'Advanced Settings'})).toBeVisible();
  });

  test('submits a MEGA URL and shows submitted status', async ({page}) => {
    await page.goto('/');
    await page.getByPlaceholder('Paste MEGA.nz export link here…').fill('https://mega.nz/file/abc');
    await page.getByRole('button', {name: 'Download'}).click();
    await expect(page.getByText(/Last download:\s*submitted/i)).toBeVisible();
  });

  test('add to queue shows saved link in pending panel', async ({page}) => {
    await page.setViewportSize({width: 1280, height: 720});
    await page.goto('/');
    await page.getByPlaceholder('Paste MEGA.nz export link here…').fill('https://mega.nz/file/queued');
    await page.getByRole('button', {name: /add to queue/i}).click();
    await page.getByRole('navigation', {name: 'Primary'}).getByRole('button', {name: 'History and Queue'}).click();
    await expect(page.getByRole('heading', {name: 'History and Queue Management'})).toBeVisible();
    await expect(page.getByTitle('https://mega.nz/file/queued')).toBeVisible();
  });

  test('surfaces error when download API returns 400', async ({page}) => {
    await installApiMocks(page, {downloadShouldFail: true});
    await page.goto('/');
    await page.getByPlaceholder('Paste MEGA.nz export link here…').fill('https://mega.nz/file/abc');
    await page.getByRole('button', {name: 'Download'}).click();
    await expect(page.getByText(/Last download:\s*failed/i)).toBeVisible();
  });
});
