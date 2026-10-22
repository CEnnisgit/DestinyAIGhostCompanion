import { test, expect } from '@playwright/test';

test('loads, persists Settings, and reports invalid credentials', async ({ page }) => {
  await page.route('**/*', async route => {
    const path = new URL(route.request().url()).pathname;
    const replies = {
      '/config': {mode: 'hosted', keyring_available: false},
      '/health': {ok: true}, '/auth/status': {authenticated: false, api_key_ok: true},
      '/models': {ollama: []}, '/personas': {personas: ['destiny_ghost']},
      '/voices': {voices: []}, '/diagnostics/audio': {},
      '/ai/test': {ok: false, error: 'AI request failed; check provider, model and credentials'},
    };
    if (path in replies) return route.fulfill({json: replies[path]});
    if (path.startsWith('/stt')) return route.fulfill({json: {ok: false}});
    return route.continue();
  });
  await page.goto('/');
  await expect(page.getByRole('main', {name: 'Empty state'})).toBeVisible();
  await page.getByRole('button', {name: 'Settings', exact: true}).click();
  await page.getByLabel('AI provider').selectOption('openai');
  await page.getByLabel('AI API key').fill('bad-key');
  await page.getByLabel('Model', {exact: true}).fill('test-model');
  await page.reload();
  await page.getByRole('button', {name: 'Settings', exact: true}).click();
  await expect(page.getByLabel('AI API key')).toHaveValue('bad-key');
  await expect(page.getByLabel('Model', {exact: true})).toHaveValue('test-model');
  await page.getByRole('button', {name: 'Test connection'}).click();
  await expect(page.getByRole('status')).toContainText('AI request failed');
});
