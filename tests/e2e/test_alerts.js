const { chromium } = require('playwright');
const fs = require('fs');

const BASE_URL = 'http://localhost:5001';
const SCREENSHOT_DIR = './screenshots';

async function testAlerts() {
  console.log('Starting Alerts Page Tests...\n');

  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  // Capture API responses
  const apiResponses = {};
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('/api/v1/')) {
      try {
        const json = await response.json();
        const endpoint = url.split('/api/v1/')[1].split('?')[0];
        apiResponses[endpoint] = json;
        console.log(`  API Response [${endpoint}]: ${JSON.stringify(json).substring(0, 200)}...`);
      } catch (e) {
        // Not JSON response
      }
    }
  });

  try {
    // Test 1: Navigate to Alerts page
    console.log('Test 1: Navigating to Alerts page...');
    await page.goto(`${BASE_URL}/alerts`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/alerts-page.png`, fullPage: true });
    console.log('  Screenshot: alerts-page.png\n');

    // Test 2: Check Alert Stats API
    console.log('Test 2: Checking Alert Stats...');
    const statsResponse = await page.evaluate(async () => {
      const res = await fetch('/api/v1/alerts/stats');
      return res.json();
    });
    console.log('  Alert Stats API Response:');
    console.log(JSON.stringify(statsResponse, null, 2));

    // Test 3: Check Alerts List API
    console.log('\nTest 3: Checking Alerts List...');
    const alertsResponse = await page.evaluate(async () => {
      const res = await fetch('/api/v1/alerts');
      return res.json();
    });
    console.log(`  Total alerts in response: ${alertsResponse.data?.length || 0}`);
    console.log(`  Pagination total: ${alertsResponse.total || 'N/A'}`);

    // Test 4: Check Dashboard Summary for comparison
    console.log('\nTest 4: Checking Dashboard Summary...');
    const summaryResponse = await page.evaluate(async () => {
      const res = await fetch('/api/v1/dashboard/summary');
      return res.json();
    });
    console.log('  Dashboard Summary - Alerts:');
    console.log(JSON.stringify(summaryResponse.data?.alerts, null, 2));

    // Test 5: Check page elements
    console.log('\nTest 5: Checking Page Elements...');

    // Look for stat cards/counters
    const statCards = await page.$$eval('[class*="Card"], [class*="Stat"], [class*="chip"]', elements => {
      return elements.map(el => ({
        text: el.textContent?.trim().substring(0, 100),
        class: el.className
      }));
    });
    console.log(`  Found ${statCards.length} card/stat elements`);
    statCards.slice(0, 10).forEach((card, i) => {
      console.log(`    ${i + 1}. ${card.text}`);
    });

    // Test 6: Check for "0" values that might be wrong
    console.log('\nTest 6: Checking for zero values...');
    const zeroElements = await page.$$eval('*', elements => {
      return elements
        .filter(el => el.textContent?.trim() === '0' && el.children.length === 0)
        .map(el => ({
          tag: el.tagName,
          class: el.className,
          parent: el.parentElement?.textContent?.trim().substring(0, 50)
        }))
        .slice(0, 20);
    });
    console.log(`  Found ${zeroElements.length} elements showing "0":`);
    zeroElements.forEach((el, i) => {
      console.log(`    ${i + 1}. <${el.tag}> parent: "${el.parent}"`);
    });

    // Test 7: Take screenshot of specific areas
    console.log('\nTest 7: Capturing detailed screenshots...');

    // Full page
    await page.screenshot({ path: `${SCREENSHOT_DIR}/alerts-full.png`, fullPage: true });

    // Just the main content area
    const mainContent = await page.$('main, [class*="content"], [class*="Container"]');
    if (mainContent) {
      await mainContent.screenshot({ path: `${SCREENSHOT_DIR}/alerts-content.png` });
    }

    console.log('\n' + '='.repeat(50));
    console.log('SUMMARY');
    console.log('='.repeat(50));
    console.log(`API Stats - Unacknowledged: ${statsResponse.data?.overall?.unacknowledged || 'N/A'}`);
    console.log(`API Stats - Critical: ${statsResponse.data?.overall?.critical || statsResponse.data?.by_severity?.critical || 'N/A'}`);
    console.log(`API Stats - Warning: ${statsResponse.data?.overall?.warning || statsResponse.data?.by_severity?.warning || 'N/A'}`);
    console.log(`Dashboard Summary - Unacknowledged: ${summaryResponse.data?.alerts?.unacknowledged || 'N/A'}`);
    console.log(`Alerts List Total: ${alertsResponse.total || alertsResponse.data?.length || 'N/A'}`);

  } catch (error) {
    console.error('\n❌ Test Error:', error.message);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/alerts-error.png`, fullPage: true });
  } finally {
    await browser.close();
  }
}

testAlerts().catch(console.error);
