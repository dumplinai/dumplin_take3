# Feature: Dumplin Scoring System

## Feature Description
Implement a comprehensive scoring system that ranks restaurants based on three key factors: relevancy (similarity score), quality (combined score from ratings/reviews), and distance from search location. Currently, restaurants are sorted only by similarity score, which doesn't account for restaurant quality or distance from the search center. The new `dumplin_score` will provide a holistic ranking that balances what users are looking for with quality and proximity.

This feature will also fix a critical issue where distance is currently calculated from the user's actual GPS location instead of the search location (which may be the city center when the user is outside city bounds).

## Scope
This feature affects:
- **Backend (FastAPI)**: New scoring utility module, modifications to vector search and restaurant search tool
- **ETL Pipeline**: May require updates to ensure quality score components are available in the database
- **No Frontend Changes**: The frontend already displays distance, similarity scores, and restaurant data - it just needs proper scoring from backend

## User Story
As a **Dumplin user**
I want to **see restaurants ranked by a combination of relevance, quality, and distance**
So that **I get the best overall recommendations that match my request, are highly-rated, and are conveniently located**

## Problem Statement
The current restaurant ranking system has fundamental limitations:

1. **Single-Factor Sorting**: Restaurants are sorted only by `similarity_score` (semantic relevance to the user's query), ignoring restaurant quality (ratings, review counts) and proximity to the search location.

2. **Distance Calculation Bug**: Distance is calculated from `user_latitude/user_longitude` (actual GPS position) instead of `search_latitude/search_longitude` (the intended search center). This is incorrect when users are outside city bounds and the search center defaults to the city center.

3. **No Quality Consideration**: High-similarity restaurants with poor ratings or few reviews are ranked the same as excellent restaurants with the same similarity score.

4. **Proximity Not Weighted**: Two restaurants with similar relevancy scores but vastly different distances (e.g., 2km vs 20km) are ranked the same if they have similar similarity scores.

## Solution Statement
Create a new `dumplin_score` that combines three weighted factors:

**Formula:**
```
dumplin_score = (w_relevancy * relevancy_score) + (w_quality * quality_score) + (w_distance * distance_score)
```

Where:
- **relevancy_score**: Normalized similarity score from vector search (0-1)
- **quality_score**: Normalized combined score from ratings and review counts (0-1)
- **distance_score**: Inverse distance score from search location (0-1, where 1 is closest)
- **Weights**: `w_relevancy=0.5`, `w_quality=0.3`, `w_distance=0.2` (configurable)

**Key Changes:**
1. Create new `scoring.py` utility with scoring logic
2. Calculate quality_score from `totalScore` and `reviewsCount` fields
3. Fix distance calculation to use `search_latitude/search_longitude` instead of user coordinates
4. Sort restaurants by `dumplin_score` instead of just `similarity_score`
5. Maintain backward compatibility by still sorting by `is_open` first

## Relevant Files
Use these files to implement the feature:

### Existing Files to Modify

**1. `backend/app/utils/vector_search.py`**
- Contains the `VectorSearch` class with distance calculation methods
- Lines 19-31: `calculate_distance_km()` method - needs fix to use search coordinates
- Lines 439-460: Distance calculation in `search_by_text()` - currently uses `user_lat/user_lng`, should use search coordinates
- Lines 203-220: Distance calculation in `get_by_place_ids()` - same issue
- **Why**: This is where the distance calculation bug exists

**2. `backend/app/tools/restaurant_search.py`**
- Lines 13-71: `process_single_result()` - processes each restaurant result
- Line 66: Returns `combined_score` field (already available from database)
- Lines 274-275: Sorts by `is_open` then `similarity_score` - needs to sort by `dumplin_score` instead
- Lines 176-190: Tool creation in food_agent - receives search coordinates
- **Why**: This is where we'll integrate the new scoring system and modify sorting logic

**3. `backend/app/agents/food_agent.py`**
- Lines 176-190: Creates search_restaurants tool with search/user coordinates
- Lines 550: Adds `similarity_score` to restaurant_info - will add `dumplin_score` too
- Lines 560-561: Sorts restaurants by `is_open` and `similarity_score` - needs update
- **Why**: Agent assembles final restaurant data and applies sorting

**4. `backend/app/models/places.py`**
- Restaurant data model definitions
- **Why**: May need to add `dumplin_score` field to the Place model for consistency

**5. `backend/app/test/export_utils.py`**
- Line 30: Exports `combined_score` to Excel for testing
- **Why**: Will add `dumplin_score` to test exports for debugging

**6. `specs/WHERE-TO-SEE-MONGODB-FIELDS.md`**
- Documents MongoDB field structure
- **Why**: Will update to document the new dumplin_score field

### New Files

#### h3: New Files to Create

**1. `backend/app/utils/scoring.py`**
- Core scoring logic for Dumplin score calculation
- Functions: `normalize_score()`, `calculate_quality_score()`, `calculate_distance_score()`, `calculate_dumplin_score()`
- Configuration: Scoring weights and parameters

**2. `backend/app/test/test_scoring.py`**
- Unit tests for scoring logic
- Test cases: edge cases, weight variations, normalization

**3. `specs/DUMPLIN-SCORING-SYSTEM.md`**
- Comprehensive documentation of the scoring system
- Formula explanation, weight justification, examples

## Implementation Plan

### Phase 1: Foundation
Create the scoring utility module and establish the mathematical foundation for the Dumplin score. This includes:
- Defining the scoring formula and weights
- Implementing normalization functions for each score component
- Creating comprehensive unit tests for scoring logic
- Documenting the scoring system design

### Phase 2: Core Implementation
Integrate the scoring system into the existing search pipeline:
- Fix the distance calculation bug to use search coordinates
- Calculate quality scores from database fields
- Compute dumplin_score for each restaurant
- Update sorting logic to use dumplin_score

### Phase 3: Integration
Ensure the scoring system works end-to-end:
- Update restaurant data models to include dumplin_score
- Pass dumplin_score through to frontend
- Add scoring metrics to test exports
- Validate with real user queries

## Step by Step Tasks

### Step 1: Create Scoring Utility Module
- Create `backend/app/utils/scoring.py` with the following functions:
  - `normalize_score(value, min_val, max_val)`: Normalize any value to 0-1 range
  - `calculate_quality_score(total_score, review_count, max_score=5.0, review_weight=0.7, rating_weight=0.3)`: Calculate quality score from ratings and reviews
  - `calculate_distance_score(distance_km, max_distance_km=35.0)`: Convert distance to inverse score (closer = higher)
  - `calculate_dumplin_score(similarity_score, quality_score, distance_score, w_relevancy=0.5, w_quality=0.3, w_distance=0.2)`: Calculate final weighted score
- Include comprehensive docstrings with formula explanations
- Add configuration constants for default weights and parameters

### Step 2: Create Unit Tests for Scoring
- Create `backend/app/test/test_scoring.py` with test cases:
  - Test `normalize_score()` with various ranges and edge cases (0, negative, beyond max)
  - Test `calculate_quality_score()` with different rating/review combinations
  - Test `calculate_distance_score()` with various distances (0km, 1km, max distance, beyond max)
  - Test `calculate_dumplin_score()` with different weight configurations
  - Test edge cases: missing scores, zero values, extreme values
- Run tests with `pytest backend/app/test/test_scoring.py`

### Step 3: Fix Distance Calculation in VectorSearch
- Modify `backend/app/utils/vector_search.py`:
  - Update `search_by_text()` method (lines 439-460):
    - Change distance calculation to use `lat/lng` parameters (search coordinates) instead of `user_lat/user_lng`
    - Keep `user_lat/user_lng` parameters for backward compatibility but use `lat/lng` for distance calculation
    - Add logging to track which coordinates are used for distance calculation
  - Update `get_by_place_ids()` method (lines 203-220):
    - Apply same fix - use `radius_lat/radius_lng` or fallback to `lat/lng` for distance calculation
    - Document the change in comments
  - Add detailed logging for distance calculations to help debugging

### Step 4: Integrate Quality Score Calculation
- Modify `backend/app/tools/restaurant_search.py`:
  - Import the new scoring utility: `from app.utils.scoring import calculate_quality_score, calculate_distance_score, calculate_dumplin_score`
  - In `process_single_result()` function (lines 13-71):
    - Extract `totalScore` and `reviewsCount` from result
    - Calculate `quality_score = calculate_quality_score(totalScore, reviewsCount)`
    - Calculate `distance_score = calculate_distance_score(distance_km)`
    - Get `similarity_score` from result (already available)
    - Calculate `dumplin_score = calculate_dumplin_score(similarity_score, quality_score, distance_score)`
    - Add all scores to returned dictionary: `quality_score`, `distance_score`, `dumplin_score`
  - Update the returned dictionary to include the new scores

### Step 5: Update Sorting Logic in Restaurant Search Tool
- Modify `backend/app/tools/restaurant_search.py`:
  - Update sorting logic (line 274-275):
    - Change from: `formatted_results.sort(key=lambda x: (x.get("is_open", False), x.get("similarity_score", 0)), reverse=True)`
    - Change to: `formatted_results.sort(key=lambda x: (x.get("is_open", False), x.get("dumplin_score", 0)), reverse=True)`
  - Add logging to show top 5 restaurants with their dumplin_scores
  - Ensure `dumplin_score` is included in the JSON response returned to the agent

### Step 6: Update Test Export Utilities
- Modify `backend/app/test/export_utils.py`:
  - Add new columns to Excel export (around line 30):
    - `quality_score`
    - `distance_score`
    - `dumplin_score`
    - `totalScore` (raw rating)
    - `reviewsCount` (raw review count)
  - Add these fields to help debug and validate the scoring system
  - Ensure TEST_MODE exports show all scoring components for analysis

### Step 7: Update Food Agent Sorting
- Modify `backend/app/agents/food_agent.py`:
  - Update restaurant_info dictionary (line 550):
    - Add `dumplin_score` to the restaurant info: `"dumplin_score": metadata.get("dumplin_score", 0)`
    - Add `quality_score`: `"quality_score": metadata.get("quality_score", 0)`
    - Add `distance_score`: `"distance_score": metadata.get("distance_score", 0)`
  - Update sorting logic (lines 560-561):
    - Change from: `restaurants.sort(key=lambda x: (x.get("is_open", False), x.get("similarity_score", 0)), reverse=True)`
    - Change to: `restaurants.sort(key=lambda x: (x.get("is_open", False), x.get("dumplin_score", 0)), reverse=True)`
  - Update history formatting to include dumplin_score in the restaurant summary

### Step 8: Update Place Model (Optional)
- Modify `backend/app/models/places.py`:
  - Add new optional fields to the `Place` model:
    - `dumplin_score: Optional[float] = Field(None, description="Dumplin composite score (relevancy + quality + distance)")`
    - `quality_score: Optional[float] = Field(None, description="Quality score from ratings and reviews")`
    - `distance_score: Optional[float] = Field(None, description="Distance score (inverse of distance)")`
  - Add docstrings explaining each score component

### Step 9: Create Documentation
- Create `specs/DUMPLIN-SCORING-SYSTEM.md` with:
  - Complete formula explanation with examples
  - Weight justification and tuning guidelines
  - Edge case handling documentation
  - Example calculations for 3-5 restaurant scenarios
  - Instructions for adjusting weights
  - Performance impact analysis
  - A/B testing recommendations

### Step 10: Integration Testing
- Test the complete flow end-to-end:
  - Start the backend server with TEST_MODE enabled
  - Make a restaurant search query via the API
  - Verify dumplin_score is calculated correctly in the Excel export
  - Check that restaurants are sorted by dumplin_score (after is_open)
  - Test edge cases:
    - Restaurants with no reviews (reviewsCount = 0)
    - Restaurants very far away (> 35km)
    - Restaurants with perfect ratings (5.0) vs high relevancy (similarity_score = 0.95)
  - Verify distance calculation uses search coordinates, not user coordinates
  - Check logs for scoring calculation details

### Step 11: Validate Distance Fix
- Create test scenarios to verify the distance fix:
  - User outside city bounds (user coords != search coords)
    - Example: User at (40.6, -74.1), Search center at (40.7, -74.0)
    - Verify distance is calculated from search center (40.7, -74.0)
  - User inside city bounds (user coords == search coords)
    - Verify distance calculation still works correctly
  - Log both user and search coordinates for each query
  - Compare old distance vs new distance in test exports

### Step 12: Regression Testing
- Ensure no existing functionality is broken:
  - Test similarity-only ranking still works if dumplin_score calculation fails
  - Test that open/closed sorting still takes precedence
  - Test price filtering still works
  - Test radius filtering still works
  - Test city filtering still works
  - Test exclusion logic (exclude_place_ids) still works
  - Run full backend test suite: `pytest backend/app/test/`
  - Check for any warnings or errors in logs

## Testing Strategy

### Unit Tests

**Test Scoring Functions:**
- `test_normalize_score_basic()`: Test normalization with typical values (0.5 → 0.5 in 0-1 range)
- `test_normalize_score_edge_cases()`: Test with 0, negative, beyond max
- `test_calculate_quality_score_perfect()`: Test perfect restaurant (5.0 rating, 1000 reviews)
- `test_calculate_quality_score_no_reviews()`: Test with 0 reviews
- `test_calculate_quality_score_few_reviews()`: Test with 1-5 reviews
- `test_calculate_distance_score_close()`: Test very close restaurant (0.5km)
- `test_calculate_distance_score_far()`: Test far restaurant (30km)
- `test_calculate_distance_score_beyond_max()`: Test beyond max distance (50km > 35km max)
- `test_calculate_dumplin_score_balanced()`: Test with typical values for all components
- `test_calculate_dumplin_score_weights()`: Test with different weight configurations
- `test_calculate_dumplin_score_missing_components()`: Test with None/0 values

**Test Distance Calculation Fix:**
- `test_distance_from_search_coords()`: Verify distance is calculated from search coordinates
- `test_distance_user_outside_city()`: Test when user is outside city bounds
- `test_distance_user_inside_city()`: Test when user is inside city bounds

**Test Sorting Logic:**
- `test_sorting_open_first()`: Verify open restaurants always come first
- `test_sorting_by_dumplin_score()`: Verify sorting by dumplin_score within open/closed groups
- `test_sorting_fallback()`: Verify fallback to similarity_score if dumplin_score is missing

### Integration Tests

**End-to-End Search Flow:**
1. Query: "Find pizza near me" with user outside city bounds
   - Verify distance is from search center, not user location
   - Verify dumplin_score is calculated
   - Verify sorting is by dumplin_score
2. Query: "Find cheap restaurants" with price filtering
   - Verify dumplin_score works with price filters
   - Verify sorting maintains price filter
3. Query: "Show more restaurants" with exclusion
   - Verify excluded restaurants are not returned
   - Verify dumplin_score is calculated for new restaurants
4. Query: "Find Italian restaurants" with high similarity
   - Verify relevancy weight is dominant
   - Compare ranking with old similarity-only approach

### Edge Cases

**Data Edge Cases:**
- Restaurant with 0 reviews (reviewsCount = 0)
  - Expected: quality_score should be low but not 0
  - Validate: Uses only rating component of quality score
- Restaurant with null totalScore
  - Expected: Graceful fallback, quality_score = 0
  - Validate: No crashes, logging shows missing data
- Restaurant at exact search coordinates (0km distance)
  - Expected: distance_score = 1.0
  - Validate: Perfect distance score
- Restaurant beyond max distance (50km when max = 35km)
  - Expected: distance_score close to 0
  - Validate: Inverse distance calculation handles large distances
- Restaurant with very high similarity (0.99) but low quality (2.5 rating, 3 reviews)
  - Expected: dumplin_score balanced by quality weight
  - Validate: Doesn't rank #1 if better overall options exist

**User Location Edge Cases:**
- User at city center (user coords == search coords)
  - Expected: No difference from current behavior
- User far outside city bounds (50km away)
  - Expected: Distance calculated from search center, not user location
  - Validate: Fixed distance calculation
- No user location provided (latitude/longitude = None)
  - Expected: Graceful handling, distance_score = 0 or default
- Invalid coordinates (out of range)
  - Expected: Error handling, fallback to defaults

**Scoring Edge Cases:**
- All three scores are 0
  - Expected: dumplin_score = 0, restaurant ranks last
- One component score is missing (e.g., quality_score = None)
  - Expected: Treat as 0, calculate with other components
- Weights don't sum to 1.0
  - Expected: Still works, but document expected weight ranges

## Acceptance Criteria

1. **Dumplin Score Calculation**
   - [ ] `dumplin_score` is calculated for every restaurant returned from search
   - [ ] Score includes all three components: relevancy, quality, distance
   - [ ] Score is between 0 and 1
   - [ ] Score is included in restaurant data returned to frontend

2. **Distance Fix**
   - [ ] Distance is calculated from `search_latitude/search_longitude`, not user GPS coordinates
   - [ ] When user is outside city bounds, distance is from city center
   - [ ] When user is inside city bounds, distance is from user location
   - [ ] Distance calculation is logged for debugging

3. **Quality Score**
   - [ ] Quality score is calculated from `totalScore` and `reviewsCount`
   - [ ] Restaurants with 0 reviews receive a low but non-zero quality score
   - [ ] Higher review counts improve quality score (with diminishing returns)
   - [ ] Quality score is normalized to 0-1 range

4. **Sorting Behavior**
   - [ ] Open restaurants are always ranked before closed restaurants (unchanged)
   - [ ] Within open/closed groups, restaurants are sorted by `dumplin_score` descending
   - [ ] Sorting works correctly even if some restaurants have missing score components
   - [ ] Previous sorting by `similarity_score` is replaced by `dumplin_score`

5. **No Regressions**
   - [ ] All existing tests pass
   - [ ] Price filtering still works
   - [ ] Radius filtering still works
   - [ ] City filtering still works
   - [ ] Exclusion logic still works
   - [ ] Restaurant details still load correctly
   - [ ] Frontend displays restaurants without errors

6. **Testing & Documentation**
   - [ ] Unit tests cover all scoring functions with 90%+ coverage
   - [ ] Integration tests verify end-to-end scoring flow
   - [ ] Edge cases are tested and handled gracefully
   - [ ] Documentation explains scoring formula and weights
   - [ ] Test exports include all score components for debugging

7. **Performance**
   - [ ] Scoring calculation adds < 50ms to search latency
   - [ ] Parallel processing still works efficiently
   - [ ] No additional database queries required
   - [ ] Logging doesn't significantly impact performance

8. **Observability**
   - [ ] Scoring calculations are logged at debug level
   - [ ] Test exports show all score components for analysis
   - [ ] Easy to identify which component influences ranking most
   - [ ] Can compare old similarity-only ranking vs new dumplin_score ranking
