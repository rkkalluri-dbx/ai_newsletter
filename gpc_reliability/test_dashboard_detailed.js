const { chromium } = require('playwright');
const fs = require('fs');

const BASE_URL = 'http://localhost:5001';
const SCREENSHOT_DIR = './screenshots';

async function testDashboardDetailed() {
  console.log('Starting Detailed Dashboard Tests...\n');

  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await context.newPage();

  // Track console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  // Track failed requests
  const failedRequests = [];
  page.on('requestfailed', request => {
    failedRequests.push({
      url: request.url(),
      failure: request.failure()?.errorText
    });
  });

  // Track API responses
  const apiResponses = {};
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('/api/v1/')) {
      const status = response.status();
      const endpoint = url.split('/api/v1/')[1].split('?')[0];

      if (status >= 400) {
        console.log(`  ❌ API Error [${endpoint}]: ${status}`);
        try {
          const body = await response.text();
          console.log(`     Response: ${body.substring(0, 200)}`);
        } catch (e) {}
      }

      if (status === 200) {
        try {
          const json = await response.json();
          apiResponses[endpoint] = json;
        } catch (e) {}
      }
    }
  });

  try {
    // Test 1: Load Dashboard
    console.log('Test 1: Loading Dashboard...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/dashboard-detailed.png`, fullPage: true });
    console.log('  Screenshot: dashboard-detailed.png\n');

    // Test 2: Check Vendor Performance API
    console.log('Test 2: Checking Vendor Performance API...');
    const vendorPerfResponse = await page.evaluate(async () => {
      const res = await fetch('/api/v1/dashboard/vendor-performance?limit=5');
      return { status: res.status, data: await res.json() };
    });
    console.log(`  Status: ${vendorPerfResponse.status}`);
    console.log('  Response:');
    console.log(JSON.stringify(vendorPerfResponse.data, null, 2));

    // Test 3: Check if charts are rendering
    console.log('\nTest 3: Checking Chart Rendering...');
    const charts = await page.$$eval('svg.recharts-surface', elements => {
      return elements.map(el => ({
        width: el.getAttribute('width'),
        height: el.getAttribute('height'),
        parent: el.parentElement?.parentElement?.textContent?.substring(0, 50)
      }));
    });
    console.log(`  Found ${charts.length} charts:`);
    charts.forEach((c, i) => console.log(`    ${i + 1}. ${c.width}x${c.height} - "${c.parent}..."`));

    // Test 4: Check for "Top Vendor Performance" section
    console.log('\nTest 4: Checking Vendor Performance Chart...');
    const vendorChartSection = await page.$('text=Top Vendor Performance');
    if (vendorChartSection) {
      console.log('  ✅ Vendor Performance section found');

      // Check the chart bars
      const bars = await page.$$('svg .recharts-bar-rectangle');
      console.log(`  Found ${bars.length} bar elements in charts`);

      // Check for any data in the vendor performance chart area
      const vendorChartArea = await page.$('text=Top Vendor Performance');
      if (vendorChartArea) {
        const parent = await vendorChartArea.evaluateHandle(el => el.closest('div[class*="Paper"], div[class*="paper"]'));
        if (parent) {
          const chartContent = await parent.evaluate(el => el.innerHTML);
          const hasOnTimeData = chartContent.includes('On-Time') || chartContent.includes('on_time');
          console.log(`  Chart has On-Time data: ${hasOnTimeData}`);
        }
      }
    } else {
      console.log('  ❌ Vendor Performance section NOT found');
    }

    // Test 5: Test clicking on Next Actions items
    console.log('\nTest 5: Testing Next Actions Click (potential crash point)...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Find clickable action items
    const actionItems = await page.$$('[class*="MuiBox"] >> text=Critical Alert');
    console.log(`  Found ${actionItems.length} Critical Alert items`);

    if (actionItems.length > 0) {
      console.log('  Clicking first action item...');
      try {
        await actionItems[0].click();
        await page.waitForTimeout(2000);

        const currentUrl = page.url();
        console.log(`  Navigated to: ${currentUrl}`);

        if (currentUrl.includes('/projects/')) {
          console.log('  ✅ Successfully navigated to project detail');
          await page.screenshot({ path: `${SCREENSHOT_DIR}/project-from-action.png`, fullPage: true });
        }
      } catch (e) {
        console.log(`  ❌ Click failed: ${e.message}`);
      }
    }

    // Test 6: Test clicking on Recent Activity items
    console.log('\nTest 6: Testing Recent Activity Click (potential crash point)...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const activityItems = await page.$$('text=WO-');
    console.log(`  Found ${activityItems.length} Work Order items`);

    if (activityItems.length > 0) {
      console.log('  Clicking first activity item...');
      try {
        await activityItems[0].click();
        await page.waitForTimeout(2000);

        const currentUrl = page.url();
        console.log(`  Navigated to: ${currentUrl}`);

        if (currentUrl.includes('/projects/')) {
          console.log('  ✅ Successfully navigated to project detail');
        }
      } catch (e) {
        console.log(`  ❌ Click failed: ${e.message}`);
      }
    }

    // Test 7: Check for console errors
    console.log('\nTest 7: Console Errors Check...');
    if (consoleErrors.length > 0) {
      console.log(`  Found ${consoleErrors.length} console errors:`);
      consoleErrors.forEach((e, i) => console.log(`    ${i + 1}. ${e.substring(0, 100)}`));
    } else {
      console.log('  ✅ No console errors');
    }

    // Test 8: Check for failed requests
    console.log('\nTest 8: Failed Requests Check...');
    if (failedRequests.length > 0) {
      console.log(`  Found ${failedRequests.length} failed requests:`);
      failedRequests.forEach((r, i) => console.log(`    ${i + 1}. ${r.url} - ${r.failure}`));
    } else {
      console.log('  ✅ No failed requests');
    }

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('SUMMARY');
    console.log('='.repeat(60));
    console.log(`Charts found: ${charts.length}`);
    console.log(`Console errors: ${consoleErrors.length}`);
    console.log(`Failed requests: ${failedRequests.length}`);

    // Check vendor performance specifically
    if (vendorPerfResponse.data?.data) {
      console.log(`\nVendor Performance Data Fields:`);
      const firstVendor = vendorPerfResponse.data.data[0];
      if (firstVendor) {
        Object.keys(firstVendor).forEach(k => {
          console.log(`  - ${k}: ${firstVendor[k]}`);
        });
      }
    }

  } catch (error) {
    console.error('\n❌ Test Error:', error.message);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/dashboard-error.png`, fullPage: true });
  } finally {
    await browser.close();
  }
}

testDashboardDetailed().catch(console.error);
