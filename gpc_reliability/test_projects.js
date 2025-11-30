const { chromium } = require('playwright');
const fs = require('fs');

const BASE_URL = 'http://localhost:5001';
const SCREENSHOT_DIR = './screenshots';

async function testProjects() {
  console.log('Starting Projects Page Tests...\n');

  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await context.newPage();

  // Track API errors
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('/api/v1/') && response.status() >= 400) {
      console.log(`  ❌ API Error [${url.split('/api/v1/')[1]}]: ${response.status()}`);
      try {
        const body = await response.text();
        console.log(`     ${body.substring(0, 150)}`);
      } catch (e) {}
    }
  });

  try {
    // Test 1: Navigate to Projects page
    console.log('Test 1: Navigating to Projects page...');
    await page.goto(`${BASE_URL}/projects`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/projects-page.png`, fullPage: true });
    console.log('  Screenshot: projects-page.png\n');

    // Test 2: Check Projects List API
    console.log('Test 2: Checking Projects List API...');
    const projectsResponse = await page.evaluate(async () => {
      const res = await fetch('/api/v1/projects');
      return res.json();
    });
    console.log(`  Total projects: ${projectsResponse.total || projectsResponse.data?.length || 0}`);
    if (projectsResponse.data?.length > 0) {
      console.log('  First project sample:');
      const firstProject = projectsResponse.data[0];
      console.log(JSON.stringify(firstProject, null, 2));

      // Check for specific fields
      console.log('\n  Field check:');
      console.log(`    - target_date: ${firstProject.target_date || firstProject.expected_completion_date || 'NOT FOUND'}`);
      console.log(`    - progress_percentage: ${firstProject.progress_percentage ?? 'NOT FOUND'}`);
      console.log(`    - start_date: ${firstProject.start_date || firstProject.authorized_date || 'NOT FOUND'}`);
    }

    // Test 3: Check table/card structure
    console.log('\nTest 3: Checking Page Structure...');

    // Check for table rows
    const tableRows = await page.$$('table tbody tr');
    console.log(`  Table rows found: ${tableRows.length}`);

    // Check for project cards
    const projectCards = await page.$$('[class*="Card"], [class*="card"]');
    console.log(`  Card elements found: ${projectCards.length}`);

    // Get all visible text content
    const pageText = await page.evaluate(() => document.body.innerText);

    // Check for key data
    console.log('\n  Content check:');
    console.log(`    - Contains "Target": ${pageText.includes('Target')}`);
    console.log(`    - Contains "Progress": ${pageText.includes('Progress')}`);
    console.log(`    - Contains "View Details": ${pageText.includes('View Details') || pageText.includes('View')}`);
    console.log(`    - Contains "%": ${pageText.includes('%')}`);

    // Test 4: Look for View Details buttons
    console.log('\nTest 4: Looking for View Details buttons...');
    const viewButtons = await page.$$('button:has-text("View"), a:has-text("View"), button:has-text("Details")');
    console.log(`  Found ${viewButtons.length} View/Details buttons`);

    // Also check for any clickable elements in table rows
    const rowButtons = await page.$$('table tbody tr button, table tbody tr a');
    console.log(`  Found ${rowButtons.length} buttons/links in table rows`);

    // Test 5: Try clicking View Details
    console.log('\nTest 5: Testing View Details functionality...');

    // Try different selectors for view details
    const viewDetailsSelectors = [
      'button:has-text("View Details")',
      'button:has-text("View")',
      'a:has-text("View")',
      '[aria-label*="view"]',
      '[aria-label*="View"]',
      'table tbody tr:first-child button',
      'table tbody tr:first-child a',
    ];

    let clickedSuccessfully = false;
    for (const selector of viewDetailsSelectors) {
      const element = await page.$(selector);
      if (element) {
        console.log(`  Found element with selector: ${selector}`);
        try {
          await element.click();
          await page.waitForTimeout(2000);
          const newUrl = page.url();
          console.log(`  After click, URL: ${newUrl}`);
          if (newUrl.includes('/projects/')) {
            console.log('  ✅ Successfully navigated to project detail');
            clickedSuccessfully = true;
            await page.screenshot({ path: `${SCREENSHOT_DIR}/project-detail.png`, fullPage: true });
            console.log('  Screenshot: project-detail.png');
            break;
          } else {
            // Go back and try next selector
            await page.goto(`${BASE_URL}/projects`, { waitUntil: 'networkidle' });
            await page.waitForTimeout(1000);
          }
        } catch (e) {
          console.log(`  Click failed: ${e.message}`);
        }
      }
    }

    if (!clickedSuccessfully) {
      console.log('  ❌ Could not find working View Details button');

      // Check what's in the first row
      const firstRowContent = await page.$eval('table tbody tr:first-child', el => el.innerHTML);
      console.log('\n  First row HTML (truncated):');
      console.log(`  ${firstRowContent.substring(0, 500)}...`);
    }

    // Test 6: Check column headers
    console.log('\nTest 6: Checking Table Headers...');
    const headers = await page.$$eval('table thead th, table th', elements =>
      elements.map(el => el.textContent?.trim())
    );
    console.log(`  Headers found: ${headers.join(' | ')}`);

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('SUMMARY');
    console.log('='.repeat(60));

    if (projectsResponse.data?.[0]) {
      const p = projectsResponse.data[0];
      console.log('First Project Fields Available:');
      Object.keys(p).forEach(k => {
        const val = p[k];
        const display = typeof val === 'object' ? JSON.stringify(val) : val;
        console.log(`  ${k}: ${display}`);
      });
    }

  } catch (error) {
    console.error('\n❌ Test Error:', error.message);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/projects-error.png`, fullPage: true });
  } finally {
    await browser.close();
  }
}

testProjects().catch(console.error);
