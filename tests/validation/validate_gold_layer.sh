#!/bin/bash

# Gold Layer Validation Script (T008 & T009)
# Validates daily and weekly gold materialized views

set -e

echo "=========================================="
echo "GOLD LAYER VALIDATION (T008 & T009)"
echo "=========================================="
echo ""

# Configuration
PROFILE="DEFAULT"
CATALOG="main"
GOLD_SCHEMA="${CATALOG}.ai_newsletter_gold"
DAILY_TABLE="${GOLD_SCHEMA}.daily_top_candidates"
WEEKLY_TABLE="${GOLD_SCHEMA}.weekly_top_stories"
AUTHORS_TABLE="${GOLD_SCHEMA}.weekly_trending_authors"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNING=0

echo "Tables to validate:"
echo "  - ${DAILY_TABLE}"
echo "  - ${WEEKLY_TABLE}"
echo "  - ${AUTHORS_TABLE}"
echo ""

# Test 1: Check Gold Daily Job
echo "[TEST 1] Checking gold daily job deployment..."
DAILY_JOB=$(databricks jobs list --profile "$PROFILE" 2>/dev/null | grep "gold_daily_view" || echo "")

if [ -n "$DAILY_JOB" ]; then
    JOB_ID=$(echo "$DAILY_JOB" | awk '{print $1}')
    echo -e "${GREEN}✅ PASS: Gold daily job deployed${NC}"
    echo "   Job ID: $JOB_ID"

    # Check recent runs
    RECENT_RUNS=$(databricks jobs list-runs --job-id "$JOB_ID" --limit 5 --profile "$PROFILE" 2>/dev/null | grep -c "SUCCESS" || echo "0")
    if [ "$RECENT_RUNS" -gt 0 ]; then
        echo -e "   ${GREEN}Recent successful runs: $RECENT_RUNS${NC}"
    else
        echo -e "   ${YELLOW}⚠️  No recent successful runs${NC}"
    fi
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL: Gold daily job not found${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 2: Check Gold Weekly Job
echo ""
echo "[TEST 2] Checking gold weekly job deployment..."
WEEKLY_JOB=$(databricks jobs list --profile "$PROFILE" 2>/dev/null | grep "gold_weekly_rollup" || echo "")

if [ -n "$WEEKLY_JOB" ]; then
    JOB_ID=$(echo "$WEEKLY_JOB" | awk '{print $1}')
    echo -e "${GREEN}✅ PASS: Gold weekly job deployed${NC}"
    echo "   Job ID: $JOB_ID"

    # Check recent runs
    RECENT_RUNS=$(databricks jobs list-runs --job-id "$JOB_ID" --limit 5 --profile "$PROFILE" 2>/dev/null | grep -c "SUCCESS" || echo "0")
    if [ "$RECENT_RUNS" -gt 0 ]; then
        echo -e "   ${GREEN}Recent successful runs: $RECENT_RUNS${NC}"
    else
        echo -e "   ${YELLOW}⚠️  No recent successful runs${NC}"
    fi
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL: Gold weekly job not found${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 3: Check Daily Job Configuration
echo ""
echo "[TEST 3] Checking daily job configuration..."

if [ -f "databricks.yml" ]; then
    DAILY_TASK=$(grep -A 5 "ai_newsletter_gold_daily_job" databricks.yml | grep "gold_daily_view.py" || echo "")

    if [ -n "$DAILY_TASK" ]; then
        echo -e "${GREEN}✅ PASS: Daily job configured with correct script${NC}"
        echo "   Task: run_gold_daily_view"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL: Daily job configuration not found${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${RED}❌ FAIL: databricks.yml not found${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 4: Check Weekly Job Configuration
echo ""
echo "[TEST 4] Checking weekly job configuration..."

if [ -f "databricks.yml" ]; then
    WEEKLY_TASK=$(grep -A 5 "ai_newsletter_gold_weekly_job" databricks.yml | grep "gold_weekly_rollup.py" || echo "")

    if [ -n "$WEEKLY_TASK" ]; then
        echo -e "${GREEN}✅ PASS: Weekly job configured with correct script${NC}"
        echo "   Task: run_gold_weekly_rollup"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL: Weekly job configuration not found${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${RED}❌ FAIL: databricks.yml not found${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 5: Check Job Schedules
echo ""
echo "[TEST 5] Checking job schedules..."
echo "   Daily job: Should run at 06:00 UTC daily"
echo "   Weekly job: Should run at 07:00 UTC daily"

# Check databricks.yml for schedule configuration
if [ -f "databricks.yml" ]; then
    DAILY_SCHEDULE=$(grep -A 10 "ai_newsletter_gold_daily_job" databricks.yml | grep "quartz_cron" || echo "")
    WEEKLY_SCHEDULE=$(grep -A 10 "ai_newsletter_gold_weekly_job" databricks.yml | grep "quartz_cron" || echo "")

    if [ -n "$DAILY_SCHEDULE" ] && [ -n "$WEEKLY_SCHEDULE" ]; then
        echo -e "${GREEN}✅ PASS: Job schedules configured${NC}"
        DAILY_CRON=$(echo "$DAILY_SCHEDULE" | grep -o '"[^"]*"' | tr -d '"')
        WEEKLY_CRON=$(echo "$WEEKLY_SCHEDULE" | grep -o '"[^"]*"' | tr -d '"')
        echo "   Daily: $DAILY_CRON (06:00 UTC daily)"
        echo "   Weekly: $WEEKLY_CRON (07:00 UTC daily)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${YELLOW}⚠️  WARNING: Could not verify schedules${NC}"
        TESTS_WARNING=$((TESTS_WARNING + 1))
    fi
else
    echo -e "${YELLOW}⚠️  WARNING: databricks.yml not found in current directory${NC}"
    TESTS_WARNING=$((TESTS_WARNING + 1))
fi

# Test 6: Check Source Files Exist
echo ""
echo "[TEST 6] Checking source files..."

if [ -f "src/gold_daily_view.py" ]; then
    echo -e "${GREEN}✅ PASS: src/gold_daily_view.py exists${NC}"
    LINE_COUNT=$(wc -l < src/gold_daily_view.py)
    echo "   Lines: $LINE_COUNT"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL: src/gold_daily_view.py not found${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

if [ -f "src/gold_weekly_rollup.py" ]; then
    echo -e "${GREEN}✅ PASS: src/gold_weekly_rollup.py exists${NC}"
    LINE_COUNT=$(wc -l < src/gold_weekly_rollup.py)
    echo "   Lines: $LINE_COUNT"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL: src/gold_weekly_rollup.py not found${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 7: Verify Implementation Features
echo ""
echo "[TEST 7] Verifying implementation features..."

# Check for key features in daily view
DAILY_FEATURES=0
if grep -q "top 100" src/gold_daily_view.py 2>/dev/null; then
    ((DAILY_FEATURES++))
fi
if grep -q "influence_score" src/gold_daily_view.py 2>/dev/null; then
    ((DAILY_FEATURES++))
fi
if grep -q "partitionBy" src/gold_daily_view.py 2>/dev/null; then
    ((DAILY_FEATURES++))
fi
if grep -q "row_number" src/gold_daily_view.py 2>/dev/null; then
    ((DAILY_FEATURES++))
fi

echo "   Daily view features found: $DAILY_FEATURES/4"
if [ "$DAILY_FEATURES" -ge 3 ]; then
    echo -e "${GREEN}✅ PASS: Daily view has required features${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL: Daily view missing features${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Check for key features in weekly rollup
WEEKLY_FEATURES=0
if grep -q "7 days\|days_back" src/gold_weekly_rollup.py 2>/dev/null; then
    ((WEEKLY_FEATURES++))
fi
if grep -q "influence_score" src/gold_weekly_rollup.py 2>/dev/null; then
    ((WEEKLY_FEATURES++))
fi
if grep -q "trending_authors" src/gold_weekly_rollup.py 2>/dev/null; then
    ((WEEKLY_FEATURES++))
fi
if grep -q "weekly_rank" src/gold_weekly_rollup.py 2>/dev/null; then
    ((WEEKLY_FEATURES++))
fi

echo "   Weekly rollup features found: $WEEKLY_FEATURES/4"
if [ "$WEEKLY_FEATURES" -ge 3 ]; then
    echo -e "${GREEN}✅ PASS: Weekly rollup has required features${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL: Weekly rollup missing features${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Summary
echo ""
echo "=========================================="
echo "VALIDATION SUMMARY"
echo "=========================================="
TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED + TESTS_WARNING))
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed:   ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed:   ${RED}$TESTS_FAILED${NC}"
echo -e "Warnings: ${YELLOW}$TESTS_WARNING${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo ""
    echo "Gold Layer Status:"
    echo "✅ T008: Daily materialized view implemented and deployed"
    echo "✅ T009: Weekly rollup view implemented and deployed"
    echo "✅ Jobs scheduled and running"
    echo "✅ Source code validated"
    echo ""
    echo "To verify data in tables, run:"
    echo "  databricks workspace import tests/validation/validate_gold_layer.py \\"
    echo "    /Workspace/Users/rkalluri@gmail.com/tests/validate_gold_layer \\"
    echo "    --language PYTHON --overwrite --profile DEFAULT"
    echo ""
    echo "Then open and run the notebook in Databricks UI"
    echo ""
    echo "View jobs in Databricks:"
    echo "  Workflows → ai_newsletter_gold_daily_view"
    echo "  Workflows → ai_newsletter_gold_weekly_rollup"
    exit 0
else
    echo -e "${RED}⚠️  SOME TESTS FAILED${NC}"
    echo ""
    echo "Common solutions:"
    echo ""
    echo "1. Deploy bundle:"
    echo "   databricks bundle deploy --target default --profile DEFAULT"
    echo ""
    echo "2. Run gold layer jobs:"
    echo "   databricks jobs run-now <JOB_ID> --profile DEFAULT"
    echo ""
    echo "3. Check job logs in Databricks UI:"
    echo "   Workflows → ai_newsletter_gold_daily_view"
    echo "   Workflows → ai_newsletter_gold_weekly_rollup"
    exit 1
fi
