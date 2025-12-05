const { chromium } = require('playwright');
const fs = require('fs');

const BASE_URL = 'http://localhost:5001';
const SCREENSHOT_DIR = './screenshots';

async function testVendors() {
  console.log('Starting Vendors Page Tests...\n');

  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await context.newPage();

  try {
    // Test 1: Navigate to Vendors page
    console.log('Test 1: Navigating to Vendors page...');
    await page.goto(`${BASE_URL}/vendors`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    await page.screenshot({ path: `${SCREENSHOT_DIR}/vendors-page.png`, fullPage: true });
    console.log('  Screenshot: vendors-page.png\n');

    // Test 2: Check Vendors List API
    console.log('Test 2: Checking Vendors List API...');
    const vendorsResponse = await page.evaluate(async () => {
      const res = await fetch('/api/v1/vendors');
      return res.json();
    });
    console.log(`  Total vendors: ${vendorsResponse.data?.length || 0}`);
    if (vendorsResponse.data?.length > 0) {
      console.log('  First vendor sample:');
      console.log(JSON.stringify(vendorsResponse.data[0], null, 2));
    }

    // Test 3: Check Vendor Metrics API for first vendor
    console.log('\nTest 3: Checking Vendor Metrics API...');
    if (vendorsResponse.data?.length > 0) {
      const firstVendorId = vendorsResponse.data[0].id || vendorsResponse.data[0].vendor_id;
      console.log(`  Fetching metrics for vendor: ${firstVendorId}`);

      const metricsResponse = await page.evaluate(async (vendorId) => {
        const res = await fetch(`/api/v1/vendors/${vendorId}/metrics`);
        return res.json();
      }, firstVendorId);

      console.log('  Vendor Metrics Response:');
      console.log(JSON.stringify(metricsResponse, null, 2));
    }

    // Test 4: Check Dashboard Vendor Performance API
    console.log('\nTest 4: Checking Dashboard Vendor Performance API...');
    const perfResponse = await page.evaluate(async () => {
      const res = await fetch('/api/v1/dashboard/vendor-performance?limit=10');
      return res.json();
    });
    console.log('  Vendor Performance Response:');
    console.log(JSON.stringify(perfResponse, null, 2));

    // Test 5: Check page elements for zero values
    console.log('\nTest 5: Checking for zero values on page...');
    const pageContent = await page.content();

    // Find all table cells or stat values
    const tableData = await page.$$eval('td, th', elements => {
      return elements.map(el => el.textContent?.trim()).filter(t => t);
    });
    console.log('  Table cell values (sample):');
    console.log(tableData.slice(0, 30).join(' | '));

    // Check for "0%" or "0" values
    const zeroValues = await page.$$eval('*', elements => {
      return elements
        .filter(el => {
          const text = el.textContent?.trim();
          return (text === '0' || text === '0%' || text === '0.0%') && el.children.length === 0;
        })
        .map(el => ({
          tag: el.tagName,
          text: el.textContent?.trim(),
          parent: el.parentElement?.textContent?.trim().substring(0, 80)
        }))
        .slice(0, 20);
    });
    console.log(`\n  Found ${zeroValues.length} elements showing zero:`);
    zeroValues.forEach((el, i) => {
      console.log(`    ${i + 1}. <${el.tag}> "${el.text}" in: "${el.parent}"`);
    });

    // Test 6: Click on a vendor to see detail
    console.log('\nTest 6: Testing Vendor Detail Navigation...');
    const vendorRows = await page.$$('table tbody tr');
    if (vendorRows.length > 0) {
      // Try to click the first vendor row or a link within it
      const firstRow = vendorRows[0];
      const viewButton = await firstRow.$('button, a, [role="button"]');
      if (viewButton) {
        await viewButton.click();
        await page.waitForTimeout(2000);
        await page.screenshot({ path: `${SCREENSHOT_DIR}/vendor-detail.png`, fullPage: true });
        console.log('  Screenshot: vendor-detail.png');

        // Check the vendor detail page
        const currentUrl = page.url();
        console.log(`  Current URL: ${currentUrl}`);

        if (currentUrl.includes('/vendors/')) {
          // Check metrics on detail page
          const detailMetrics = await page.$$eval('[class*="Card"], [class*="Stat"], [class*="metric"]', elements => {
            return elements.map(el => el.textContent?.trim().substring(0, 100));
          });
          console.log('  Detail page metrics:');
          detailMetrics.slice(0, 10).forEach((m, i) => console.log(`    ${i + 1}. ${m}`));
        }
      }
    }

    // Test 7: Check vendor_metrics table data via API
    console.log('\nTest 7: Checking raw vendor_metrics data...');
    // This would require a direct SQL query - let's check what the API returns

    console.log('\n' + '='.repeat(60));
    console.log('SUMMARY');
    console.log('='.repeat(60));
    console.log(`Total Vendors: ${vendorsResponse.data?.length || 0}`);
    console.log(`Vendors with on_time_percentage in API: ${
      perfResponse.data?.filter(v => v.on_time_percentage !== undefined).length || 0
    }`);

    // List vendors and their on-time percentages
    if (perfResponse.data) {
      console.log('\nVendor Performance Data:');
      perfResponse.data.forEach((v, i) => {
        console.log(`  ${i + 1}. ${v.vendor_name}: on_time_percentage=${v.on_time_percentage}, total=${v.total_projects}, completed=${v.completed}`);
      });
    }

  } catch (error) {
    console.error('\n❌ Test Error:', error.message);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/vendors-error.png`, fullPage: true });
  } finally {
    await browser.close();
  }
}

testVendors().catch(console.error);
