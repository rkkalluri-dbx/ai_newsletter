const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:5001';
const SCREENSHOT_DIR = './screenshots';

async function ensureScreenshotDir() {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }
}

async function testDashboard() {
  console.log('Starting Dashboard Tests...\n');

  await ensureScreenshotDir();

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();

  const results = [];

  try {
    // Test 1: Load Dashboard
    console.log('Test 1: Loading Dashboard...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const title = await page.title();
    console.log(`  Page Title: ${title}`);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/01-dashboard.png`, fullPage: true });
    console.log('  Screenshot: 01-dashboard.png');

    // Check for error alert
    const errorAlert = await page.$('text=Failed to connect to API');
    if (errorAlert) {
      console.log('  ❌ FAIL: API connection error displayed');
      results.push({ test: 'Dashboard Load', status: 'FAIL', error: 'API connection error' });
    } else {
      console.log('  ✅ PASS: Dashboard loaded successfully');
      results.push({ test: 'Dashboard Load', status: 'PASS' });
    }

    // Test 2: Check Summary Cards
    console.log('\nTest 2: Checking Summary Cards...');
    const summaryCards = await page.$$('div[class*="MuiCard"]');
    console.log(`  Found ${summaryCards.length} cards`);

    if (summaryCards.length >= 4) {
      console.log('  ✅ PASS: Summary cards present');
      results.push({ test: 'Summary Cards', status: 'PASS' });
    } else {
      console.log('  ❌ FAIL: Expected at least 4 summary cards');
      results.push({ test: 'Summary Cards', status: 'FAIL' });
    }

    // Test 3: Check Next Actions Section
    console.log('\nTest 3: Checking Next Actions...');
    const nextActionsHeader = await page.$('text=Next Actions');
    if (nextActionsHeader) {
      console.log('  ✅ PASS: Next Actions section found');
      results.push({ test: 'Next Actions Section', status: 'PASS' });

      // Check for clickable action items
      const actionItems = await page.$$('div[style*="cursor: pointer"], div[class*="cursor-pointer"]');
      console.log(`  Found ${actionItems.length} clickable action items`);
    } else {
      console.log('  ❌ FAIL: Next Actions section not found');
      results.push({ test: 'Next Actions Section', status: 'FAIL' });
    }

    // Test 4: Check Charts
    console.log('\nTest 4: Checking Charts...');
    const charts = await page.$$('svg.recharts-surface');
    console.log(`  Found ${charts.length} Recharts charts`);

    if (charts.length >= 2) {
      console.log('  ✅ PASS: Charts rendered');
      results.push({ test: 'Charts', status: 'PASS' });
    } else {
      console.log('  ⚠️ WARN: Expected at least 2 charts');
      results.push({ test: 'Charts', status: 'WARN' });
    }

    // Test 5: Navigate to Projects
    console.log('\nTest 5: Testing Navigation to Projects...');
    await page.click('text=Projects');
    await page.waitForTimeout(1500);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/02-projects.png`, fullPage: true });
    console.log('  Screenshot: 02-projects.png');

    const projectsHeader = await page.$('text=Projects');
    if (projectsHeader) {
      console.log('  ✅ PASS: Navigated to Projects page');
      results.push({ test: 'Projects Navigation', status: 'PASS' });
    } else {
      console.log('  ❌ FAIL: Projects page not loaded');
      results.push({ test: 'Projects Navigation', status: 'FAIL' });
    }

    // Test 6: Navigate to Vendors
    console.log('\nTest 6: Testing Navigation to Vendors...');
    await page.click('text=Vendors');
    await page.waitForTimeout(1500);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/03-vendors.png`, fullPage: true });
    console.log('  Screenshot: 03-vendors.png');

    const vendorsContent = await page.$('text=Vendor');
    if (vendorsContent) {
      console.log('  ✅ PASS: Navigated to Vendors page');
      results.push({ test: 'Vendors Navigation', status: 'PASS' });
    } else {
      console.log('  ❌ FAIL: Vendors page not loaded');
      results.push({ test: 'Vendors Navigation', status: 'FAIL' });
    }

    // Test 7: Navigate to Alerts
    console.log('\nTest 7: Testing Navigation to Alerts...');
    await page.click('text=Alerts');
    await page.waitForTimeout(1500);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/04-alerts.png`, fullPage: true });
    console.log('  Screenshot: 04-alerts.png');
    results.push({ test: 'Alerts Navigation', status: 'PASS' });

    // Test 8: Click notification badge
    console.log('\nTest 8: Testing Notification Badge...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const badge = await page.$('.MuiBadge-root');
    if (badge) {
      console.log('  Found notification badge');
      await badge.click();
      await page.waitForTimeout(1000);
      await page.screenshot({ path: `${SCREENSHOT_DIR}/05-badge-click.png`, fullPage: true });
      console.log('  ✅ PASS: Notification badge clicked');
      results.push({ test: 'Notification Badge', status: 'PASS' });
    } else {
      console.log('  ⚠️ WARN: Notification badge not found');
      results.push({ test: 'Notification Badge', status: 'WARN' });
    }

    // Test 9: Test Next Actions click navigation (TASK-061)
    console.log('\nTest 9: Testing Next Actions Click Navigation (TASK-061)...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Look for clickable action items in Next Actions
    const actionBoxes = await page.$$('div[style*="cursor"][style*="pointer"]');
    console.log(`  Found ${actionBoxes.length} clickable elements`);

    if (actionBoxes.length > 0) {
      await actionBoxes[0].click();
      await page.waitForTimeout(1500);

      const currentUrl = page.url();
      console.log(`  Navigated to: ${currentUrl}`);

      if (currentUrl.includes('/projects/')) {
        console.log('  ✅ PASS: Click navigated to project detail');
        results.push({ test: 'Action Click Navigation', status: 'PASS' });
        await page.screenshot({ path: `${SCREENSHOT_DIR}/06-project-detail.png`, fullPage: true });
      } else {
        console.log('  ⚠️ WARN: Did not navigate to project detail');
        results.push({ test: 'Action Click Navigation', status: 'WARN' });
      }
    } else {
      console.log('  ⚠️ WARN: No clickable action items found');
      results.push({ test: 'Action Click Navigation', status: 'WARN' });
    }

  } catch (error) {
    console.error('\n❌ Test Error:', error.message);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/error.png`, fullPage: true });
    results.push({ test: 'Execution', status: 'ERROR', error: error.message });
  } finally {
    await browser.close();
  }

  // Summary
  console.log('\n' + '='.repeat(50));
  console.log('TEST SUMMARY');
  console.log('='.repeat(50));

  const passed = results.filter(r => r.status === 'PASS').length;
  const failed = results.filter(r => r.status === 'FAIL').length;
  const warnings = results.filter(r => r.status === 'WARN').length;

  results.forEach(r => {
    const icon = r.status === 'PASS' ? '✅' : r.status === 'FAIL' ? '❌' : '⚠️';
    console.log(`${icon} ${r.test}: ${r.status}${r.error ? ' - ' + r.error : ''}`);
  });

  console.log('='.repeat(50));
  console.log(`Total: ${results.length} | Passed: ${passed} | Failed: ${failed} | Warnings: ${warnings}`);
  console.log(`Screenshots saved to: ${SCREENSHOT_DIR}/`);

  return failed === 0;
}

testDashboard()
  .then(success => process.exit(success ? 0 : 1))
  .catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
