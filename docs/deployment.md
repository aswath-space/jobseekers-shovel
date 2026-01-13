# Deployment Guide

This guide covers deploying JobSeekers Shovel with automated ingestion and static frontend hosting.

## Overview

The deployment architecture consists of:

1. **GitHub Actions** - Scheduled job ingestion (daily at 2 AM UTC)
2. **GitHub Pages** - Static frontend hosting
3. **Git Repository** - Data artifact storage
4. **Local Backups** - Versioned snapshots (30-day retention)

## Prerequisites

- GitHub repository with Actions enabled
- GitHub Pages configured
- Python 3.11+ for local development

## Deployment Steps

### 1. Enable GitHub Actions

GitHub Actions workflows are located in `.github/workflows/`:

- `ingest-jobs.yml` - Scheduled job ingestion
- `deploy-frontend.yml` - Frontend deployment to GitHub Pages

**Configuration:**

1. Go to repository Settings → Actions → General
2. Enable "Read and write permissions" for workflows
3. Save changes

### 2. Configure GitHub Pages

1. Go to repository Settings → Pages
2. Source: "GitHub Actions"
3. Save configuration

The frontend will be deployed automatically on:
- Push to `main` branch (if frontend or data changes)
- Manual workflow trigger

### 3. Set Up Company Configuration

Create `config/companies.yml` with your target companies:

```yaml
companies:
  - id: anthropic
    name: Anthropic
    adapter: greenhouse
    sources:
      - url: https://boards.greenhouse.io/anthropic

  - id: openai
    name: OpenAI
    adapter: lever
    sources:
      - url: https://jobs.lever.co/openai
```

### 4. Initial Data Population

Run ingestion locally to create initial dataset:

```bash
python -m src.ingestion
```

This creates `data/jobs/jobs-v1.json` which will be:
- Committed to the repository
- Served by GitHub Pages
- Updated daily by GitHub Actions

### 5. Commit and Push

```bash
git add config/companies.yml data/jobs/jobs-v1.json
git commit -m "Initial deployment configuration"
git push origin main
```

## Automated Ingestion

### Schedule

Jobs are ingested daily at 2 AM UTC via GitHub Actions.

**To change schedule:**

Edit `.github/workflows/ingest-jobs.yml`:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Modify this line
```

Cron format: `minute hour day month weekday`

Examples:
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 0` - Weekly on Sunday
- `0 12 * * 1-5` - Weekdays at noon

### Manual Trigger

Trigger ingestion manually:

1. Go to Actions → Job Ingestion
2. Click "Run workflow"
3. Select branch and run

### Monitoring

View ingestion logs:

1. Go to Actions → Job Ingestion
2. Click on latest run
3. View logs for each step

Common issues:
- **Rate limiting**: Adjust `crawling.request_delay` in `config/ingestion.yml`
- **Adapter failures**: Check company URL and adapter configuration
- **Commit failures**: Verify workflow permissions

## Artifact Versioning

### Snapshot Creation

Each successful ingestion creates a timestamped snapshot:

- Location: `data/versions/`
- Format: `jobs-v1-YYYYMMDD-HHMMSS-microseconds.json`
- Retention: 30 most recent snapshots
- Auto-rotation: Deletes older snapshots

### Local Backup Management

View snapshots:

```python
from src.storage.versioning import ArtifactVersionManager

manager = ArtifactVersionManager()
snapshots = manager.list_snapshots()

for snap in snapshots:
    print(f"{snap['name']}: {snap['job_count']} jobs, {snap['size_bytes']} bytes")
```

Restore snapshot:

```python
manager.restore_snapshot('jobs-v1-20260113-120000-123456.json')
```

Clean corrupted snapshots:

```python
cleaned = manager.cleanup_corrupted_snapshots()
print(f"Removed {cleaned} corrupted snapshots")
```

### CI Artifacts

GitHub Actions also uploads artifacts:

- Name: `jobs-database-<run-number>`
- Retention: 90 days
- Access: Actions → Run → Artifacts section

## Frontend Deployment

### Automatic Deployment

Frontend deploys automatically when:
- `frontend/**` files change
- `data/jobs/jobs-v1.json` updates
- Workflow file changes

### Manual Deployment

Trigger frontend deployment:

1. Go to Actions → Deploy Frontend
2. Click "Run workflow"
3. Wait for deployment (1-2 minutes)

### Access

Once deployed, access at:

```
https://<username>.github.io/<repository-name>/
```

Example: `https://yourusername.github.io/jobseekers-shovel/`

### Custom Domain

To use custom domain:

1. Add `CNAME` file to `frontend/`:
   ```
   jobs.yourdomain.com
   ```

2. Configure DNS:
   - Type: CNAME
   - Name: jobs
   - Value: <username>.github.io

3. Enable HTTPS in GitHub Pages settings

## Configuration Reference

### Ingestion Configuration

`config/ingestion.yml`:

```yaml
schedule:
  frequency_hours: 24

crawling:
  user_agent: "JobSeekers-Shovel/1.0"
  request_delay: 2
  max_retries: 3

classification:
  similarity_threshold: 0.90
  repost_window_days: 30

lifecycle:
  close_timeout_days: 14
```

### Storage Configuration

Default paths (can be customized):

- Jobs data: `data/jobs/jobs-v1.json`
- Snapshots: `data/versions/`
- Archives: `data/archive/`
- Max versions: 30

## Security Considerations

### Repository Visibility

**Public repositories:**
- Job data is publicly visible
- Ensure no sensitive information in job descriptions
- Application data stored in browser LocalStorage (not in repo)

**Private repositories:**
- GitHub Pages works with private repos (Pro/Enterprise)
- Actions workflows still run
- Data remains private

### API Rate Limiting

Respect ATS platform limits:

- Configure delays in `config/ingestion.yml`
- Monitor for rate limit errors in Actions logs
- Adjust schedule if needed

### Data Privacy

- **Job data**: Sourced from public ATS platforms
- **Application tracking**: Stored locally in browser
- **No user accounts**: No authentication or central database
- **No PII**: System does not collect personal information

## Troubleshooting

### Ingestion Failures

**Problem**: Companies fail to fetch

**Solutions**:
- Verify URL accessibility
- Check adapter configuration
- Review rate limiting settings
- Check Actions logs for errors

### Frontend Not Updating

**Problem**: Changes not reflected on GitHub Pages

**Solutions**:
- Verify workflow completed successfully
- Check Actions → Deploy Frontend logs
- Clear browser cache
- Wait 2-3 minutes for CDN propagation

### Version Conflicts

**Problem**: Local and remote data differ

**Solutions**:
- Pull latest changes: `git pull origin main`
- Restore snapshot if needed
- Force sync by re-running ingestion

### Storage Limits

**Problem**: Repository size growing

**Solutions**:
- Snapshots rotate automatically (30-day retention)
- Archive old data to separate branch
- Use Git LFS for large files (if needed)

## Maintenance

### Regular Tasks

**Weekly**:
- Review Actions logs for failures
- Check frontend accessibility

**Monthly**:
- Verify company URLs still valid
- Review storage usage
- Update dependencies (`pip list --outdated`)

**Quarterly**:
- Review and update company list
- Test snapshot restore process
- Audit classification accuracy

### Updates

Update Python dependencies:

```bash
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
git commit -am "Update dependencies"
git push
```

Update GitHub Actions versions:

1. Check for action updates in `.github/workflows/`
2. Update version tags (e.g., `v4` → `v5`)
3. Test workflows after updating

## Rollback Procedures

### Data Rollback

Restore previous snapshot:

```python
from src.storage.versioning import ArtifactVersionManager

manager = ArtifactVersionManager()

# List available snapshots
snapshots = manager.list_snapshots()
print(snapshots[0]['name'])  # Most recent

# Restore specific snapshot
manager.restore_snapshot('<snapshot-name>')
```

### Code Rollback

Revert to previous commit:

```bash
git log --oneline  # Find commit hash
git revert <commit-hash>
git push origin main
```

### Frontend Rollback

GitHub Pages deployment history:

1. Go to Actions → Deploy Frontend
2. Find successful previous deployment
3. Re-run that workflow

## Performance Optimization

### Reduce Ingestion Time

- Adjust `crawling.request_delay` (balance speed vs. respect)
- Run parallel workflows for company subsets (advanced)
- Cache adapter results for unchanged data

### Reduce Storage Usage

- Lower `max_versions` in versioning config
- Compress snapshots (manual process)
- Archive closed jobs to separate file

### Improve Frontend Performance

- Enable CDN caching headers
- Minimize data file size (filter closed jobs)
- Lazy-load job details in modal

## Monitoring & Alerts

### GitHub Actions Notifications

Enable email notifications:

1. Settings → Notifications
2. Actions → ✓ Send notifications for failed workflows

### Custom Monitoring

Add monitoring script to workflow:

```yaml
- name: Check job count
  run: |
    JOBS=$(jq '.job_count' data/jobs/jobs-v1.json)
    if [ "$JOBS" -lt 10 ]; then
      echo "Warning: Low job count: $JOBS"
      exit 1
    fi
```

### Health Checks

Create health check endpoint (advanced):

```javascript
// frontend/health.json
{
  "status": "healthy",
  "last_updated": "2026-01-13T12:00:00Z",
  "job_count": 307,
  "version": "1.0.0"
}
```

## Cost Analysis

**GitHub Free Tier:**
- Actions: 2,000 minutes/month
- Storage: 500 MB
- Pages: 1 GB soft limit, 100 GB bandwidth/month

**Estimated Usage:**
- Ingestion: ~5 minutes/day = 150 minutes/month
- Storage: <50 MB (300 jobs with snapshots)
- Pages: <10 GB bandwidth/month (light traffic)

**Result**: Completely free for typical usage.

## Support

For issues or questions:

1. Check logs in Actions tab
2. Review troubleshooting section above
3. Consult project documentation
4. File issue on GitHub repository
