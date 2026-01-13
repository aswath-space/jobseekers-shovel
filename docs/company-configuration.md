# Company Configuration Guide

## Overview

Companies are configured in `config/companies.yaml`. Each entry defines a company to track and how to fetch its job postings.

## Configuration Format

```yaml
companies:
  - id: unique-id
    name: Display Name
    adapter_type: greenhouse|lever
    adapter_config:
      board_token: token
```

## Required Fields

### `id`
- Unique identifier for the company
- Lowercase, no spaces (use hyphens)
- Used internally for data organization
- Example: `anthropic`, `openai`, `acme-corp`

### `name`
- Human-readable company name
- Used in frontend display
- Example: `Anthropic`, `OpenAI`, `ACME Corporation`

### `adapter_type`
- Job board platform used by company
- Supported values: `greenhouse`, `lever`

### `adapter_config.board_token`
- Company-specific identifier on job board
- Find by visiting company's careers page
- See "Finding Board Tokens" below

## Finding Board Tokens

### Greenhouse

1. Visit company careers page
2. Look for URL pattern: `https://boards.greenhouse.io/[TOKEN]`
3. Token is the final path segment

Example: `https://boards.greenhouse.io/anthropic` → token: `anthropic`

### Lever

1. Visit company careers page
2. Look for URL pattern: `https://jobs.lever.co/[TOKEN]`
3. Token is the final path segment

Example: `https://jobs.lever.co/openai` → token: `openai`

## Example Configurations

### Single Company

```yaml
companies:
  - id: anthropic
    name: Anthropic
    adapter_type: greenhouse
    adapter_config:
      board_token: anthropic
```

### Multiple Companies

```yaml
companies:
  - id: anthropic
    name: Anthropic
    adapter_type: greenhouse
    adapter_config:
      board_token: anthropic

  - id: openai
    name: OpenAI
    adapter_type: lever
    adapter_config:
      board_token: openai

  - id: google-deepmind
    name: Google DeepMind
    adapter_type: greenhouse
    adapter_config:
      board_token: deepmind
```

## Adding New Companies

1. Open `config/companies.yaml`
2. Add new entry following format above
3. Save file
4. Run ingestion: `python -m src.ingestion`
5. Jobs appear in `data/jobs/jobs-v1.json`

## Validation

After adding companies, verify configuration:

```bash
# Run ingestion
python -m src.ingestion

# Check output
cat data/jobs/jobs-v1.json | grep company_name
```

Expected: New company names appear in output

## Troubleshooting

**No jobs ingested**:
- Verify board token by visiting careers page URL
- Check company uses supported platform (Greenhouse/Lever)
- Confirm `adapter_type` matches platform

**Rate limiting errors**:
- Increase `rate_limit_delay_seconds` in `config/config.yaml`
- Default: 1.0 seconds between requests

**Invalid YAML syntax**:
- Use YAML validator (yamllint)
- Check indentation (2 spaces per level)
- Verify no tabs used

## Best Practices

- Use descriptive IDs (company name in lowercase)
- Keep `name` field accurate for frontend display
- Test new entries individually before adding multiple
- Document board token sources for future reference
