// Automated UI tests for the TempSafe prototype (see docs/testing/browser-test-plan.md).
const { test, expect } = require('@playwright/test');
const path = require('path');

const page_ = (name) => 'file://' + path.resolve(__dirname, '..', name);

test('BT-01 sign-in fields have labels', async ({ page }) => {
  await page.goto(page_('login.html'));
  await expect(page.getByLabel('Email or username')).toBeVisible();
  await expect(page.getByLabel('Password')).toBeVisible();
});

test('BT-02 wrong password shows a generic error', async ({ page }) => {
  await page.goto(page_('login.html'));
  await page.getByLabel('Email or username').fill('paramedic');
  await page.getByLabel('Password').fill('wrong');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('alert')).toContainText('Sign-in failed');
  await expect(page).toHaveURL(/login\.html/);
});

test('BT-03 valid sign-in opens the current status page', async ({ page }) => {
  await page.goto(page_('login.html'));
  await page.getByLabel('Email or username').fill('paramedic');
  await page.getByLabel('Password').fill('demo');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/dashboard\.html/);
});

test('BT-04 current status shows value, unit and observation time', async ({ page }) => {
  await page.goto(page_('dashboard.html?state=warning'));
  await expect(page.getByText('24.6°C')).toBeVisible();
  await expect(page.getByText(/Observed 14:17:30/)).toBeVisible();
});

for (const [state, heading] of [['normal', 'NORMAL'], ['warning', 'WARNING'], ['alert', 'ALERT']]) {
  test(`BT-05 ${state} state has a text label`, async ({ page }) => {
    await page.goto(page_(`dashboard.html?state=${state}`));
    await expect(page.getByRole('heading', { name: heading })).toBeVisible();
  });
}

for (const state of ['stale', 'sensor', 'offline']) {
  test(`BT-06 ${state} state never shows Normal`, async ({ page }) => {
    await page.goto(page_(`dashboard.html?state=${state}`));
    await expect(page.getByText('NORMAL', { exact: true })).toHaveCount(0);
  });
}

test('BT-07 account without a box sees no data', async ({ page }) => {
  await page.goto(page_('dashboard.html?state=denied'));
  await expect(page.getByText('No assigned box available')).toBeVisible();
  await expect(page.getByText(/°C/)).toHaveCount(0);
});

test('BT-08 keyboard-only sign-in', async ({ page }) => {
  await page.goto(page_('login.html'));
  await page.keyboard.press('Tab');
  await page.keyboard.type('paramedic');
  await page.keyboard.press('Tab');
  await page.keyboard.type('demo');
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/dashboard\.html/);
});

test('BT-09 history rejects From after To', async ({ page }) => {
  await page.goto(page_('history.html'));
  await page.getByLabel('From').fill('14:30');
  await page.getByLabel('To').fill('14:10');
  await page.getByRole('button', { name: 'Apply' }).click();
  await expect(page.getByText('The start time must be before the end time.')).toBeVisible();
});

test('BT-10 history table lists every reading', async ({ page }) => {
  await page.goto(page_('history.html'));
  await expect(page.locator('#rows tr')).toHaveCount(81);
  await expect(page.getByText('Missing (device offline)').first()).toBeVisible();
});

test('BT-11 empty range shows a message', async ({ page }) => {
  await page.goto(page_('history.html'));
  await page.getByLabel('From').fill('14:50');
  await page.getByLabel('To').fill('14:55');
  await page.getByRole('button', { name: 'Apply' }).click();
  await expect(page.getByText('No observations found for this period.')).toBeVisible();
});

test('BT-12 no horizontal scroll at 320 px', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 640 });
  await page.goto(page_('dashboard.html?state=warning'));
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  expect(overflow).toBe(false);
});
