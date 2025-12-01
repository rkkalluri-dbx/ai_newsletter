#!/bin/bash

# T007 Validation Script - Silver Table Implementation
# This script validates the silver table processing implementation

set -e

echo "=========================================="
echo "T007 VALIDATION: Silver Table Processing"
echo "=========================================="
echo ""

# Configuration
PROFILE="DEFAULT"
CATALOG="main"
BRONZE_TABLE="${CATALOG}.ai_newsletter_bronze.tweets"
SILVER_TABLE="${CATALOG}.ai_newsletter_silver.tweets"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run SQL query and return result
run_sql() {
    local query="$1"
    databricks sql execute --statement "$query" --profile "$PROFILE" 2>/dev/null || echo "ERROR"
}

# Test 1: Check Bronze Table
echo "[TEST 1] Checking bronze table..."
BRONZE_COUNT=$(run_sql "SELECT COUNT(*) as count FROM ${BRONZE_TABLE}" | tail -1 | awk '{print $1}')

if [ "$BRONZE_COUNT" = "ERROR" ] || [ -z "$BRONZE_COUNT" ]; then
    echo -e "${RED}❌ FAIL: Bronze table not accessible${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
elif [ "$BRONZE_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  WARNING: Bronze table is empty (0 records)${NC}"
    echo "   Run: databricks bundle run ai_newsletter_bronze_job --profile $PROFILE"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "${GREEN}✅ PASS: Bronze table has $BRONZE_COUNT records${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 2: Check Silver Table Exists
echo ""
echo "[TEST 2] Checking silver table..."
SILVER_COUNT=$(run_sql "SELECT COUNT(*) as count FROM ${SILVER_TABLE}" | tail -1 | awk '{print $1}')

if [ "$SILVER_COUNT" = "ERROR" ] || [ -z "$SILVER_COUNT" ]; then
    echo -e "${RED}❌ FAIL: Silver table not accessible${NC}"
    echo "   Run: databricks bundle run ai_newsletter_silver_job --profile $PROFILE"
    TESTS_FAILED=$((TESTS_FAILED + 1))
elif [ "$SILVER_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  WARNING: Silver table is empty (0 records)${NC}"
    echo "   Run: databricks bundle run ai_newsletter_silver_job --profile $PROFILE"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "${GREEN}✅ PASS: Silver table has $SILVER_COUNT records${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 3: Check for Duplicates
echo ""
echo "[TEST 3] Checking for duplicate tweet_ids..."
DUPLICATE_COUNT=$(run_sql "
    SELECT COUNT(*) - COUNT(DISTINCT tweet_id) as duplicates
    FROM ${SILVER_TABLE}
" | tail -1 | awk '{print $1}')

if [ "$DUPLICATE_COUNT" = "ERROR" ] || [ -z "$DUPLICATE_COUNT" ]; then
    echo -e "${RED}❌ FAIL: Could not check for duplicates${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
elif [ "$DUPLICATE_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✅ PASS: No duplicates found${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL: Found $DUPLICATE_COUNT duplicates${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 4: Check Influence Scores
echo ""
echo "[TEST 4] Validating influence scores..."
NULL_SCORES=$(run_sql "
    SELECT SUM(CASE WHEN influence_score IS NULL THEN 1 ELSE 0 END) as null_count
    FROM ${SILVER_TABLE}
" | tail -1 | awk '{print $1}')

NEGATIVE_SCORES=$(run_sql "
    SELECT SUM(CASE WHEN influence_score < 0 THEN 1 ELSE 0 END) as negative_count
    FROM ${SILVER_TABLE}
" | tail -1 | awk '{print $1}')

if [ "$NULL_SCORES" = "ERROR" ] || [ "$NEGATIVE_SCORES" = "ERROR" ]; then
    echo -e "${RED}❌ FAIL: Could not validate influence scores${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
elif [ "$NULL_SCORES" -eq 0 ] && [ "$NEGATIVE_SCORES" -eq 0 ]; then
    echo -e "${GREEN}✅ PASS: All influence scores are valid (no nulls or negatives)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL: Found $NULL_SCORES null scores and $NEGATIVE_SCORES negative scores${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 5: Check Schema
echo ""
echo "[TEST 5] Checking silver table schema..."
COLUMN_COUNT=$(run_sql "
    SELECT COUNT(*) as count
    FROM main.information_schema.columns
    WHERE table_schema = 'ai_newsletter_silver'
      AND table_name = 'tweets'
" | tail -1 | awk '{print $1}')

if [ "$COLUMN_COUNT" = "ERROR" ] || [ -z "$COLUMN_COUNT" ]; then
    echo -e "${RED}❌ FAIL: Could not verify schema${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
elif [ "$COLUMN_COUNT" -eq 12 ]; then
    echo -e "${GREEN}✅ PASS: Schema has expected 12 columns${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  WARNING: Schema has $COLUMN_COUNT columns (expected 12)${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 6: Check Job Status
echo ""
echo "[TEST 6] Checking job deployment..."
JOB_EXISTS=$(databricks jobs list --profile "$PROFILE" 2>/dev/null | grep -c "ai_newsletter_silver_processing" || echo "0")

if [ "$JOB_EXISTS" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: Silver processing job is deployed${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL: Silver processing job not found${NC}"
    echo "   Run: databricks bundle deploy --target default --profile $PROFILE"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Summary
echo ""
echo "=========================================="
echo "VALIDATION SUMMARY"
echo "=========================================="
TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo "T007 implementation is validated."
    echo ""
    echo "Next steps:"
    echo "1. Monitor the silver job in Databricks UI"
    echo "2. Review influence score distribution"
    echo "3. Proceed to T008: Gold daily materialized view"
    exit 0
else
    echo -e "${RED}⚠️  SOME TESTS FAILED${NC}"
    echo "Review the output above for details."
    echo ""
    echo "Common solutions:"
    echo "1. Ensure bronze table has data:"
    echo "   databricks bundle run ai_newsletter_bronze_job --profile $PROFILE"
    echo ""
    echo "2. Run silver processing:"
    echo "   databricks bundle run ai_newsletter_silver_job --profile $PROFILE"
    echo ""
    echo "3. Check job logs in Databricks UI:"
    echo "   Workflows → ai_newsletter_silver_processing"
    exit 1
fi
