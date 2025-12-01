# Testing Suite - AI Newsletter

This directory contains all testing and validation scripts for the AI Newsletter project.

## Directory Structure

```
tests/
├── README.md                    # This file
├── validation/                  # End-to-end validation tests
│   ├── validate_t007.py        # T007: Silver table validation (Databricks)
│   ├── validate_t007.sh        # T007: Silver table validation (CLI)
│   └── VALIDATION_T007.md      # T007: Validation guide
├── integration/                 # Integration tests (future)
│   └── README.md
└── unit/                        # Unit tests (future)
    └── README.md
```

## Test Categories

### Validation Tests (`validation/`)

End-to-end validation tests that verify complete feature implementations against specifications.

**Current Tests:**
- `validate_t007.*` - Silver table implementation validation
  - Deduplication testing
  - Influence score calculation
  - Schema validation
  - Data quality checks

**How to Run:**
```bash
# CLI validation (quick - 2 minutes)
./tests/validation/validate_t007.sh

# Comprehensive validation (Databricks)
# Upload validate_t007.py to Databricks and run
```

### Integration Tests (`integration/`)

Tests that verify multiple components working together.

**Planned Tests:**
- Bronze → Silver → Gold pipeline flow
- Job orchestration and scheduling
- API integrations (Twitter, LLM, Email)
- Secret management

### Unit Tests (`unit/`)

Individual component/function tests.

**Planned Tests:**
- Influence score UDF
- Deduplication logic
- Data transformation functions
- Configuration parsing

## Running Tests

### Quick Validation (Recommended Start)

```bash
# Navigate to project root
cd /Users/rkalluri/projects/ai_newsletter

# Run validation for current task
./tests/validation/validate_t007.sh
```

### Comprehensive Validation

```bash
# Upload to Databricks
databricks workspace import tests/validation/validate_t007.py \
  /Workspace/Users/rkalluri@gmail.com/tests/validate_t007 \
  --language PYTHON \
  --profile DEFAULT

# Run in Databricks workspace
```

### CI/CD Integration (Future)

```bash
# Run all validation tests
./tests/run_all_validations.sh

# Run specific test suite
./tests/run_validation_suite.sh t007
```

## Test Development Guidelines

### Validation Tests

1. **Purpose**: Verify feature implementation against specification
2. **Scope**: End-to-end functionality
3. **Location**: `tests/validation/`
4. **Naming**: `validate_<task_id>.{py,sh}`
5. **Documentation**: Include corresponding `.md` guide

**Template Structure:**
```python
# 1. Prerequisites check
# 2. Component existence verification
# 3. Data quality validation
# 4. Functional correctness tests
# 5. Performance checks
# 6. Summary and recommendations
```

### Integration Tests

1. **Purpose**: Verify component interactions
2. **Scope**: Multiple components/services
3. **Location**: `tests/integration/`
4. **Naming**: `test_<feature>_integration.py`

### Unit Tests

1. **Purpose**: Test individual functions/methods
2. **Scope**: Single function or class
3. **Location**: `tests/unit/`
4. **Naming**: `test_<module_name>.py`
5. **Framework**: pytest (when added)

## Test Checklist Template

Use this checklist for each task validation:

```markdown
## [Task ID]: [Task Name]

### Prerequisites
- [ ] Source data available
- [ ] Dependencies deployed
- [ ] Permissions configured

### Core Functionality
- [ ] Component exists
- [ ] Expected output generated
- [ ] Schema/structure correct

### Data Quality
- [ ] No null values in required fields
- [ ] Data types correct
- [ ] Constraints satisfied

### Integration
- [ ] Upstream dependencies satisfied
- [ ] Downstream consumers work
- [ ] End-to-end flow complete

### Performance
- [ ] Execution time acceptable
- [ ] Resource usage reasonable
- [ ] Scalability verified
```

## Adding New Tests

### For New Task (e.g., T008)

1. **Create validation script:**
   ```bash
   touch tests/validation/validate_t008.sh
   chmod +x tests/validation/validate_t008.sh
   ```

2. **Create Databricks notebook:**
   ```bash
   touch tests/validation/validate_t008.py
   ```

3. **Create documentation:**
   ```bash
   touch tests/validation/VALIDATION_T008.md
   ```

4. **Follow existing patterns:**
   - Copy template from `validate_t007.*`
   - Update for new task requirements
   - Add to this README

### For Unit Tests (Future)

1. **Install pytest:**
   ```bash
   pip install pytest pytest-spark
   ```

2. **Create test file:**
   ```bash
   touch tests/unit/test_influence_score.py
   ```

3. **Write tests:**
   ```python
   import pytest
   from src.silver_processing import calculate_influence_score

   def test_influence_score_basic():
       score = calculate_influence_score(10, 5, 2, 1000)
       expected = (10 * 2) + (5 * 3) + (2 * 1) + (1000 / 1000)
       assert score == expected
   ```

4. **Run tests:**
   ```bash
   pytest tests/unit/
   ```

## Test Results

Track test results for each task:

| Task | Validation Script | Status | Last Run | Notes |
|------|------------------|--------|----------|-------|
| T007 | validate_t007.sh | ✅ Pass | 2025-12-01 | Silver table validated |
| T008 | validate_t008.sh | ⏳ Pending | - | Not implemented yet |
| T009 | validate_t009.sh | ⏳ Pending | - | Not implemented yet |

## Troubleshooting

### Common Issues

**Issue: Permission denied when running .sh scripts**
```bash
chmod +x tests/validation/*.sh
```

**Issue: Databricks CLI not found**
```bash
pip install databricks-cli
databricks configure --profile DEFAULT
```

**Issue: Table not found**
```bash
# Ensure upstream jobs have run
databricks bundle deploy --target default --profile DEFAULT
databricks bundle run <job_name> --profile DEFAULT
```

## Future Enhancements

- [ ] Add pytest framework for unit tests
- [ ] Create CI/CD pipeline integration
- [ ] Add performance benchmarking tests
- [ ] Create test data generators
- [ ] Add code coverage reporting
- [ ] Create automated test reports
- [ ] Add load testing for production validation

## Contributing

When adding new tests:
1. Follow existing naming conventions
2. Include both automated and manual test methods
3. Document expected results
4. Add troubleshooting section
5. Update this README
6. Include validation checklist
