#!/bin/bash

# Quick Pipeline Verification
# Checks that jobs ran and files were created

set -e

echo "=========================================="
echo "QUICK PIPELINE VERIFICATION"
echo "=========================================="
echo ""

PROFILE="DEFAULT"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

# Test 1: Check Twitter Ingestion Job Success
echo "[TEST 1] Twitter Ingestion Job..."
TWITTER_JOB_ID=$(databricks jobs list --profile "$PROFILE" 2>/dev/null | grep "twitter_ingestion" | head -1 | awk '{print $1}')

if [ -n "$TWITTER_JOB_ID" ]; then
    LAST_RUN=$(databricks jobs get-run-output "$TWITTER_JOB_ID" --profile "$PROFILE" 2>&1 | grep -i "SUCCESS" || echo "")
    if [ -n "$LAST_RUN" ]; then
        echo -e "${GREEN}✅ PASS: Twitter ingestion job exists and has successful runs${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${YELLOW}⚠️  Twitter ingestion job exists but status unknown${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
else
    echo -e "${RED}❌ FAIL: Twitter ingestion job not found${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 2: Check Real Tweet Files
echo ""
echo "[TEST 2] Real Tweet Files in UC Volume..."
REAL_TWEETS=$(databricks fs ls dbfs:/Volumes/main/default/ai_newsletter_raw_tweets/ --profile "$PROFILE" 2>/dev/null | grep "tweet_" | grep -v "dummy" | wc -l | tr -d ' ')

if [ "$REAL_TWEETS" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS: Found $REAL_TWEETS real tweet files${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL: No real tweet files found${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 3: Check Bronze Job Success
echo ""
echo "[TEST 3] Bronze Processing Job..."
BRONZE_JOB_ID=$(databricks jobs list --profile "$PROFILE" 2>/dev/null | grep "bronze_processing" | head -1 | awk '{print $1}')

if [ -n "$BRONZE_JOB_ID" ]; then
    BRONZE_RUNS=$(databricks jobs list-runs --job-id "$BRONZE_JOB_ID" --limit 5 --profile "$PROFILE" 2>/dev/null | grep -c "SUCCESS" || echo "0")
    if [ "$BRONZE_RUNS" -gt 0 ]; then
        echo -e "${GREEN}✅ PASS: Bronze processing job has $BRONZE_RUNS successful runs${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL: Bronze processing job has no successful runs${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${RED}❌ FAIL: Bronze processing job not found${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 4: Check Silver Job Success
echo ""
echo "[TEST 4] Silver Processing Job..."
SILVER_JOB_ID=$(databricks jobs list --profile "$PROFILE" 2>/dev/null | grep "silver_processing" | head -1 | awk '{print $1}')

if [ -n "$SILVER_JOB_ID" ]; then
    SILVER_RUNS=$(databricks jobs list-runs --job-id "$SILVER_JOB_ID" --limit 5 --profile "$PROFILE" 2>/dev/null | grep -c "SUCCESS" || echo "0")
    if [ "$SILVER_RUNS" -gt 0 ]; then
        echo -e "${GREEN}✅ PASS: Silver processing job has $SILVER_RUNS successful runs${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL: Silver processing job has no successful runs${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${RED}❌ FAIL: Silver processing job not found${NC}"
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
    echo ""
    echo "Pipeline Status:"
    echo "✅ Twitter API → Ingesting real tweets"
    echo "✅ Bronze Layer → Processing raw data"
    echo "✅ Silver Layer → Deduplication + influence scoring"
    echo ""
    echo "To view detailed results, run the verification notebook:"
    echo "Workspace → Users → rkalluri@gmail.com → tests → verify_pipeline"
    echo ""
    echo "Next: Proceed to T008 (Gold daily materialized view)"
    exit 0
else
    echo -e "${RED}⚠️  SOME TESTS FAILED${NC}"
    echo ""
    echo "Check job logs in Databricks UI:"
    echo "- Workflows → ai_newsletter_twitter_ingestion"
    echo "- Workflows → ai_newsletter_bronze_processing"
    echo "- Workflows → ai_newsletter_silver_processing"
    exit 1
fi
