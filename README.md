# Crossref XML Generator for WordPress Publications

Generate Crossref-compliant XML files from WordPress publications at Psychopharmacology Institute.

## Overview

This tool fetches publications and their sections from the WordPress REST API, transforms them to Crossref metadata format, and generates valid XML files for DOI registration as **Reports** with hierarchical parent-child relationships.

## Features

- Fetch publications and sections from WordPress/LearnDash
- Generate DOIs for both publications and sections:
  - **Publications**: `10.64239/pi-{publication_code}`
  - **Sections**: `10.64239/pi-{publication_code}-s{number}`
- Create hierarchical relationships using Crossref relations schema
- Transform to Crossref 5.4.0 Report format
- Generate CSV report of all DOIs for display on website
- XSD schema validation
- Batch or individual XML output
- Graceful error handling

## Requirements

- Python 3.9+
- WordPress Application Password
- Internet connection

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```
WP_USERNAME=your_username@example.com
WP_APP_PASSWORD=your application password
WP_BASE_URL=https://psychopharmacologyinstitute.com
```

## Configuration

Edit `config/crossref_config.yml` to customize:
- Depositor information
- DOI prefix and patterns
- Publisher information
- Output settings

## Usage

### Basic Usage (Batch Mode)

Generate a single XML file with all publications:

```bash
python -m src.cli
```

### Test with Single Publication

```bash
python -m src.cli --limit 1 --mode individual --output output/test/
```

### Generate Both Batch and Individual Files

```bash
python -m src.cli --mode both
```

### Skip Validation (Faster)

```bash
python -m src.cli --no-validate
```

### Process Limited Number

```bash
python -m src.cli --limit 10
```

## Command-Line Options

- `--mode {batch|individual|both}` - Output mode (default: batch)
- `--output PATH` - Output directory (default: output/batches)
- `--validate` - Validate XML against schema (default: true)
- `--no-validate` - Skip validation
- `--limit N` - Limit number of publications

## Output

### Batch Mode
Single XML file with all publications and sections: `output/batches/crossref_batch_YYYYMMDD_HHMMSS.xml`

### Individual Mode
One XML file per DOI: `output/individual/10_64239_pi-{code}.xml`

### DOI Report
CSV file with all generated DOIs: `output/*/doi_report.csv`

The DOI report contains:
- Type (Publication or Section)
- DOI
- Title
- Report Number
- URL
- Parent DOI (for sections)
- WordPress ID

Use this report to add DOIs to your WordPress pages.

## Hierarchical Structure

### DOI Patterns

**Publications**: `10.64239/pi-{publication_code}`
- Example: `10.64239/pi-98`

**Sections**: `10.64239/pi-{publication_code}-s{number}`
- Examples: `10.64239/pi-98-s01`, `10.64239/pi-98-s02`, etc.

### Parent-Child Relationships

Sections are linked to their parent publication using Crossref relations:

**Parent Publication:**
```xml
<report-paper>
  <report-paper_metadata language="en">
    <titles><title>Antidepressant Withdrawal Effects...</title></titles>
    <doi_data>
      <doi>10.64239/pi-98</doi>
      <resource>https://...publication/...</resource>
    </doi_data>
  </report-paper_metadata>
</report-paper>
```

**Child Section:**
```xml
<report-paper>
  <report-paper_metadata language="en">
    <titles><title>Section 1: Current Trends...</title></titles>
    <!-- Relations link to parent -->
    <rel:program xmlns:rel="http://www.crossref.org/relations.xsd">
      <rel:related_item>
        <rel:intra_work_relation relationship-type="isPartOf" identifier-type="doi">
          10.64239/pi-98
        </rel:intra_work_relation>
      </rel:related_item>
    </rel:program>
    <doi_data>
      <doi>10.64239/pi-98-s01</doi>
      <resource>https://...section/...</resource>
    </doi_data>
  </report-paper_metadata>
</report-paper>
```

## DOI Display Requirements

Crossref requires DOIs to be prominently displayed on content pages:

**Left Sidebar** (Publication DOI - persistent across all sections):
```
📄 DOI: 10.64239/pi-98
   [Cite this course]
```

**Main Content Area** (Section DOI - specific to current section):
```
Published on September 1, 2025
📄 DOI: 10.64239/pi-98-s01
```

Both DOIs should be clickable links to `https://doi.org/{doi}`

## Troubleshooting

### Authentication Errors

- Verify WordPress Application Password in `.env`
- Ensure password has no extra spaces
- Check WordPress user has proper permissions

### Validation Errors

- Review schema validation output
- Check XML structure matches Crossref requirements
- Verify all required fields are present

### Missing Authors

Some author IDs may not resolve (404 errors). This is handled gracefully:
- Missing authors are logged as warnings
- Publications continue to process
- Check logs for details

## Project Structure

```
doi/
├── src/
│   ├── fetchers/          # WordPress API clients
│   ├── models/            # Data models
│   ├── transformers/      # Data transformation
│   ├── generators/        # XML generation
│   ├── validators/        # Schema validation
│   └── cli.py             # Command-line interface
├── config/                # Configuration files
├── output/                # Generated XML files
├── docs/                  # Documentation & schemas
└── requirements.txt       # Python dependencies
```

## Next Steps

1. Test with sample publications
2. Review generated XML
3. Submit to Crossref test environment
4. Register DOIs in production

## Support

For issues or questions, check:
- Generated logs for error details
- Crossref documentation: https://www.crossref.org/documentation/
- Schema files in `docs/cross-ref/schemas/`
