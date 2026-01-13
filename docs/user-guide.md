# User Guide

## Overview

JobSeekers Shovel tracks job postings from configured companies, identifies reposts, and provides a web interface for browsing and tracking applications.

## Views

### Jobs View

Browse all tracked job postings with filtering and sorting.

**Features**:
- Search by title, company, or location (top search bar)
- Filter by status: Active, Missing, Closed
- Filter by classification: New, Existing, Repost, Reopened
- Sort by: Newest First, Oldest First, Company, Title

**Job Cards Display**:
- Job title and company name
- Location and status badge
- First seen and last seen dates
- Classification with reasoning
- Application tracking indicator (if tracked)

**Actions**:
- Click card to view full details
- Click "Track Application" to log application

### Applications View

Manage tracked job applications.

**Features**:
- View all applications with status
- Filter by stage: Applied, Interviewing, Offer, Rejected, Accepted, Withdrawn
- Track follow-up dates

**Application Fields**:
- Applied date (required)
- Current stage
- Notes
- Contact person (optional)
- Next follow-up date (optional)

**Actions**:
- Add new application
- Update application details (edit in localStorage)
- View associated job details

### Help View

In-app documentation with:
- Classification definitions
- Status meanings
- Usage tips

## Job Classifications

**New**: First time job posted by company

**Existing**: Previously seen job, still active (reobserved within repost window)

**Repost**: Likely duplicate of previous posting (90%+ similarity)
- System uses component-wise matching (company, title, location)
- Handles word reordering: "ML Engineer" = "Engineer - ML"
- Distinguishes seniority: "Engineer" ≠ "Senior Engineer"

**Reopened**: Previously closed job reposted (seen again after closure)

## Job Statuses

**Active**: Currently posted on company careers page

**Missing**: Not seen in recent ingestion (may be closed)
- Transitions to Missing if not seen within repost window (default: 30 days)
- Transitions to Closed after missing timeout (default: 14 days)

**Closed**: Confirmed no longer posted
- Automatically marked after missing timeout
- May transition to Reopened if reappears

## Using the Interface

### Browsing Jobs

1. Default view shows all active jobs
2. Use search bar for quick filtering
3. Apply status/classification filters as needed
4. Sort by preference (newest first recommended)

### Viewing Job Details

1. Click any job card
2. Modal shows:
   - Full job metadata
   - Temporal tracking (first/last seen, observation count)
   - Department and description (if available)
   - Classification reasoning
   - Recent observations timeline
3. Click "View Original Posting" to visit company careers page

### Tracking Applications

1. From job card: Click "Track Application"
2. From job detail modal: Click "Track Application"
3. Fill in form:
   - Applied date (use calendar picker)
   - Current stage (dropdown)
   - Optional notes
   - Optional contact person
   - Optional follow-up date
4. Submit to save

Applications stored in browser localStorage (persists across sessions).

### Exporting Data

**Jobs Export**:
- CSV: Filtered jobs with key fields (Company, Title, Location, Status, etc.)
- JSON: Full job objects including all metadata

**Applications Export**:
- JSON: All tracked applications with timestamps and notes

Export buttons in top-right toolbar.

## Filtering Tips

**Find specific company**: Use search bar, type company name

**See only new jobs**: Enable "New" classification filter

**Review missing jobs**: Enable "Missing" status filter (may need attention)

**Track applications**: Enable "Applied" stage filter in Applications view

## Understanding Classifications

### Repost Detection

System achieves 100% accuracy in controlled tests. Uses:
- Title matching with word order invariance
- Location normalization (CA = California)
- Abbreviation handling (Sr. = Senior)
- 90% similarity threshold

**Borderline Cases**:
- Location qualifiers (Hybrid vs In-office): System may flag as repost when work arrangement differs. Review manually if critical.

### Temporal Tracking

**First Seen**: Job first observed in ingestion

**Last Seen**: Most recent observation

**Observations**: Number of times job seen (indicates reposting frequency)

**Window**: Default 30 days for repost detection

## Data Refresh

**Automated** (if deployed with GitHub Actions):
- Daily ingestion at 2 AM UTC
- Automatic frontend redeployment
- Snapshots created for rollback

**Manual**:
```bash
python -m src.ingestion
```

Reload page to see new jobs.

## Browser Requirements

- Modern browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- localStorage enabled (for application tracking)

## Troubleshooting

**No jobs displayed**: Check `data/jobs/jobs-v1.json` exists and contains data

**Filters not working**: Clear filters, refresh page

**Application tracking not saving**: Check browser localStorage enabled

**Search slow with many jobs**: Filter by status first to reduce dataset

## Best Practices

1. Review new jobs daily
2. Mark applications immediately after applying
3. Update application stages regularly
4. Set follow-up dates for active applications
5. Export data periodically for backup
6. Monitor "Missing" status jobs (may be closing soon)
7. Check classification reasoning for borderline cases
