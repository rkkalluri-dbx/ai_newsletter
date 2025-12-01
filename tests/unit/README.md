# Unit Tests

Unit tests verify individual functions and components in isolation.

## Planned Tests

### Silver Processing
- [ ] `test_calculate_influence_score()` - UDF testing
- [ ] `test_deduplication_logic()` - Window function
- [ ] `test_schema_validation()` - Schema correctness

### Gold Processing
- [ ] `test_top_n_selection()` - Top candidates logic
- [ ] `test_date_partitioning()` - Date-based queries
- [ ] `test_weekly_aggregation()` - 7-day rollup

### LLM Agent
- [ ] `test_prompt_formatting()` - Prompt template
- [ ] `test_story_filtering()` - Quality filters
- [ ] `test_api_error_handling()` - Error scenarios

### Newsletter Rendering
- [ ] `test_template_rendering()` - Jinja2 templates
- [ ] `test_markdown_to_html()` - Format conversion
- [ ] `test_email_formatting()` - Email structure

## Framework

Will use pytest with pytest-spark for PySpark testing:

```bash
pip install pytest pytest-spark
pytest tests/unit/
```

## Coming Soon

Unit tests will be added progressively as features are implemented.
