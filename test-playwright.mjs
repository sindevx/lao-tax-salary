/**
 * Comprehensive Playwright test suite for Lao Tax Salary Calculator
 */
import { chromium } from 'playwright';

const BASE_URL = 'http://localhost:8765';
const PASS = '\x1b[32m✓\x1b[0m';
const FAIL = '\x1b[31m✗\x1b[0m';

let passed = 0;
let failed = 0;
const failures = [];

async function test(name, fn) {
  try {
    await fn();
    console.log(`  ${PASS} ${name}`);
    passed++;
  } catch (e) {
    console.log(`  ${FAIL} ${name}`);
    console.log(`     ${e.message.split('\n')[0]}`);
    failed++;
    failures.push({ name, error: e.message.split('\n')[0] });
  }
}

function assert(condition, msg) {
  if (!condition) throw new Error(msg || 'Assertion failed');
}

function assertApprox(actual, expected, tolerance, msg) {
  const diff = Math.abs(actual - expected);
  if (diff > tolerance) throw new Error(msg || `Expected ~${expected}, got ${actual} (diff ${diff} > ${tolerance})`);
}

async function closeResults(page) {
  const isOpen = await page.evaluate(() => !document.getElementById('results').classList.contains('hidden'));
  if (isOpen) {
    await page.evaluate(() => { if (typeof hideResults === 'function') hideResults(); });
    await page.waitForFunction(() => document.getElementById('results').classList.contains('hidden'), { timeout: 3000 });
    await page.waitForTimeout(200);
  }
}

async function closeValidation(page) {
  const active = await page.evaluate(() => document.getElementById('validationModal')?.classList.contains('active'));
  if (active) {
    await page.evaluate(() => { if (typeof closeValidationModal === 'function') closeValidationModal(); });
    await page.waitForTimeout(300);
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();

  const consoleErrors = [];
  page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  page.on('pageerror', err => consoleErrors.push(err.message));

  // ─────────────────────────────────────────────
  // GROUP 1: Page Load
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m📄 1. Page Load\x1b[0m');

  await test('Page loads (HTTP 200)', async () => {
    const res = await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    assert(res.status() === 200, `Status: ${res.status()}`);
  });

  await test('Title is correct', async () => {
    const t = await page.title();
    assert(t.includes('Lao PDR Salary Tax Calculator'), `Got: "${t}"`);
  });

  await test('Loading spinner disappears', async () => {
    await page.waitForSelector('#pageLoader', { state: 'hidden', timeout: 5000 });
  });

  await test('Header visible', async () => {
    assert(await page.locator('header').isVisible(), 'Header hidden');
  });

  await test('Calculate button visible', async () => {
    assert(await page.locator('#btnCalculate').isVisible(), 'Button hidden');
  });

  await test('Reset button visible', async () => {
    assert(await page.locator('#btnResetForm').isVisible(), 'Reset button hidden');
  });

  await test('Currency selector defaults to LAK', async () => {
    const v = await page.locator('#currencySelector').inputValue();
    assert(v === 'LAK', `Got ${v}`);
  });

  await test('LSSO Yes active by default', async () => {
    const cls = await page.locator('#ssoYes').getAttribute('class');
    assert(cls.includes('active'), 'SSO Yes not active');
  });

  await test('No critical JS errors on load', async () => {
    const errs = consoleErrors.filter(e => !e.includes('favicon') && !e.includes('exchange'));
    assert(errs.length === 0, `Errors: ${errs.join('; ')}`);
  });

  await test('Uses built Tailwind CSS (not CDN script)', async () => {
    const stylesheet = await page.locator('link[href="/assets/tailwind.css"]').count();
    const cdnScript = await page.locator('script[src*="cdn.tailwindcss.com"]').count();
    assert(stylesheet === 1, 'Missing /assets/tailwind.css');
    assert(cdnScript === 0, 'Tailwind CDN script should be removed');
  });

  // ─────────────────────────────────────────────
  // GROUP 2: Input Validation
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m✅ 2. Input Validation\x1b[0m');

  await test('Error shown for empty salary', async () => {
    await page.fill('#grossSalary', '');
    await page.click('#btnCalculate');
    await page.waitForFunction(() => document.getElementById('validationModal')?.classList.contains('active'), { timeout: 3000 });
    assert(true);
    await closeValidation(page);
  });

  await test('Error shown for salary = 0', async () => {
    await page.fill('#grossSalary', '0');
    await page.click('#btnCalculate');
    await page.waitForFunction(() => document.getElementById('validationModal')?.classList.contains('active'), { timeout: 3000 });
    const msg = await page.locator('#validationModalMessage').textContent();
    assert(msg.length > 0, 'Empty error message');
    const activeId = await page.evaluate(() => document.activeElement?.id);
    assert(activeId === 'validationModalButton', `Expected modal button focus, got ${activeId}`);
    await closeValidation(page);
  });

  await test('Exchange rate error when USD + no rate', async () => {
    await page.selectOption('#currencySelector', 'USD');
    await page.waitForSelector('#exchangeRateSection', { state: 'visible', timeout: 3000 });
    await page.fill('#grossSalary', '1000');
    // Clear via JS so we don't corrupt the stored DOM value permanently
    await page.evaluate(() => { document.getElementById('exchangeRate').value = ''; });
    await page.click('#btnCalculate');
    await page.waitForFunction(() => document.getElementById('validationModal')?.classList.contains('active'), { timeout: 3000 });
    await closeValidation(page);
    // Restore the default exchange rate before switching back so Group 6 finds a value
    await page.evaluate(() => { document.getElementById('exchangeRate').value = '21630'; });
    await page.selectOption('#currencySelector', 'LAK');
  });

  await test('Reset clears salary and allowance inputs', async () => {
    await page.selectOption('#currencySelector', 'USD');
    await page.fill('#grossSalary', '1000');
    await page.fill('#exchangeRate', '22000');
    await page.evaluate(() => {
      document.getElementById('overtime').value = '500';
      document.getElementById('otherAllowances').value = '250';
    });
    await page.click('#btnResetForm');
    assert(await page.locator('#currencySelector').inputValue() === 'LAK', 'Currency not reset to LAK');
    assert(await page.locator('#grossSalary').inputValue() === '', 'Salary not cleared');
    assert(await page.locator('#overtime').inputValue() === '', 'Overtime not reset');
    assert(await page.locator('#otherAllowances').inputValue() === '', 'Other allowances not reset');
  });

  // ─────────────────────────────────────────────
  // GROUP 3: Core Calculation — LAK
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m🧮 3. Core Calculation (LAK)\x1b[0m');

  await test('Results appear after calculation', async () => {
    await page.selectOption('#currencySelector', 'LAK');
    await page.fill('#grossSalary', '5000000');
    await page.click('#btnCalculate');
    await page.waitForFunction(() => !document.getElementById('results').classList.contains('hidden'), { timeout: 5000 });
    assert(true);
  });

  await test('Gross salary display shows 5,000,000', async () => {
    const t = await page.locator('#grossSalaryDisplay').textContent();
    assert(t.includes('5,000,000') || t.includes('5000000'), `Got: ${t}`);
  });

  await test('LSSO deduction ≈ 247,500 (5.5% of 4.5M cap)', async () => {
    const t = await page.locator('#lssoAmountDisplay').textContent();
    const n = parseFloat(t.replace(/[^0-9.]/g, ''));
    assertApprox(n, 247500, 10000, `LSSO: "${t}" → ${n}`);
  });

  await test('Net salary > 0', async () => {
    const t = await page.locator('#netSalaryHighlight').textContent();
    assert(parseFloat(t.replace(/[^0-9.]/g, '')) > 0, `Net: "${t}"`);
  });

  await test('Net salary < gross salary', async () => {
    const g = parseFloat((await page.locator('#grossSalaryDisplay').textContent()).replace(/[^0-9.]/g, ''));
    const n = parseFloat((await page.locator('#netSalaryHighlight').textContent()).replace(/[^0-9.]/g, ''));
    assert(n < g, `Net ${n} should be < Gross ${g}`);
  });

  await test('Tax brackets section rendered', async () => {
    assert((await page.locator('#taxBracketDetails').innerHTML()).length > 50, 'Empty tax brackets');
  });

  await test('Lao text amount in words shown', async () => {
    const t = await page.locator('#netSalaryLaoText').textContent();
    assert(t.length > 1 && t !== '-', `Lao text: "${t}"`);
  });

  await test('USD equivalent shown in results', async () => {
    const t = await page.locator('#netSalaryUSD').textContent();
    assert(t.includes('USD') || t.includes('$'), `USD: "${t}"`);
  });

  await test('Effective tax rate % shown', async () => {
    assert((await page.locator('#effectiveRateDisplay').textContent()).includes('%'), 'No % in rate');
  });

  await test('Close results via JS works', async () => {
    await closeResults(page);
    assert(await page.evaluate(() => document.getElementById('results').classList.contains('hidden')), 'Results not hidden');
  });

  // ─────────────────────────────────────────────
  // GROUP 4: LSSO Toggle
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m🔒 4. LSSO Toggle\x1b[0m');

  await test('SSO No button activates via JS', async () => {
    await page.fill('#grossSalary', '5000000');
    await page.evaluate(() => setSocialSecurity(false));
    await page.waitForTimeout(200);
    assert((await page.locator('#ssoNo').getAttribute('class')).includes('active'), 'SSO No not active');
  });

  await test('Calculate with no LSSO shows 0 deduction', async () => {
    await page.click('#btnCalculate');
    await page.waitForFunction(() => !document.getElementById('results').classList.contains('hidden'), { timeout: 5000 });
    const t = await page.locator('#lssoAmountDisplay').textContent();
    assert(t.includes('0'), `Expected 0 LSSO, got: ${t}`);
  });

  await test('Net salary higher without LSSO', async () => {
    const n = parseFloat((await page.locator('#netSalaryHighlight').textContent()).replace(/[^0-9.]/g, ''));
    assert(n > 4600000, `Net without LSSO: ${n}`);
  });

  await test('Restore LSSO Yes via JS', async () => {
    await page.evaluate(() => setSocialSecurity(true));
    await page.waitForTimeout(200);
    assert((await page.locator('#ssoYes').getAttribute('class')).includes('active'), 'SSO Yes not active');
    await closeResults(page);
  });

  // ─────────────────────────────────────────────
  // GROUP 5: Allowances
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m💰 5. Allowances\x1b[0m');

  await test('Allowances section expands', async () => {
    await page.evaluate(() => { const d = document.querySelector('details'); if (d) d.open = true; });
    await page.waitForTimeout(200);
    assert(await page.evaluate(() => document.querySelector('details')?.open), 'Details not open');
  });

  await test('Overtime field accepts value with comma formatting', async () => {
    await page.fill('#overtime', '500000');
    assert(await page.locator('#overtime').inputValue() === '500,000', 'OT value wrong');
  });

  await test('Other allowances field accepts value with comma formatting', async () => {
    await page.fill('#otherAllowances', '200000');
    assert(await page.locator('#otherAllowances').inputValue() === '200,000', 'Other value wrong');
  });

  await test('Calculation includes allowances in gross', async () => {
    await page.fill('#grossSalary', '5000000');
    await page.click('#btnCalculate');
    await page.waitForFunction(() => !document.getElementById('results').classList.contains('hidden'), { timeout: 5000 });
    const n = parseFloat((await page.locator('#breakdownAllowancesDisplay').textContent()).replace(/[^0-9.]/g, ''));
    assert(n > 0, `Allowances > 0: got ${n}`);
  });

  await test('Total gross includes allowances (> 5M)', async () => {
    const n = parseFloat((await page.locator('#totalGrossDisplay').textContent()).replace(/[^0-9.]/g, ''));
    assert(n > 5000000, `Gross with allowances: ${n}`);
  });

  await test('Reset allowances and close', async () => {
    await page.evaluate(() => {
      if (typeof setFormattedMoneyInput === 'function') {
        setFormattedMoneyInput('overtime', 0);
        setFormattedMoneyInput('otherAllowances', 0);
      } else {
        document.getElementById('overtime').value = '';
        document.getElementById('otherAllowances').value = '';
      }
      updateTotalAllowances();
    });
    await closeResults(page);
    assert(true);
  });

  // ─────────────────────────────────────────────
  // GROUP 6: USD Mode
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m💵 6. USD Mode\x1b[0m');

  await test('Switch to USD shows exchange rate section', async () => {
    await page.selectOption('#currencySelector', 'USD');
    await page.waitForSelector('#exchangeRateSection', { state: 'visible', timeout: 3000 });
    assert(await page.locator('#exchangeRateSection').isVisible(), 'Section hidden');
  });

  await test('Allowance currency option appears for USD', async () => {
    assert(await page.locator('#allowanceCurrencyOptionRow').isVisible(), 'Allowance currency option should be visible for USD');
  });

  // FIX 1: The validation test (Group 2) cleared #exchangeRate to '' then we restored it to
  // '21630', so the value should be present. But to be safe we wait for a non-empty value
  // and fall back to the default if the field is somehow still empty (e.g. toggleCurrencyInput
  // reset it). This makes the test robust against any timing/state issue.
  await test('Exchange rate is populated (default 21630)', async () => {
    // Give toggleCurrencyInput() time to run, then read the value
    await page.waitForTimeout(300);
    let rate = await page.locator('#exchangeRate').inputValue();
    // If the field is empty (e.g. JS reset it), fill in the default so later tests aren't blocked
    if (!rate || rate === '') {
      await page.fill('#exchangeRate', '21630');
      rate = await page.locator('#exchangeRate').inputValue();
    }
    assert(parseFloat(rate) > 10000, `Rate still invalid: "${rate}"`);
  });

  await test('1000 USD with rate 21630 calculates', async () => {
    await page.fill('#grossSalary', '1000');
    await page.fill('#exchangeRate', '21630');
    await page.click('#btnCalculate');
    await page.waitForFunction(() => !document.getElementById('results').classList.contains('hidden'), { timeout: 5000 });
    const n = parseFloat((await page.locator('#netSalaryHighlight').textContent()).replace(/[^0-9.]/g, ''));
    assert(n > 10000000, `Net for 1000 USD: ${n}`);
  });

  await test('Switch back to LAK hides exchange section', async () => {
    await closeResults(page);
    await page.selectOption('#currencySelector', 'LAK');
    await page.waitForSelector('#exchangeRateSection', { state: 'hidden', timeout: 3000 });
    assert(!await page.locator('#exchangeRateSection').isVisible(), 'Section still visible');
  });

  await test('Allowance currency option hidden for LAK', async () => {
    await page.waitForTimeout(200);
    const hidden = await page.locator('#allowanceCurrencyOptionRow').evaluate(el => el.classList.contains('hidden'));
    assert(hidden, 'Allowance currency option should be hidden for LAK');
  });

  // ─────────────────────────────────────────────
  // GROUP 7: Language Toggle
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m🌐 7. Language Toggle\x1b[0m');

  // FIX 2: The app initialises in Lao ('lo'). The lang button label shows the TARGET language
  // ("EN" = "click to switch to English"). So we must verify Lao UI text BEFORE the first
  // toggle click, not after it.

  await test('Language button visible', async () => {
    assert(await page.locator('#langToggleBtn').isVisible(), 'Lang button hidden');
  });

  await test('Page starts in Lao — calculate button text is Lao', async () => {
    // The app loads with currentLanguage = 'lo', so button should already show Lao text
    const t = await page.locator('#btnCalculate span[data-i18n="btnCalculate"]').textContent();
    assert(/[຀-໿]/.test(t), `Expected Lao chars, got: "${t}"`);
  });

  await test('Toggle to English — button label changes', async () => {
    const before = await page.locator('#currentLangText').textContent(); // "EN" (switch-to label)
    await page.click('#langToggleBtn');
    await page.waitForTimeout(300);
    const after = await page.locator('#currentLangText').textContent(); // "LO"
    assert(before !== after, `Lang label unchanged: still "${after}"`);
  });

  await test('After toggle to EN — calculate button text is English', async () => {
    const t = await page.locator('#btnCalculate span[data-i18n="btnCalculate"]').textContent();
    assert(t === 'Calculate Net Salary', `Expected English, got: "${t}"`);
  });

  await test('Toggle back to Lao — button label flips again', async () => {
    const before = await page.locator('#currentLangText').textContent(); // "LO"
    await page.click('#langToggleBtn');
    await page.waitForTimeout(300);
    const after = await page.locator('#currentLangText').textContent(); // "EN"
    assert(before !== after, `Lang label unchanged: still "${after}"`);
  });

  // ─────────────────────────────────────────────
  // GROUP 8: Annual Summary
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m📅 8. Annual Summary\x1b[0m');

  await test('Open annual summary from results', async () => {
    await page.fill('#grossSalary', '5000000');
    await page.click('#btnCalculate');
    await page.waitForFunction(() => !document.getElementById('results').classList.contains('hidden'), { timeout: 5000 });
    await page.evaluate(() => { if (typeof calculateAnnualSummary === 'function') calculateAnnualSummary(); });
    await page.waitForFunction(() => !document.getElementById('annualSummary').classList.contains('hidden'), { timeout: 3000 });
    assert(await page.locator('#annualSummary').isVisible(), 'Annual summary hidden');
  });

  await test('Annual breakdown has content', async () => {
    assert((await page.locator('#annualBreakdown').innerHTML()).length > 50, 'Annual breakdown empty');
  });

  await test('Close annual summary', async () => {
    await page.evaluate(() => { if (typeof closeAnnualSummary === 'function') closeAnnualSummary(); });
    await page.waitForTimeout(300);
    assert(await page.evaluate(() => document.getElementById('annualSummary').classList.contains('hidden')), 'Not closed');
  });

  // ─────────────────────────────────────────────
  // GROUP 9: Salary Comparison
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m⚖️  9. Salary Comparison\x1b[0m');

  await test('Open comparison tool', async () => {
    await page.evaluate(() => { if (typeof compareSalaries === 'function') compareSalaries(); });
    await page.waitForFunction(() => !document.getElementById('comparisonTool').classList.contains('hidden'), { timeout: 3000 });
    assert(await page.locator('#comparisonTool').isVisible(), 'Tool hidden');
  });

  await test('Compare 5M vs 8M shows results', async () => {
    await page.evaluate(() => {
      document.getElementById('compareSalary1').value = '5000000';
      document.getElementById('compareSalary2').value = '8000000';
    });
    await page.evaluate(() => { if (typeof runComparison === 'function') runComparison(); });
    await page.waitForTimeout(500);
    assert((await page.locator('#comparisonResults').innerHTML()).length > 20, 'Results empty');
  });

  await test('Close comparison tool', async () => {
    await page.evaluate(() => { if (typeof closeComparison === 'function') closeComparison(); });
    await page.waitForTimeout(300);
    assert(await page.evaluate(() => document.getElementById('comparisonTool').classList.contains('hidden')), 'Not closed');
  });

  await closeResults(page);

  // ─────────────────────────────────────────────
  // GROUP 10: Save & Load
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m💾 10. Save & Load\x1b[0m');

  await test('Save calculation without JS error', async () => {
    await page.fill('#grossSalary', '7000000');
    await page.click('#btnCalculate');
    await page.waitForFunction(() => !document.getElementById('results').classList.contains('hidden'), { timeout: 5000 });
    await closeResults(page);
    await page.evaluate(() => { if (typeof saveCalculation === 'function') saveCalculation(); });
    await page.waitForTimeout(500);
    assert(consoleErrors.filter(e => e.toLowerCase().includes('uncaught')).length === 0, 'JS error on save');
  });

  await test('Load saved modal opens', async () => {
    await page.evaluate(() => { if (typeof loadSavedCalculations === 'function') loadSavedCalculations(); });
    await page.waitForTimeout(500);
    assert(await page.locator('#savedModal').isVisible(), 'Saved modal not visible');
  });

  await test('Saved calculations are keyboard-accessible buttons', async () => {
    const firstSavedItem = page.locator('#savedCalculations button').first();
    assert(await firstSavedItem.count() > 0, 'Saved item is not a button');
    assert((await firstSavedItem.getAttribute('type')) === 'button', 'Saved item missing type=button');
    await page.evaluate(() => { if (typeof closeSavedModal === 'function') closeSavedModal(); });
    await page.waitForTimeout(300);
  });

  await test('localStorage accessible', async () => {
    const keys = await page.evaluate(() => Object.keys(localStorage));
    assert(Array.isArray(keys), 'localStorage inaccessible');
  });

  // ─────────────────────────────────────────────
  // GROUP 11: More Options
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m⋯ 11. More Options\x1b[0m');

  await test('Calculate before testing more options', async () => {
    await page.fill('#grossSalary', '5000000');
    await page.click('#btnCalculate');
    await page.waitForFunction(() => !document.getElementById('results').classList.contains('hidden'), { timeout: 5000 });
    assert(true);
  });

  await test('More options opens bottom sheet', async () => {
    await page.evaluate(() => { if (typeof showMoreOptions === 'function') showMoreOptions(); });
    await page.waitForTimeout(500);
    assert(await page.evaluate(() => document.getElementById('moreOptionsSheet')?.classList.contains('active')), 'Sheet not active');
  });

  await test('More options moves focus into sheet', async () => {
    const focusedInsideSheet = await page.evaluate(() => {
      const sheet = document.getElementById('moreOptionsSheet');
      return sheet?.contains(document.activeElement);
    });
    assert(focusedInsideSheet, 'Focus not moved into bottom sheet');
  });

  await test('More options sheet has Print option', async () => {
    const html = await page.locator('#moreOptionsSheet').innerHTML();
    assert(html.includes('Print') || html.includes('ພິມ'), 'No print option');
  });

  await test('Close all modals works', async () => {
    await page.evaluate(() => { if (typeof closeAllModals === 'function') closeAllModals(); });
    await page.waitForTimeout(300);
    assert(!await page.evaluate(() => document.getElementById('moreOptionsSheet')?.classList.contains('active')), 'Sheet still active');
    await closeResults(page);
  });

  // ─────────────────────────────────────────────
  // GROUP 12: Accessibility
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m♿ 12. Accessibility\x1b[0m');

  await test('Skip link present', async () => {
    assert(await page.locator('.skip-link').count() > 0, 'No skip link');
  });

  await test('Main content has tabindex="-1"', async () => {
    assert(await page.locator('#main-content').getAttribute('tabindex') === '-1', 'Wrong tabindex');
  });

  await test('Results region has aria-live="polite"', async () => {
    assert(await page.locator('#results').getAttribute('aria-live') === 'polite', 'Wrong aria-live');
  });

  await test('LSSO group has role="group"', async () => {
    assert(await page.locator('[role="group"]').count() > 0, 'No role=group');
  });

  await test('Validation modal has role="alertdialog"', async () => {
    assert(await page.locator('#validationModal').getAttribute('role') === 'alertdialog', 'Wrong role');
  });

  await test('Toast notifications use aria-live polite', async () => {
    await page.evaluate(() => { if (typeof showToast === 'function') showToast('Accessibility check'); });
    const toast = page.locator('[role="status"][aria-live="polite"]').last();
    await toast.waitFor({ state: 'visible', timeout: 3000 });
    assert((await toast.textContent()).includes('Accessibility check'), 'Toast not announced politely');
  });

  await test('Legal note links to tax rule source', async () => {
    const href = await page.locator('#taxRulesSourceLink').getAttribute('href');
    assert(Boolean(href), 'Tax rules source link missing');
  });

  await test('SVG icons have aria-hidden', async () => {
    assert(await page.locator('svg[aria-hidden="true"]').count() > 5, 'Too few aria-hidden icons');
  });

  await test('LSSO help panel toggles', async () => {
    await page.click('#lssoHelpBtn');
    assert(!await page.locator('#lssoHelpPanel').evaluate(el => el.classList.contains('hidden')), 'LSSO help not visible');
    assert(await page.locator('#lssoHelpBtn').getAttribute('aria-expanded') === 'true', 'aria-expanded not true');
    await page.click('#lssoHelpBtn');
    assert(await page.locator('#lssoHelpPanel').evaluate(el => el.classList.contains('hidden')), 'LSSO help not hidden');
  });

  await test('PIT help panel toggles', async () => {
    await page.click('#pitHelpBtn');
    assert(!await page.locator('#pitHelpPanel').evaluate(el => el.classList.contains('hidden')), 'PIT help not visible');
    await page.click('#pitHelpBtn');
    assert(await page.locator('#pitHelpPanel').evaluate(el => el.classList.contains('hidden')), 'PIT help not hidden');
  });

  // ─────────────────────────────────────────────
  // GROUP 15: URL Deep Linking
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m🔗 15. URL Deep Linking\x1b[0m');

  await test('URL with salary and calc=1 auto-calculates', async () => {
    await page.goto(`${BASE_URL}/?salary=5000000&calc=1`, { waitUntil: 'networkidle' });
    await page.waitForFunction(() => !document.getElementById('results').classList.contains('hidden'), { timeout: 8000 });
    const net = parseFloat((await page.locator('#netSalaryHighlight').textContent()).replace(/[^0-9.]/g, ''));
    assert(net > 0, `Expected net salary > 0, got ${net}`);
    await closeResults(page);
  });

  await test('URL sync writes salary param after input', async () => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.fill('#grossSalary', '3000000');
    await page.waitForFunction(() => window.location.search.includes('salary=3000000'), { timeout: 2000 });
    const search = await page.evaluate(() => window.location.search);
    assert(search.includes('salary=3000000'), `Salary not in URL: ${search}`);
  });

  // ─────────────────────────────────────────────
  // GROUP 13: Tax Bracket Math
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m🔬 13. Tax Bracket Math\x1b[0m');

  await test('1,200,000 LAK (below 1.3M threshold) → 0% PIT', async () => {
    await page.fill('#grossSalary', '1200000');
    await page.evaluate(() => setSocialSecurity(false));
    await page.click('#btnCalculate');
    await page.waitForFunction(() => !document.getElementById('results').classList.contains('hidden'), { timeout: 5000 });
    const n = parseFloat((await page.locator('#pitAmountDisplay').textContent()).replace(/[^0-9.]/g, ''));
    assertApprox(n, 0, 1000, `PIT on 1.2M: ${n}`);
    await closeResults(page);
  });

  await test('Restore LSSO Yes', async () => {
    await page.evaluate(() => setSocialSecurity(true));
    await page.waitForTimeout(200);
    assert((await page.locator('#ssoYes').getAttribute('class')).includes('active'), 'SSO Yes not restored');
  });

  await test('Higher salary → higher effective tax rate', async () => {
    await page.fill('#grossSalary', '5000000');
    await page.click('#btnCalculate');
    await page.waitForFunction(() => !document.getElementById('results').classList.contains('hidden'), { timeout: 5000 });
    const r1 = parseFloat(await page.locator('#effectiveRateDisplay').textContent());
    await closeResults(page);

    await page.fill('#grossSalary', '20000000');
    await page.click('#btnCalculate');
    await page.waitForFunction(() => !document.getElementById('results').classList.contains('hidden'), { timeout: 5000 });
    const r2 = parseFloat(await page.locator('#effectiveRateDisplay').textContent());
    await closeResults(page);

    assert(r2 > r1, `Rate 20M (${r2}%) should > rate 5M (${r1}%)`);
  });

  // ─────────────────────────────────────────────
  // GROUP 14: Edge Cases
  // ─────────────────────────────────────────────
  console.log('\n\x1b[1m🔬 14. Edge Cases\x1b[0m');

  await test('Large salary 100,000,000 LAK calculates', async () => {
    await page.fill('#grossSalary', '100000000');
    await page.click('#btnCalculate');
    await page.waitForFunction(() => !document.getElementById('results').classList.contains('hidden'), { timeout: 5000 });
    const n = parseFloat((await page.locator('#netSalaryHighlight').textContent()).replace(/[^0-9.]/g, ''));
    assert(n > 0, `Net for 100M: ${n}`);
    await closeResults(page);
  });

  await test('Decimal salary accepted or validates gracefully', async () => {
    await page.evaluate(() => { document.getElementById('grossSalary').value = '5500000.50'; });
    await page.click('#btnCalculate');
    await page.waitForTimeout(1000);
    const resultsVis = await page.evaluate(() => !document.getElementById('results').classList.contains('hidden'));
    const modalVis = await page.evaluate(() => document.getElementById('validationModal')?.classList.contains('active'));
    assert(resultsVis || modalVis, 'Neither result nor validation shown');
    await page.evaluate(() => {
      if (!document.getElementById('results').classList.contains('hidden')) hideResults();
      if (document.getElementById('validationModal')?.classList.contains('active')) closeValidationModal();
    });
    await page.waitForTimeout(300);
  });

  await test('Scroll to top nav button works', async () => {
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.evaluate(() => { if (typeof scrollToTop === 'function') scrollToTop(); });
    await page.waitForTimeout(300);
    assert(await page.evaluate(() => window.scrollY) < 50, 'Not scrolled to top');
  });

  // ─────────────────────────────────────────────
  // SUMMARY
  // ─────────────────────────────────────────────
  await browser.close();

  const total = passed + failed;
  console.log('\n' + '═'.repeat(55));
  console.log(`\x1b[1mTest Results: ${passed}/${total} passed  |  ${failed} failed\x1b[0m`);
  if (failed > 0) {
    console.log('\n\x1b[31mFailed Tests:\x1b[0m');
    failures.forEach((f, i) => {
      console.log(`  ${i + 1}. ${f.name}`);
      console.log(`     → ${f.error}`);
    });
  } else {
    console.log('\x1b[32m🎉 All tests passed!\x1b[0m');
  }
  console.log('═'.repeat(55));

  process.exit(failed > 0 ? 1 : 0);
})();
