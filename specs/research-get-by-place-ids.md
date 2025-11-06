# Request
`def get_by_place_ids` - What does this get used on? What does it return?

## Request Description
The `get_by_place_ids` method is a core data retrieval function in the VectorSearch utility class that fetches restaurant information from MongoDB's `place_embeddings` collection using a list of place IDs. It serves as a direct lookup mechanism to retrieve complete restaurant details when you already know the specific place IDs you want, as opposed to vector search which finds restaurants based on semantic similarity.

**Purpose and Value:**
- **Direct Retrieval**: Fetch restaurants by exact IDs without semantic search
- **Filtering Support**: Apply additional filters (radius, city, price tier) on top of ID-based retrieval
- **Distance Calculation**: Automatically calculates distance and travel time from user location
- **Performance**: More efficient than vector search when you already have IDs
- **Flexibility**: Supports conditional inclusion of posts (social media content) to reduce payload size

## Relevant Files

### Primary Implementation
1. **`backend/app/utils/vector_search.py:133-231`** - Core implementation of `get_by_place_ids`
2. **`backend/app/utils/vector_search.py:10-17`** - VectorSearch class initialization and MongoDB connection

### Usage Locations
3. **`backend/app/agents/food_agent.py:496-509`** - Used to fetch restaurant metadata when filtering results
4. **`backend/app/tools/restaurant_details.py:55-60`** - Used by get_restaurant_details tool
5. **`backend/app/tools/favorites.py:105-117`** - Used by get_favorites tool for non-semantic favorite searches

### Documentation
6. **`specs/WHERE-TO-SEE-MONGODB-FIELDS.md`** - Complete field documentation for place_embeddings collection
7. **`specs/WHEN-URLS-ARE-FETCHED.md:143-148, 313-316`** - Examples of usage with include_posts parameter

## Inputs

### Function Signature
```python
def get_by_place_ids(
    self,
    place_ids: List[str],              # Required
    lat: Optional[float] = None,       # Optional - user location for distance calc
    lng: Optional[float] = None,       # Optional - user location for distance calc
    include_posts: bool = False,       # Optional - whether to include social posts
    radius_km: Optional[float] = None, # Optional - filter by radius
    radius_lat: Optional[float] = None,# Optional - center of radius (overrides lat)
    radius_lng: Optional[float] = None,# Optional - center of radius (overrides lng)
    city_name: Optional[str] = None,   # Optional - filter by city
    price_tier_min: Optional[int] = None,    # Optional - min price tier (1-5)
    price_tier_max: Optional[int] = None,    # Optional - max price tier (1-5)
    sort_by_price: bool = False        # Optional - sort by price instead of similarity
) -> List[Dict[str, Any]]
```

### Input Format & Trigger Conditions

**Required:**
- `place_ids`: List of MongoDB ObjectId strings (e.g., `["507f1f77bcf86cd799439011", "507f191e810c19729de860ea"]`)

**Optional Parameters:**
1. **Distance Calculation** - Requires `lat` and `lng`
   - When provided: Calculates distance_km and distance_string for each restaurant
   - When omitted: Sets distance_km to 0.0 and distance_string to "4-5 min"

2. **Social Media Posts** - `include_posts`
   - `True`: Returns posts array with Instagram/TikTok content
   - `False` (default): Excludes posts to reduce payload size

3. **Radius Filtering** - Requires `radius_km` + coordinates
   - Uses `radius_lat/radius_lng` if provided (search location)
   - Falls back to `lat/lng` if radius coordinates not provided (user location)
   - Applies MongoDB `$geoWithin` query to filter by distance

4. **City Filtering** - `city_name`
   - Applies case-insensitive regex match on city field
   - Example: "New York" matches "new york", "NEW YORK", etc.

5. **Price Filtering** - `price_tier_min` and `price_tier_max`
   - Filters restaurants by price tier (1=cheapest to 5=most expensive)
   - Can specify both min and max or just one

6. **Sorting** - `sort_by_price`
   - `True`: Sort by price_tier ascending, then similarity_score descending
   - `False` (default): Sort by similarity_score descending only

### Input Validation
- Converts string place_ids to MongoDB ObjectIds
- Skips invalid IDs (catches exceptions silently)
- Returns empty list if no valid ObjectIds

## Outputs

### Return Format
Returns a `List[Dict[str, Any]]` containing restaurant documents with the following structure:

### Output Structure
```python
[
    {
        # IDs
        "_id": ObjectId,
        "place_id": ObjectId,

        # Basic Info
        "title": "Joe's Pizza",
        "description": "Classic NY-style pizza...",
        "embedding_text": "Aggregated description for search...",

        # Location
        "location": {
            "type": "Point",
            "coordinates": [-73.9973, 40.7331]  # [lng, lat]
        },
        "address": "7 Carmine St",
        "neighborhood": "Greenwich Village",
        "city": "New York",
        "state": "NY",
        "countryCode": "US",
        "postal_code": "10014",
        "timezone": "America/New_York",

        # Categories
        "categoryName": "Pizza Restaurant",
        "categories": ["Italian", "Pizza", "Casual Dining"],

        # Ratings
        "totalScore": 4.6,
        "reviewsCount": 2847,

        # Pricing
        "price": "$$",
        "price_tier": 2,  # 1-5 scale

        # Contact
        "phone": "+1 212-555-0100",
        "website": "https://joespizza.com",
        "url": "https://maps.google.com/?cid=...",  # Google Maps URL

        # Hours (or openingHours)
        "open_hours": [
            {
                "day": "Monday",
                "hours_string": "11:00 AM - 11:00 PM",
                "time_ranges": [...]
            }
        ],

        # Status
        "permanentlyClosed": false,
        "temporarilyClosed": false,

        # Social Media (only if include_posts=True)
        "posts": [
            {
                "_id": ObjectId,
                "caption": "Best slice in NYC!",
                "thumbnail_url": "https://...",
                "media_url": "https://...",
                "permalink": "https://instagram.com/p/...",
                "media_type": "IMAGE",
                "timestamp": ISODate("2024-01-15T...")
            }
        ],

        # Calculated Fields (added by this method)
        "distance_km": 2.5,              # Calculated if lat/lng provided
        "distance_string": "10-15 min",  # Calculated if lat/lng provided
        "similarity_score": 1.0,         # Always 1.0 (perfect match for direct ID lookup)

        # Note: "embedding" field is EXCLUDED (not returned)
    }
]
```

### Output Destinations & Consumers

**1. Food Agent (backend/app/agents/food_agent.py:496-509)**
- **Purpose**: Fallback when restaurant_metadata is empty during filtering operations
- **Usage**: Fetches full restaurant data when user filters existing results (e.g., "only open", "only Italian")
- **Processing**: Serializes documents and stores in restaurant_metadata dictionary
- **Flow**: Results → serialize → restaurant_metadata[place_id] → restaurant_info dict → frontend

**2. Restaurant Details Tool (backend/app/tools/restaurant_details.py:55-60)**
- **Purpose**: Fetch detailed information for specific restaurants by ID
- **Usage**: When user asks for details like "address", "hours", "phone", "directions"
- **Processing**: Formats into simplified details dict, converts ObjectIds to strings
- **Flow**: Results → format details → JSON string → LLM agent → markdown response → frontend

**3. Favorites Tool (backend/app/tools/favorites.py:105-117)**
- **Purpose**: Retrieve user's saved favorite restaurants
- **Usage**: When user requests "my favorites", "saved places", or filtered favorites
- **Processing**: Further processes with place_service for is_open status, then formats as cards
- **Flow**: Results → process_favorite_results() → formatted cards → JSON → LLM agent → card UI → frontend

### Sort Order
- **Default**: `similarity_score` descending (always 1.0, so maintains query order)
- **With sort_by_price=True**: `price_tier` ascending, then `similarity_score` descending

### Empty Result Cases
Returns empty list `[]` when:
- No valid ObjectIds after conversion
- No matching documents in database
- All documents filtered out by radius/city/price criteria
- Exception occurs during query (caught and logged)

## Notes

### Key Design Patterns

1. **Dual Coordinate System**
   - `lat/lng` = User's actual location (for distance calculation)
   - `radius_lat/radius_lng` = Search center location (for filtering)
   - This allows filtering by search area while calculating distance from user

2. **Projection Strategy**
   - **Excludes**: Only the `embedding` field (1536-dimensional vector)
   - **Includes**: ALL other fields by default (blacklist approach)
   - Conditional exclusion of `posts` field when `include_posts=False`

3. **Perfect Similarity Score**
   - Always returns `similarity_score: 1.0` for all results
   - Rationale: Direct ID match = perfect relevance
   - Differs from `search_by_text()` which has varying similarity scores

4. **Error Handling**
   - Silently catches and skips invalid ObjectIds during conversion
   - Returns empty list on any exception (doesn't throw)
   - Logs errors but doesn't expose them to caller

### Performance Considerations

1. **When to Use vs search_by_text()**
   - Use `get_by_place_ids`: When you have specific IDs (favorites, filtering, details)
   - Use `search_by_text`: When searching by keywords/semantic meaning
   - get_by_place_ids is faster as it uses indexed _id lookup vs vector search

2. **Payload Size Management**
   - Set `include_posts=False` when social media content not needed
   - Each post includes image URLs and metadata (~1-2KB per post)
   - Can significantly reduce response size for multi-restaurant queries

3. **Index Requirements**
   - Requires index on `place_id` field for efficient lookup
   - Requires 2dsphere index on `location` field for radius filtering
   - Requires index on `price_tier` for price-based queries

### Integration with Scoring System

**Current State:**
- Returns restaurants with basic fields
- Similarity score is hardcoded to 1.0
- Distance calculated but not used for scoring

**Future Enhancement (per DUMPLIN-SCORING-SYSTEM.md):**
- Should calculate dumplin_score (composite relevancy + quality + distance)
- Should calculate quality_score (from totalScore and reviewsCount)
- Should calculate distance_score (inverse distance, closer = higher)
- Currently only implemented in `search_by_text()`, not yet in `get_by_place_ids()`

### MongoDB Collection Structure

**Collection**: `place_embeddings`
**Source**: Combination of `places` + `posts` collections
**Purpose**: Unified search index combining venue data and social media content

**Data Flow:**
```
places collection (venue details)
    +
posts collection (Instagram/TikTok content)
    +
embedding generation (1536-dimensional vectors)
    =
place_embeddings collection (searchable unified data)
```

### Common Usage Patterns

**Pattern 1: Fetch Favorites**
```python
favorites = vector_search.get_by_place_ids(
    place_ids=user_favorite_ids,
    lat=user_lat,
    lng=user_lng,
    include_posts=True
)
```

**Pattern 2: Fetch Details**
```python
details = vector_search.get_by_place_ids(
    place_ids=["place_id_1", "place_id_2"],
    lat=user_lat,
    lng=user_lng,
    include_posts=True  # For rich content display
)
```

**Pattern 3: Nearby Favorites**
```python
nearby_favs = vector_search.get_by_place_ids(
    place_ids=user_favorite_ids,
    lat=search_lat,
    lng=search_lng,
    radius_km=10,
    radius_lat=search_lat,  # Filter by search location
    radius_lng=search_lng,
    include_posts=True
)
```

**Pattern 4: Budget Favorites**
```python
cheap_favs = vector_search.get_by_place_ids(
    place_ids=user_favorite_ids,
    lat=user_lat,
    lng=user_lng,
    price_tier_min=1,
    price_tier_max=2,
    sort_by_price=True
)
```

### Comparison with Related Methods

| Method | Purpose | Input | Scoring |
|--------|---------|-------|---------|
| `get_by_place_ids` | Direct ID lookup | List of IDs | similarity_score = 1.0 |
| `search_by_text` | Semantic search | Query text | similarity_score = 0.0-1.0 (from vector search) |
| `get_by_place_id` | Single ID lookup | One ID | similarity_score = 1.0 |

### Debugging Tips

1. **Check if restaurant_metadata is empty**: Log at food_agent.py:488
2. **Verify ObjectId conversion**: Check logs for conversion failures
3. **Inspect returned fields**: Add logging after line 195 in vector_search.py
4. **Verify distance calculation**: Check if lat/lng provided and location.coordinates valid
5. **Check filtering logic**: Verify radius/city/price filters in query_conditions (line 157)
