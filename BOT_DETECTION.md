# Bot Detection System

This document explains how the AI Newsletter pipeline filters out bot-generated tweets to ensure only human-authored content is processed.

## Overview

The bot detection system uses **multi-heuristic analysis** of Twitter account metadata to identify likely automated accounts. It operates at the Twitter ingestion stage, before tweets are even saved to the UC Volume.

## Architecture

```
Twitter API → Bot Detection → UC Volume → Bronze → Silver → Gold
                    ↓
            Filter out bots
```

**Benefits of early filtering**:
- Saves storage costs (don't store bot tweets)
- Reduces processing costs (don't process bot content)
- Higher quality data from the start
- Better LLM summarization results

## Detection Criteria

### ✅ Trusted Accounts (Never Filtered)

- **Verified accounts**: Blue checkmark, business, or government verified accounts
- Conservative approach: If account has any verification, it's trusted

### ❌ Bot Indicators (Triggers Filtering)

| Indicator | Threshold | Rationale |
|-----------|-----------|-----------|
| **Account Age** | < 30 days | New accounts often created for spam/bots |
| **Follower Count** | < 10 followers | Legitimate accounts typically have some followers |
| **Following Ratio** | Following/Followers > 10:1 | Spam accounts follow many, have few followers |
| **Bio Keywords** | Contains "bot", "automated", etc. | Self-identified bots |

### Detection Logic Flow

```python
def is_likely_bot(tweet):
    1. If verified → NOT a bot ✅
    2. If account < 30 days old → IS a bot ❌
    3. If followers < 10 → IS a bot ❌
    4. If following/followers > 10:1 → IS a bot ❌
    5. If bio contains bot keywords → IS a bot ❌
    6. Otherwise → NOT a bot ✅
```

## Configuration

All thresholds are configurable at the top of `src/twitter_ingestion_script.py`:

```python
# Bot Detection Configuration
BOT_DETECTION_ENABLED = True                # Master switch
BOT_MIN_ACCOUNT_AGE_DAYS = 30               # Minimum account age
BOT_MIN_FOLLOWERS = 10                      # Minimum follower count
BOT_MAX_FOLLOWING_RATIO = 10                # Max following/followers ratio
BOT_KEYWORDS = [                            # Bio keywords indicating bots
    'bot',
    'automated',
    'auto-tweet',
    'auto tweet',
    'scheduled tweets'
]
```

### Tuning Recommendations

**For stricter filtering** (fewer bots, might filter some humans):
```python
BOT_MIN_ACCOUNT_AGE_DAYS = 90    # Only accounts 3+ months old
BOT_MIN_FOLLOWERS = 50           # More established accounts
BOT_MAX_FOLLOWING_RATIO = 5      # Tighter ratio
```

**For looser filtering** (allow more content, might include some bots):
```python
BOT_MIN_ACCOUNT_AGE_DAYS = 7     # 1 week old accounts OK
BOT_MIN_FOLLOWERS = 5            # Allow newer accounts
BOT_MAX_FOLLOWING_RATIO = 20     # More lenient ratio
```

**To disable entirely**:
```python
BOT_DETECTION_ENABLED = False
```

## Monitoring

The ingestion job provides detailed logging:

### Example Output

```
Fetched 100 tweets with author metadata.

✅ Landed tweet 1234567890 to /Volumes/...
✅ Landed tweet 1234567891 to /Volumes/...
🤖 Filtered out likely bot tweet 1234567892 (author: @spam_account, followers: 2)
🤖 Filtered out likely bot tweet 1234567893 (author: @newbot123, followers: 0)
⚠️  Filtered out non-English tweet 1234567894 (lang: es)

============================================================
INGESTION SUMMARY
============================================================
✅ Landed: 78 tweets from humans
⚠️  Filtered (language): 5 tweets
🤖 Filtered (bots): 17 tweets
Total fetched: 100 tweets
============================================================
```

### Metrics to Monitor

1. **Bot Filter Rate**: `filtered_bot / total_fetched`
   - Expected: 10-30% for typical queries
   - Too high (>50%): May be filtering legitimate accounts, loosen thresholds
   - Too low (<5%): May not be catching bots, tighten thresholds

2. **Landed Tweet Count**: Should be sufficient for newsletter content
   - Target: 50-80 tweets per ingestion run
   - If too low: Loosen filters or run more frequently

## API Request Details

The system requests additional user fields from Twitter API:

```python
"expansions": "author_id",
"user.fields": "created_at,public_metrics,verified,verified_type,description"
```

This retrieves:
- `created_at`: Account creation date (for age check)
- `public_metrics`: Followers, following counts
- `verified`: Verification status
- `verified_type`: Type of verification (blue, business, government)
- `description`: Account bio (for keyword checking)

## Limitations

### Current Approach
This is **heuristic-based detection** using simple rules. It's effective but not perfect.

**False Positives** (legitimate accounts filtered):
- New accounts from real people
- Accounts with few followers (lurkers, private accounts)
- Accounts that happen to match bot patterns

**False Negatives** (bots that pass through):
- Sophisticated bots with established profiles
- Compromised legitimate accounts
- Bots that don't match our heuristics

### Advanced Bot Detection (Future Enhancement)

For production systems at scale, consider:

1. **Botometer API Integration**
   - ML-based bot scoring (0-1 scale)
   - More accurate than heuristics
   - Requires additional API calls
   - Cost: ~$0.0001 per check

2. **Machine Learning Models**
   - Train custom bot classifier
   - Features: tweet patterns, timing, content similarity
   - Requires labeled training data

3. **Behavioral Analysis**
   - Track tweet frequency/timing
   - Detect automated patterns
   - Requires historical data

## Testing Bot Detection

### Test with Known Accounts

```python
# In Databricks notebook
test_accounts = [
    {'author_metadata': {'created_at': '2024-11-01T00:00:00Z', 'public_metrics': {'followers_count': 5, 'following_count': 1000}}},  # Should be filtered (new, low followers, bad ratio)
    {'author_metadata': {'verified': True, 'public_metrics': {'followers_count': 1000}}},  # Should pass (verified)
    {'author_metadata': {'created_at': '2020-01-01T00:00:00Z', 'public_metrics': {'followers_count': 500, 'following_count': 300}}},  # Should pass (old, good metrics)
]

for account in test_accounts:
    result = is_likely_bot(account)
    print(f"Bot: {result} - Account: {account}")
```

### Monitor Filter Effectiveness

1. Run ingestion job
2. Check job logs for filter counts
3. Manually review filtered tweets (check author profiles)
4. Adjust thresholds based on results

## Example: Adjusting for Your Use Case

### Use Case 1: Tech News Newsletter (Current Setup)
**Goal**: Quality tech discussions from established accounts
**Settings**: Current defaults (30 days, 10 followers, 10:1 ratio)
**Result**: Good balance of quality and quantity

### Use Case 2: Breaking News Aggregator
**Goal**: Get all tweets quickly, including from new accounts
**Settings**:
```python
BOT_MIN_ACCOUNT_AGE_DAYS = 7
BOT_MIN_FOLLOWERS = 5
BOT_MAX_FOLLOWING_RATIO = 20
```
**Result**: More content, some bot risk

### Use Case 3: Premium Analysis Service
**Goal**: Only highest quality sources
**Settings**:
```python
BOT_MIN_ACCOUNT_AGE_DAYS = 180
BOT_MIN_FOLLOWERS = 100
BOT_MAX_FOLLOWING_RATIO = 5
# Add: Filter for verified accounts only
```
**Result**: Very high quality, lower volume

## Deployment

Changes to configuration require redeployment:

```bash
# 1. Edit configuration in src/twitter_ingestion_script.py
# 2. Deploy bundle
databricks bundle deploy --target default --profile DEFAULT

# 3. Run ingestion to test
databricks jobs run-now <TWITTER_INGESTION_JOB_ID> --profile DEFAULT

# 4. Check logs for filter statistics
```

## Related Documentation

- [Twitter API v2 User Fields](https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/user)
- [Botometer API](https://botometer.osome.iu.edu/)
- [Twitter Best Practices for Bot Detection](https://developer.twitter.com/en/docs/twitter-api/best-practices)

## Support

For questions or issues with bot detection:
1. Check job logs for filtering statistics
2. Review filtered account profiles manually
3. Adjust thresholds as needed
4. Monitor impact on newsletter content quality
