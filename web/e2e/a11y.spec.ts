import AxeBuilder from '@axe-core/playwright';
import {expect, test} from '@playwright/test';
import {installApiMocks} from './helpers/api-mocks';

test.describe('accessibility', () => {
  test('home has no serious axe violations', async ({page}) => {
    await installApiMocks(page);
    await page.goto('/');

    const results = await new AxeBuilder({page})
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    const serious = results.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical');
    expect(serious, JSON.stringify(serious, null, 2)).toHaveLength(0);
  });
});
