# CFB Library Dependency Conflict

**Date:** December 5, 2024  
**Status:** ⚠️ **BLOCKING ISSUE FOR PRODUCTION**

## Problem Summary

The `cfbd` Python library (College Football Data API wrapper) has a **critical dependency conflict** that prevents it from being used in the First6 production environment.

### The Conflict

- **cfbd library requires:** pydantic v1.x (`pydantic<2,>=1.10.5`)
- **First6 application requires:** pydantic v2.x (`pydantic[email]==2.5.0`)

These requirements are **mutually exclusive** and cannot coexist in the same Python environment.

### Impact

When attempting to install cfbd in the Docker container:

```bash
$ pip install cfbd
# ... installation proceeds ...
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
This behaviour is the source of the following dependency conflicts.
nflreadpy 0.1.5 requires pydantic>=2.0.0, but you have pydantic 1.10.24 which is incompatible.
pydantic-settings 2.1.0 requires pydantic>=2.3.0, but you have pydantic 1.10.24 which is incompatible.
```

Installing cfbd **downgrades pydantic to v1**, which breaks:

- FastAPI application (requires pydantic v2)
- nflreadpy (requires pydantic v2)
- pydantic-settings (requires pydantic v2)
- All application schemas and validation

## Current Status

### ✅ Sandbox Environment

The `cfb_sandbox.py` script works correctly in **isolated environments**:

- Separate virtual environment with cfbd installed
- Local development outside Docker
- Dedicated testing environment

### ❌ Production Environment

The cfbd library **CANNOT** be installed in the main Docker container without breaking the application.

## Workarounds

### Option 1: Wait for Library Update (Recommended for Long-term)

**Status:** Waiting on upstream  
**Timeline:** Unknown

Monitor the cfbd library for pydantic v2 support:

- GitHub: https://github.com/CFBD/cfbd-python
- PyPI: https://pypi.org/project/cfbd/

Check for updates periodically:

```bash
pip index versions cfbd
```

### Option 2: Direct REST API Calls (Recommended for Production)

**Status:** Viable alternative  
**Effort:** Medium

Instead of using the Python library, make direct HTTP requests to the College Football Data API:

```python
import httpx

async def get_cfb_plays(year: int, week: int, api_key: str):
    """Fetch CFB plays directly from REST API"""
    url = "https://api.collegefootballdata.com/plays"
    params = {
        "year": year,
        "week": week,
        "seasonType": "regular"
    }
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
```

**Advantages:**

- No dependency conflicts
- Full control over requests
- Can use pydantic v2 for response validation
- Lighter weight (no extra dependencies)

**Disadvantages:**

- More boilerplate code
- Need to handle API details manually
- No built-in type hints from library

### Option 3: Separate Microservice

**Status:** Viable but complex  
**Effort:** High

Run CFB data ingestion in a separate Docker container with isolated dependencies:

```yaml
# docker-compose.yml
services:
  cfb-worker:
    build: ./cfb-worker
    environment:
      - CFB_API_KEY=${CFB_API_KEY}
    depends_on:
      - db
      - redis
```

**Advantages:**

- Can use cfbd library
- Isolated dependencies
- Scalable independently

**Disadvantages:**

- Increased infrastructure complexity
- Additional container to manage
- Inter-service communication overhead

### Option 4: Alternative Data Sources

**Status:** Research required  
**Effort:** High

Investigate alternative college football data providers:

- ESPN API (unofficial)
- NCAA Stats API
- Sports data aggregators (paid services)
- Web scraping (last resort)

## Recommendations

### For Sandbox/Research (Current)

✅ **Continue using cfbd in isolated environments**

- Keep `cfb_sandbox.py` for research and testing
- Document findings and data structures
- Do NOT add cfbd to `requirements.txt`

### For Production Implementation

🎯 **Recommended Approach: Direct REST API Calls (Option 2)**

Reasons:

1. **No dependency conflicts** - Works with pydantic v2
2. **Simpler architecture** - No additional services needed
3. **Full control** - Can optimize for our specific use case
4. **Maintainable** - Less external dependencies to manage

Implementation steps:

1. Create `CFBApiClient` class for REST API calls
2. Use pydantic v2 models for response validation
3. Implement same functionality as cfbd library
4. Add comprehensive error handling
5. Test with sandbox findings as reference

### Priority

⚠️ **LOW PRIORITY** for initial production release

Reasons:

1. NFL is the primary focus for First6
2. Other sports (NBA, MLB, NHL) have working libraries
3. CFB can be added later once dependency issue is resolved
4. Direct API implementation can be done when CFB support is needed

## Documentation Updates

The following files have been updated to document this issue:

1. ✅ `backend/requirements.txt` - cfbd commented out with explanation
2. ✅ `backend/sandbox/cfb_sandbox.py` - Warning in docstring
3. ✅ `backend/sandbox/README.md` - Dependency conflict warning in CFB section
4. ✅ `backend/sandbox/PRODUCTION_RECOMMENDATIONS.md` - Critical warning and alternatives
5. ✅ `backend/sandbox/CFB_DEPENDENCY_ISSUE.md` - This comprehensive document

## Testing

To verify the conflict:

```bash
# In Docker container
docker compose exec api pip install cfbd
# Observe pydantic downgrade and conflicts

# Restore pydantic v2
docker compose exec api pip uninstall -y cfbd pydantic
docker compose exec api pip install "pydantic[email]==2.5.0"
```

## Resolution Checklist

When cfbd updates to support pydantic v2:

- [ ] Verify cfbd supports pydantic v2 (check PyPI/GitHub)
- [ ] Test installation in Docker container
- [ ] Verify no dependency conflicts
- [ ] Add cfbd to requirements.txt
- [ ] Update documentation to remove warnings
- [ ] Test cfb_sandbox.py in Docker
- [ ] Implement production CFB adapter
- [ ] Update this document with resolution date

## References

- cfbd GitHub: https://github.com/CFBD/cfbd-python
- cfbd PyPI: https://pypi.org/project/cfbd/
- College Football Data API: https://collegefootballdata.com/
- Pydantic v2 Migration Guide: https://docs.pydantic.dev/latest/migration/

---

**Last Updated:** December 5, 2024  
**Next Review:** Check for cfbd updates monthly
