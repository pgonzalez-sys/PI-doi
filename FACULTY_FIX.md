# Faculty Author Fix

## Issue Identified

The system was incorrectly including the **WordPress uploader** as an author instead of the actual **faculty members**.

### Before
- Used WordPress `author` field → Person who uploaded/published the content (admin user)
- Example: Author ID 160527 (random admin account)

### After
- Uses only `coauthors` field → Actual faculty/instructors
- Example: "Mark Horowitz", "Wegdan Rashad", "Flavio Guzmán"

## Changes Made

### 1. Updated `_fetch_authors()` Method
**File**: `src/fetchers/publications.py`

```python
# OLD: Fetched both WordPress author AND coauthors
if author_id:
    author = self._fetch_user(author_id)  # ❌ Uploader
    authors.append(author)

for coauthor_id in coauthor_ids:
    coauthor = self._fetch_coauthor(coauthor_id)  # ✓ Faculty
    authors.append(coauthor)

# NEW: Only fetch coauthors (faculty)
for idx, coauthor_id in enumerate(coauthor_ids):
    coauthor = self._fetch_coauthor(coauthor_id)  # ✓ Faculty only
    coauthor.sequence = 'first' if idx == 0 else 'additional'
    authors.append(coauthor)
```

### 2. Improved Faculty Name Parsing
**File**: `src/fetchers/publications.py`

The Co-Authors Plus plugin stores faculty in a complex format:
```
Description: "Mark Horowitz Mark Horowitz mark-horowitz 1625256 email@..."
```

Updated `_fetch_coauthor()` to:
1. Parse the description field
2. Extract clean display name ("Mark Horowitz")
3. Remove duplicates and extra data

## Test Results

### Before Fix
```xml
<contributors>
  <person_name sequence="first" contributor_role="author">
    <given_name>Admin</given_name>
    <surname>User</surname>
  </person_name>
</contributors>
```

### After Fix
```xml
<contributors>
  <person_name sequence="first" contributor_role="author">
    <given_name>Mark</given_name>
    <surname>Horowitz</surname>
  </person_name>
</contributors>
```

## Verification

Tested with 3 publications:
- ✅ "New" Antidepressants → Faculty: Wegdan Rashad
- ✅ 2014 In Review → Faculty: Flavio Guzmán
- ✅ Antidepressant Withdrawal → Faculty: Mark Horowitz

All showing correct faculty names, not WordPress uploaders.

## API Endpoints Used

### Coauthors Endpoint
```bash
GET /wp/v2/coauthors?post={publication_id}
```

Returns list of faculty members for a publication.

### Coauthor Details
```bash
GET /wp/v2/coauthors/{coauthor_id}
```

Returns faculty profile with name in description field.

## Multiple Faculty Support

The system correctly handles publications with multiple faculty:
- First coauthor → `sequence="first"`
- Additional coauthors → `sequence="additional"`

Example (if publication has 2 faculty):
```xml
<contributors>
  <person_name sequence="first" contributor_role="author">
    <given_name>Mark</given_name>
    <surname>Horowitz</surname>
  </person_name>
  <person_name sequence="additional" contributor_role="author">
    <given_name>Tomás</given_name>
    <surname>Abudarham</surname>
  </person_name>
</contributors>
```

## Ready for Production

✅ Faculty names correctly extracted
✅ WordPress uploaders excluded
✅ Multiple faculty support
✅ Clean name parsing from Co-Authors Plus

The system is ready to generate production DOIs with correct faculty attribution.
