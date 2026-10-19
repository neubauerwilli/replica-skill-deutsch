// Beispiel einer Playwright-Spec für einen Ablauf. Nach e2e/f01-book.spec.ts kopieren und anpassen.
// Die Selektoren nutzen Rollen und Labels, damit sie ein neues Styling und die Umbenennung überstehen.
// Die Texte in den Selektoren (Buchungs-App auf Deutsch) an die Texte deiner App anpassen.
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('F01 Gast bucht einen Termin', () => {
  test.beforeEach(async ({ page }) => {
    page.on('console', (msg) => {
      if (msg.type() === 'error') throw new Error(`Konsolenfehler: ${msg.text()}`);
    });
    page.on('response', (res) => {
      if (res.status() >= 500) throw new Error(`${res.status()} bei ${res.url()}`);
    });
  });

  test('F01-H1 Idealweg', async ({ page }) => {
    await page.goto('/u/demo/30min');
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.getByRole('button', { name: /nächster freier tag/i }).click();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.getByRole('button', { name: /10:00/ }).click();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.getByLabel('Name').fill('Test Gast');
    await page.getByLabel('E-Mail').fill('gast@example.test');
    await page.getByRole('button', { name: /bestätigen/i }).click();
    await expect(page.getByRole('heading', { name: /du bist gebucht/i })).toBeVisible();

    const a11y = await new AxeBuilder({ page }).analyze();
    expect(a11y.violations).toEqual([]);
  });

  // Offen, bis der projektspezifische Nachweis genau einer Buchung ergänzt ist.
  test.skip('F01-E1 doppeltes Absenden erzeugt eine Buchung', async ({ page }) => {
    await page.goto('/u/demo/30min');
    await page.getByRole('button', { name: /nächster freier tag/i }).click();
    await page.getByRole('button', { name: /11:00/ }).click();
    await page.getByLabel('Name').fill('Zweimal');
    await page.getByLabel('E-Mail').fill('zweimal@example.test');
    const confirm = page.getByRole('button', { name: /bestätigen/i });
    await Promise.all([confirm.click(), confirm.click()]);
    await expect(page.getByRole('heading', { name: /du bist gebucht/i })).toBeVisible();
    // Dann über deine API oder einen Datenbank-Helfer prüfen, dass genau eine Buchung existiert.
  });
});
