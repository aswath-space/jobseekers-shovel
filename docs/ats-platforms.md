# ATS Platform Research

This document outlines common Applicant Tracking System (ATS) platforms and their technical characteristics for job ingestion.

---

## Overview

Modern companies use various ATS platforms to manage hiring. Each platform has different URL structures, API availability, and data formats. For MVP, we focus on the most common platforms with accessible job boards.

---

## Selected Platforms for MVP

### 1. Greenhouse

**Prevalence**: Very common among tech startups and mid-size companies

**Job Board URL Pattern**:
```
https://boards.greenhouse.io/{company-slug}
https://boards-api.greenhouse.io/v1/boards/{company-slug}/jobs
```

**Data Format**:
- HTML boards + JSON API available
- JSON API endpoint: `https://boards-api.greenhouse.io/v1/boards/{company}/jobs`
- Returns structured JSON with all job postings

**Key Fields**:
- `id` - Unique job ID (stable)
- `title` - Job title
- `location` - Location object with `name` field
- `absolute_url` - Direct link to job posting
- `updated_at` - Last update timestamp
- `departments` - Array of department objects

**Stability**:
- Job IDs are stable and persistent
- API is reliable and well-documented
- Rate limits: Generally permissive for reasonable use

**Example Response Structure**:
```json
{
  "jobs": [
    {
      "id": 4084045006,
      "title": "Senior Software Engineer",
      "location": {
        "name": "San Francisco, CA"
      },
      "absolute_url": "https://boards.greenhouse.io/company/jobs/4084045006",
      "updated_at": "2026-01-10T12:34:56Z",
      "departments": [
        {
          "id": 12345,
          "name": "Engineering"
        }
      ]
    }
  ]
}
```

**Implementation Notes**:
- Use JSON API endpoint (easier to parse than HTML)
- No authentication required for public job boards
- Simple GET request returns all jobs
- Check `updated_at` for change detection

---

### 2. Lever

**Prevalence**: Common among tech companies, particularly startups

**Job Board URL Pattern**:
```
https://jobs.lever.co/{company-slug}
https://api.lever.co/v0/postings/{company-slug}?mode=json
```

**Data Format**:
- HTML boards + JSON API available
- JSON endpoint: `https://api.lever.co/v0/postings/{company}?mode=json`
- Returns array of job postings

**Key Fields**:
- `id` - Unique job ID (UUID format, stable)
- `text` - Job title
- `categories.location` - Location string
- `hostedUrl` - Direct link to job posting
- `createdAt` - Creation timestamp
- `categories.team` - Department/team name

**Stability**:
- Job IDs are UUIDs and very stable
- API is reliable
- Rate limits: Permissive for reasonable use

**Example Response Structure**:
```json
[
  {
    "id": "12345678-1234-1234-1234-123456789abc",
    "text": "Senior Software Engineer",
    "categories": {
      "location": "San Francisco",
      "team": "Engineering"
    },
    "hostedUrl": "https://jobs.lever.co/company/12345678-1234-1234-1234-123456789abc",
    "createdAt": 1704897600000
  }
]
```

**Implementation Notes**:
- Add `?mode=json` to get JSON response
- No authentication required
- Timestamps in milliseconds since epoch
- Simple array response (not wrapped in object)

---

### 3. Workday

**Prevalence**: Very common in large enterprises and Fortune 500 companies

**Job Board URL Pattern**:
```
https://{company}.wd1.myworkdayjobs.com/en-US/{site-name}
https://{company}.wd1.myworkdayjobs.com/wday/cxs/{company}/{site}/jobs
```

**Data Format**:
- Dynamic JavaScript-rendered pages
- GraphQL/REST API endpoint available (more complex)
- Requires POST request with specific payload

**Key Fields**:
- `jobReqId` - Internal job requisition ID
- `title` - Job title
- `locationsText` - Location string
- `externalPath` - Relative URL path
- `postedOn` - Posted date

**Stability**:
- Job IDs can be unstable across postings
- More complex to parse than Greenhouse/Lever
- May regenerate URLs or temporarily hide postings

**Example API Endpoint**:
```
POST https://company.wd1.myworkdayjobs.com/wday/cxs/company/site/jobs
Content-Type: application/json

{
  "appliedFacets": {},
  "limit": 20,
  "offset": 0,
  "searchText": ""
}
```

**Example Response Structure**:
```json
{
  "total": 100,
  "jobPostings": [
    {
      "title": "Senior Software Engineer",
      "locationsText": "San Francisco, CA",
      "postedOn": "2026-01-10T00:00:00.000Z",
      "externalPath": "/job/San-Francisco/Senior-Software-Engineer/JR12345",
      "bulletFields": ["Engineering"],
      "jobReqId": "JR12345"
    }
  ]
}
```

**Implementation Notes**:
- Requires POST request with JSON payload
- Pagination via `limit` and `offset`
- More complex than Greenhouse/Lever
- May require handling dynamic site names
- Response structure can vary by company configuration

---

## Additional Platforms (Future Consideration)

### 4. Ashby

**Prevalence**: Growing among tech startups

**URL Pattern**: `https://jobs.ashbyhq.com/{company}`

**Notes**:
- Clean JSON API available
- Similar simplicity to Greenhouse
- Growing adoption in 2024-2026

### 5. SmartRecruiters

**Prevalence**: Common in enterprise

**URL Pattern**: `https://jobs.smartrecruiters.com/{company}`

**Notes**:
- HTML-heavy interface
- API available but may require authentication
- Less common in target industries (R&D, tech)

---

## MVP Implementation Priority

For MVP, implement in this order:

1. **Greenhouse** (Priority: HIGH)
   - Simplest JSON API
   - Very common in target companies
   - Stable job IDs
   - Good for testing and validation

2. **Lever** (Priority: HIGH)
   - Simple JSON API
   - Common in tech startups
   - Stable UUIDs

3. **Workday** (Priority: MEDIUM)
   - Most complex implementation
   - Very common in large enterprises
   - Tests robustness of classification logic
   - May have unstable job IDs (good test case for signature matching)

---

## Common Challenges

### ID Stability
- **Greenhouse/Lever**: Very stable, reliable for exact matching
- **Workday**: May regenerate or change IDs, requires signature-based matching

### Rate Limiting
- All platforms: Use respectful delays (2+ seconds between requests)
- Monitor for 429 (Too Many Requests) responses
- Implement exponential backoff

### Data Format Variations
- Different timestamp formats (ISO 8601, Unix epoch, milliseconds)
- Location data: strings vs. objects vs. arrays
- Nested vs. flat structures

### Temporary Disappearances
- Jobs may be temporarily removed for editing
- Don't immediately mark as closed - use timeout window

---

## Implementation Strategy

### Adapter Pattern
Each ATS platform gets its own adapter implementing common interface:

```python
class ATSAdapter(ABC):
    @abstractmethod
    def fetch_jobs(self, source_url: str) -> List[RawJob]:
        """Fetch jobs from ATS platform."""
        pass

    @abstractmethod
    def extract_job_data(self, raw_data: Any) -> Job:
        """Extract standardized job data from platform-specific format."""
        pass
```

### Standardized Job Format
All adapters return jobs in standard format:
- Company ID/name
- Job title
- Location (normalized string)
- URL
- Source identifier (platform-specific ID)
- Any additional metadata

---

## Testing Strategy

1. **Manual Testing**
   - Test with real company URLs
   - Verify data extraction
   - Monitor for rate limiting

2. **Mock Testing**
   - Unit tests with mock API responses
   - Test error handling
   - Test data normalization

3. **Integration Testing**
   - Full ingestion run with 3-5 real companies
   - Verify all adapters work together
   - Check classification accuracy

---

## References

- Greenhouse API: https://developers.greenhouse.io/job-board.html
- Lever API: https://github.com/lever/postings-api
- Workday: Varies by implementation (no public documentation)
