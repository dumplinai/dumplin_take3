# Request
The limit on the search restaurant tool - is it 5 or 10? Explain how it works and what it is.

## Request Description
This research investigates the restaurant search tool's `limit` parameter, which controls how many restaurants are returned in search results. The user heard it might be either 5 or 10, and wants clarity on how this parameter functions, what values it accepts, and whether it's enforced or configurable.

## Relevant Files
1. `backend\app\tools\restaurant_search.py` - Main tool implementation with limit logic
2. `backend\app\agents\food_agent.py` - Agent that creates and uses the search tool
3. `backend\app\utils\vector_search.py` - Underlying vector search service
4. `backend\docs\CHATBOT_FLOW.md` - Documentation on chatbot flow
5. `specs\research-dumplin-restaurant-search.md` - Existing restaurant search research

## Inputs

### Tool Parameters
The `search_restaurants` tool accepts these parameters (defined at `backend\app\tools\restaurant_search.py:76`):

```python
def search_restaurants(
    search_text: str,
    limit: int = 5,  # DEFAULT VALUE
    radius_km: float = 35.0,
    nearby_only: bool = True,
    specific_name_search: bool = False,
    price_tier_min: int = None,
    price_tier_max: int = None,
    sort_by_price: bool = False,
    should_exclude: bool = False
) -> str:
```

**Key Finding: The `limit` parameter accepts any integer, with a DEFAULT of 5**

### Limit Enforcement
However, there is **HARDCODED ENFORCEMENT** at line 130-131:

```python
# Limit of 5 restaurants only
limit = 5
```

**This means:**
- The tool signature accepts `limit` as a parameter
- The docstring says "Maximum number of restaurants to return (fixed at 5)"
- BUT the code **OVERRIDES** any passed value and **FORCES** it to be 5
- The LLM agent calling this tool cannot change this value - it's always 5

### Where the Limit is Used
The hardcoded `limit = 5` is passed to:
1. `vector_search.search_by_text()` at lines 148-185
2. MongoDB vector search pipeline at `backend\app\utils\vector_search.py:293-294`:
   ```python
   "numCandidates": limit * 20,  # 100 candidates examined
   "limit": limit * 10  # 50 results from vector search
   ```
3. Final sorting and limiting happens at `backend\app\utils\vector_search.py:357` (limit of 5)

### Agent Configuration
The FoodAgent system prompt at `backend\app\agents\food_agent.py:246` instructs:
```
- Filter: ONLY open restaurants UNLESS user says "even if closed"
- Return EXACTLY 5 by similarity_score as cards
```

And at line 286:
```
- search_restaurants: 🚨 ALWAYS returns CARDS! Query with city name, limit=5 (FIXED)
```

## Outputs

### What Gets Returned
1. **Vector Search Stage** (`backend\app\utils\vector_search.py:232`):
   - Examines 100 candidates (`numCandidates = limit * 20`)
   - Returns up to 50 results from vector search (`limit * 10`)
   - Filters by radius, city, price tier, exclusions
   - Applies final limit of 5

2. **Tool Processing** (`backend\app\tools\restaurant_search.py:218-272`):
   - Processes all results in parallel
   - Calculates `is_open` status for each
   - Sorts by `is_open` (open first), then `similarity_score` (highest first)
   - Returns exactly 5 restaurants

3. **JSON Output Format** (line 275-283):
   ```json
   [
     {
       "place_id": "...",
       "title": "...",
       "embedding_text": "...",
       "similarity_score": 0.85,
       "distance_km": 2.5,
       "distance_string": "10-15 min",
       "is_open": true,
       "price_tier": 3
     }
   ]
   ```

### Output Destination
- **Backend → Frontend**: JSON array of 5 restaurant objects
- **Agent Response**: Formatted as cards in structured response
- **State Storage**: Metadata stored at `backend\app\agents\food_agent.py:208-216`
- **User Display**: Frontend renders 5 restaurant cards

## The Limit: 5 or 10?

### Answer: **ALWAYS 5** (Hardcoded)

Here's why there might be confusion:

1. **The Default Says 5**: `limit: int = 5` (line 76)
2. **The Code Forces 5**: `limit = 5` (line 131)
3. **But Vector Search Uses 10x**: `limit * 10` = 50 candidates (line 294)
4. **Someone might have seen**: `limit: int = 10` in `vector_search.py:232` which is the default for the underlying search function

### Vector Search Default
In `backend\app\utils\vector_search.py:232`:
```python
def search_by_text(self, query_text: str, limit: int = 10, ...):
```

This function has a default of 10, BUT it's always called with `limit=5` from the restaurant_search tool.

## Key Design Decisions

### Why Hardcoded to 5?
1. **UX Constraint**: Prevents overwhelming users with too many options
2. **Performance**: Limits processing time for is_open calculations
3. **LLM Context**: Keeps response size manageable for agent to process
4. **Agent Prompt Alignment**: System prompt explicitly says "Return EXACTLY 5"

### How "More Options" Works
When users ask for "more" restaurants:
1. Agent sets `should_exclude=True` (line 88)
2. Uses `exclude_place_ids` from state (line 95)
3. Searches with same limit (5) but excludes previous results
4. Returns next 5 restaurants

This allows pagination without increasing the limit.

### Radius Expansion for "More"
System prompt at line 290-291:
```
- "more options"/"show me more" → limit=5 (FIXED), radius_km=50-80, should_exclude=True
```

The agent increases the search radius (not the limit) to find more options.

## Notes

### Discrepancy Between Signature and Implementation
The function signature suggests `limit` is configurable, but the implementation forces it to 5. This could be:
- **Legacy code**: Maybe it was configurable before
- **Future flexibility**: Prepared for A/B testing different limits
- **Documentation mismatch**: Signature doesn't match actual behavior

### MongoDB Vector Search Multipliers
- `numCandidates = limit * 20 = 100`: Initial candidates examined by vector search
- `limit (vector) = limit * 10 = 50`: Results returned from vector stage
- `limit (final) = 5`: Final results after filtering and sorting

This funnel approach ensures high-quality results by:
1. Examining 100 candidates for relevance
2. Filtering to 50 by location/price/etc
3. Calculating open status and sorting
4. Returning top 5

### Performance Implications
With parallel processing (line 229):
```python
with ThreadPoolExecutor(max_workers=max(1, min(10, len(results))))
```

Processing time scales with result count. Keeping it at 5 ensures:
- Fast response times
- Lower API costs (timezone calculations)
- Consistent UX

### Testing Different Limits
To change the limit, you would need to:
1. Modify line 131: `limit = 5` → `limit = 10`
2. Update system prompt references to "limit=5 (FIXED)"
3. Test impact on response time and UX
4. Consider mobile screen space for cards
