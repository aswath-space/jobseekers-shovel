# Troubleshooting Guide

## Ingestion Issues

### No Jobs Ingested

**Symptom**: Running ingestion produces empty or no output file

**Causes**:
1. Invalid board token in `companies.yaml`
2. Company not using supported platform (Greenhouse/Lever)
3. Network connectivity issues
4. Rate limiting

**Solutions**:
1. Verify board token by visiting careers page URL directly
2. Check adapter type matches actual platform
3. Test network: `curl https://boards.greenhouse.io/[token]/jobs?content=true`
4. Increase `rate_limit_delay_seconds` in `config/config.yaml`

**Example**:
```bash
# Test Greenhouse API
curl https://boards.greenhouse.io/anthropic/jobs?content=true

# Should return JSON with jobs array
```

### Import Errors

**Symptom**: `ModuleNotFoundError` or `ImportError`

**Cause**: Working directory not repository root

**Solution**:
```bash
# Ensure you're in repo root
cd /path/to/jobseekers-shovel

# Run from root with -m flag
python -m src.ingestion
```

### Rate Limiting Errors

**Symptom**: HTTP 429 errors or connection timeouts

**Cause**: Too many requests too quickly

**Solution**: Edit `config/config.yaml`:
```yaml
ingestion:
  rate_limit_delay_seconds: 2.0  # Increase from 1.0
```

### JSON Decode Errors

**Symptom**: `json.decoder.JSONDecodeError`

**Cause**: Corrupted data file or invalid API response

**Solutions**:
1. Delete corrupted file: `rm data/jobs/jobs-v1.json`
2. Restore from snapshot: Check `data/versions/` for backups
3. Run ingestion fresh

### Permission Denied

**Symptom**: Cannot write to `data/` directory

**Solutions**:
```bash
# Check permissions
ls -la data/

# Fix if needed
chmod -R u+w data/
```

## Frontend Issues

### No Jobs Displayed

**Symptom**: Frontend loads but shows empty list

**Causes**:
1. `jobs-v1.json` missing
2. JSON file malformed
3. Wrong file path

**Solutions**:
1. Verify file exists: `ls data/jobs/jobs-v1.json`
2. Check JSON validity: `python -m json.tool data/jobs/jobs-v1.json`
3. Check browser console for fetch errors (F12)

### Filters Not Working

**Symptom**: Selecting filters shows no results

**Cause**: All jobs filtered out by selected criteria

**Solution**: Clear all filters, refresh page

### Application Tracking Not Saving

**Symptom**: Applications disappear on page reload

**Cause**: localStorage disabled or blocked

**Solutions**:
1. Check browser privacy settings
2. Enable localStorage in browser
3. Try different browser
4. Check incognito/private mode (localStorage often disabled)

### Search Slow

**Symptom**: Search takes >1 second with many jobs

**Cause**: Large dataset (>5000 jobs)

**Solutions**:
1. Apply status filter first to reduce dataset
2. Use more specific search terms
3. Consider pagination (future enhancement)

## GitHub Actions Issues

### Workflow Not Running

**Symptom**: Scheduled ingestion doesn't trigger

**Causes**:
1. Workflow disabled
2. Repository inactive
3. Incorrect cron syntax

**Solutions**:
1. Check Actions tab → Enable workflow
2. Make a commit to activate repository
3. Verify cron syntax: `0 2 * * *` (daily 2 AM UTC)

### Workflow Failing

**Symptom**: Actions show red X

**Causes**:
1. Test failures
2. Missing dependencies
3. Invalid configuration

**Solutions**:
1. Click failed run → View logs
2. Check "Run job ingestion" step for errors
3. Fix issues in code, push fix

### No Automatic Deployment

**Symptom**: Changes to frontend not reflected on GitHub Pages

**Causes**:
1. Deployment workflow not triggered
2. GitHub Pages disabled
3. Wrong source branch

**Solutions**:
1. Check deploy-frontend.yml workflow ran
2. Settings → Pages → Enable GitHub Pages
3. Verify source: GitHub Actions (not branch)

### Rate Limit Exceeded

**Symptom**: "API rate limit exceeded" in Actions logs

**Cause**: Too many runs in short period

**Solution**: Wait for rate limit reset (typically 1 hour)

## Data Integrity Issues

### Duplicate Jobs

**Symptom**: Same job appears multiple times

**Cause**: Different IDs or signatures from source

**Solution**: System should handle via repost detection. If persists, check:
1. Source identifier format changed
2. Normalization not handling variation
3. File `src/processing/normalizer.py` for missing rules

### Missing Temporal Data

**Symptom**: `first_seen` or `last_seen` dates incorrect

**Cause**: Clock skew or corrupted data

**Solutions**:
1. Check system time: `date`
2. Restore from snapshot if corrupted
3. Rerun ingestion to refresh timestamps

### Snapshot Corruption

**Symptom**: Cannot restore from snapshot

**Cause**: Incomplete write or filesystem error

**Solutions**:
1. Check snapshot validity: `python -m json.tool data/versions/snapshot.json`
2. Try older snapshot
3. Clean corrupted snapshots: Run versioning cleanup

```python
from src.storage.versioning import ArtifactVersionManager
vm = ArtifactVersionManager()
vm.cleanup_corrupted_snapshots()
```

## Test Failures

### Import Errors in Tests

**Symptom**: `ModuleNotFoundError` when running pytest

**Solution**:
```bash
# Ensure working directory is repo root
cd /path/to/jobseekers-shovel
pytest tests/
```

### Validation Tests Failing

**Symptom**: Repost detection rate below 90%

**Cause**: Matcher algorithm changed

**Solution**: Review changes to `src/processing/matcher.py`, ensure component-wise matching intact

### Flaky Tests

**Symptom**: Tests pass sometimes, fail others

**Cause**: Timing-dependent code or external dependencies

**Solution**: Check tests for:
1. Time-based logic (use fixed timestamps)
2. Network calls (should be mocked)
3. Filesystem races (ensure atomic operations)

## Configuration Issues

### Invalid YAML Syntax

**Symptom**: `yaml.scanner.ScannerError`

**Cause**: Syntax error in config file

**Solutions**:
1. Validate YAML: `yamllint config/companies.yaml`
2. Check indentation (use spaces, not tabs)
3. Quote special characters

### Missing Required Fields

**Symptom**: `KeyError` when loading config

**Cause**: Missing required field in company entry

**Solution**: Ensure all entries have:
```yaml
- id: company-id          # Required
  name: Company Name      # Required
  adapter_type: greenhouse # Required
  adapter_config:
    board_token: token    # Required
```

## Performance Issues

### Slow Ingestion

**Symptom**: Ingestion takes >30 minutes

**Causes**:
1. Too many companies
2. Rate limiting delays
3. Large job datasets

**Solutions**:
1. Reduce `rate_limit_delay_seconds` (carefully)
2. Ingest subset of companies
3. Run in parallel (future enhancement)

### High Memory Usage

**Symptom**: Process using >500 MB RAM

**Cause**: Very large dataset (>10K jobs)

**Solutions**:
1. Process companies sequentially
2. Implement streaming JSON writes
3. Consider database backend

## Common Error Messages

### "Connection refused"
**Cause**: Network down or API endpoint unreachable
**Solution**: Check network, verify API endpoint

### "Signature mismatch"
**Cause**: Data format changed, incompatible version
**Solution**: Delete data, run fresh ingestion

### "Permission denied writing to file"
**Cause**: Insufficient file permissions
**Solution**: `chmod u+w data/jobs/`

### "No module named 'src'"
**Cause**: Not running from repository root
**Solution**: `cd` to repo root, use `python -m src.ingestion`

## Getting Help

**Check logs**:
```bash
# Ingestion logs (if redirected)
cat ingestion.log

# GitHub Actions logs
Visit: Actions tab → Click failed run → View logs
```

**Verify installation**:
```bash
# Test imports
python -c "import src.ingestion; print('OK')"

# Run tests
pytest tests/ -v
```

**Debug mode**:
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m src.ingestion
```

**Report issues**: Include:
1. Error message (full traceback)
2. Configuration (sanitized)
3. Steps to reproduce
4. System info (OS, Python version)
