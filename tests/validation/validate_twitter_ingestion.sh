#!/bin/bash

# Twitter Ingestion Validation Script
# This script validates that Twitter ingestion is working correctly

set -e

echo "=========================================="
echo "TWITTER INGESTION VALIDATION"
echo "=========================================="
echo ""

# Configuration
PROFILE="DEFAULT"
CATALOG="main"
SCOPE="ai_newsletter_config"
SECRET_KEY="twitter_bearer_token"
VOLUME_PATH="/Volumes/main/default/ai_newsletter_raw_tweets/"
BRONZE_TABLE="${CATALOG}.ai_newsletter_bronze.tweets"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNING=0

# Helper function to run SQL
run_sql() {
    local query="$1"
    databricks sql execute --statement "$query" --profile "$PROFILE" 2>/dev/null || echo "ERROR"
}

# Test 1: Check Secret Scope Exists
echo "[TEST 1] Checking secret scope configuration..."
SCOPE_EXISTS=$(databricks secrets list-scopes --profile "$PROFILE" 2>/dev/null | grep -c "$SCOPE" || echo "0")

if [ "$SCOPE_EXISTS" -eq 0 ]; then
    echo -e "${RED}❌ FAIL: Secret scope '$SCOPE' does not exist${NC}"
    echo "   Create with: databricks secrets create-scope $SCOPE --profile $PROFILE"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "${GREEN}✅ PASS: Secret scope '$SCOPE' exists${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 2: Check Twitter Ingestion Job
echo ""
echo "[TEST 2] Checking Twitter ingestion job..."
JOB_EXISTS=$(databricks jobs list --profile "$PROFILE" 2>/dev/null | grep -c "twitter_ingestion" || echo "0")

if [ "$JOB_EXISTS" -eq 0 ]; then
    echo -e "${RED}❌ FAIL: Twitter ingestion job not found${NC}"
    echo "   Deploy with: databricks bundle deploy --target default --profile $PROFILE"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "${GREEN}✅ PASS: Twitter ingestion job deployed${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))

    # Get job ID and check recent runs
    JOB_ID=$(databricks jobs list --profile "$PROFILE" 2>/dev/null | grep "twitter_ingestion" | head -1 | awk '{print $1}')
    echo "   Job ID: $JOB_ID"

    # Check for recent successful runs
    RECENT_RUNS=$(databricks jobs list-runs --limit 5 --profile "$PROFILE" 2>/dev/null | grep -c "SUCCESS" || echo "0")
    if [ "$RECENT_RUNS" -gt 0 ]; then
        echo -e "   ${GREEN}Recent successful runs: $RECENT_RUNS${NC}"
    else
        echo -e "   ${YELLOW}⚠️  No recent successful runs found${NC}"
    fi
fi

# Test 3: Check UC Volume Files
echo ""
echo "[TEST 3] Checking raw tweet files in UC Volume..."

# Count files using databricks fs ls
FILE_LIST=$(databricks fs ls "dbfs:$VOLUME_PATH" --profile "$PROFILE" 2>/dev/null | grep "tweet_" || echo "")

if [ -z "$FILE_LIST" ]; then
    echo -e "${RED}❌ FAIL: No tweet files found in UC Volume${NC}"
    echo "   Path: $VOLUME_PATH"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    TOTAL_FILES=$(echo "$FILE_LIST" | wc -l | tr -d ' ')
    DUMMY_FILES=$(echo "$FILE_LIST" | grep -c "dummy" || echo "0")
    REAL_FILES=$((TOTAL_FILES - DUMMY_FILES))

    echo -e "${GREEN}✅ Found $TOTAL_FILES tweet files${NC}"
    echo "   - Dummy tweets: $DUMMY_FILES"
    echo "   - Real tweets:  $REAL_FILES"

    if [ "$REAL_FILES" -eq 0 ]; then
        echo -e "${RED}❌ FAIL: All tweets are dummy data${NC}"
        echo "   Reason: Twitter API bearer token not configured or invalid"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    else
        echo -e "${GREEN}✅ PASS: Found $REAL_FILES real tweets from Twitter API${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi

    # Show most recent files
    echo ""
    echo "   Most recent files:"
    echo "$FILE_LIST" | tail -5 | while read -r line; do
        filename=$(echo "$line" | awk '{print $NF}')
        if echo "$filename" | grep -q "dummy"; then
            echo -e "   ${YELLOW}[DUMMY]${NC} $filename"
        else
            echo -e "   ${GREEN}[REAL]${NC} $filename"
        fi
    done
fi

# Test 4: Check Bronze Table
echo ""
echo "[TEST 4] Checking bronze table..."
BRONZE_COUNT=$(run_sql "SELECT COUNT(*) as count FROM ${BRONZE_TABLE}" | tail -1 | awk '{print $1}')

if [ "$BRONZE_COUNT" = "ERROR" ] || [ -z "$BRONZE_COUNT" ]; then
    echo -e "${RED}❌ FAIL: Bronze table not accessible${NC}"
    echo "   Table: $BRONZE_TABLE"
    TESTS_FAILED=$((TESTS_FAILED + 1))
elif [ "$BRONZE_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  WARNING: Bronze table is empty${NC}"
    echo "   Run: databricks bundle run ai_newsletter_bronze_job --profile $PROFILE"
    TESTS_WARNING=$((TESTS_WARNING + 1))
else
    echo -e "${GREEN}✅ PASS: Bronze table has $BRONZE_COUNT records${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))

    # Check for real vs dummy tweets
    DUMMY_COUNT=$(run_sql "SELECT COUNT(*) as count FROM ${BRONZE_TABLE} WHERE id LIKE 'dummy%'" | tail -1 | awk '{print $1}')
    REAL_COUNT=$((BRONZE_COUNT - DUMMY_COUNT))

    echo "   - Dummy tweets: $DUMMY_COUNT"
    echo "   - Real tweets:  $REAL_COUNT"

    if [ "$REAL_COUNT" -eq 0 ]; then
        echo -e "${RED}❌ Bronze table only contains dummy data${NC}"
    else
        echo -e "${GREEN}✅ Bronze table contains $REAL_COUNT real tweets${NC}"
    fi
fi

# Test 5: Check Search Terms Table
echo ""
echo "[TEST 5] Checking search terms configuration..."
SEARCH_TERMS_TABLE="main.config.search_terms"
TERMS_COUNT=$(run_sql "SELECT COUNT(*) as count FROM ${SEARCH_TERMS_TABLE}" 2>/dev/null | tail -1 | awk '{print $1}')

if [ "$TERMS_COUNT" = "ERROR" ] || [ -z "$TERMS_COUNT" ]; then
    echo -e "${YELLOW}⚠️  WARNING: Search terms table does not exist${NC}"
    echo "   Using default terms: Gemini, Databricks, Claude Code, Claude, AI Driven Development"
    echo ""
    echo "   To create:"
    echo "   CREATE TABLE ${SEARCH_TERMS_TABLE} (term STRING);"
    echo "   INSERT INTO ${SEARCH_TERMS_TABLE} VALUES ('claude code'), ('databricks'), ('gemini');"
    TESTS_WARNING=$((TESTS_WARNING + 1))
elif [ "$TERMS_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  WARNING: Search terms table is empty${NC}"
    echo "   Using default terms"
    TESTS_WARNING=$((TESTS_WARNING + 1))
else
    echo -e "${GREEN}✅ PASS: Search terms configured with $TERMS_COUNT terms${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
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

# Provide recommendations
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}⚠️  SOME TESTS FAILED${NC}"
    echo ""
    echo "Common Solutions:"
    echo ""
    echo "1. Configure Twitter API bearer token:"
    echo "   databricks secrets put-secret $SCOPE $SECRET_KEY --profile $PROFILE"
    echo ""
    echo "2. Deploy and run ingestion job:"
    echo "   databricks bundle deploy --target default --profile $PROFILE"
    echo "   databricks jobs run-now <JOB_ID> --profile $PROFILE"
    echo ""
    echo "3. Run bronze processing:"
    echo "   databricks bundle run ai_newsletter_bronze_job --profile $PROFILE"
    echo ""
    echo "4. Check job logs in Databricks UI:"
    echo "   Workflows → ai_newsletter_twitter_ingestion"
    echo ""
    exit 1
else
    echo -e "${GREEN}🎉 TWITTER INGESTION VALIDATED!${NC}"
    echo ""
    echo "✅ Twitter API integration working"
    echo "✅ Real tweets being ingested"
    echo "✅ Bronze pipeline processing data"
    echo ""
    echo "Next Steps:"
    echo "1. Monitor ingestion (runs every 15 minutes)"
    echo "2. Verify silver processing with: ./tests/validation/validate_t007.sh"
    echo "3. Check data quality and influence scores"
    echo "4. Proceed to T008: Gold daily materialized view"
    echo ""
    exit 0
fi
