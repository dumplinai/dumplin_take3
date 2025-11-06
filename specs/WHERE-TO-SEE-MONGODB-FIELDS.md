# WHERE TO SEE MONGODB FIELDS/COLUMNS

## 1. IN THE CODE - PROJECTION STATEMENT

**Location:** `backend/app/utils/vector_search.py:330-332` (and 344-346)

```python
{
    "$project": {
        "embedding": 0  # ← ONLY excludes embedding field
    }
}
```

**What this means:**
- `"embedding": 0` = EXCLUDE this field
- ALL other fields are INCLUDED (returned)
- This is MongoDB's blacklist syntax (exclude one, return everything else)

**If we wanted to select specific columns, it would look like:**
```python
{
    "$project": {
        "title": 1,
        "url": 1,
        "posts": 1
    }
}
```
But we DON'T do this. We return everything except embedding.

---

## 2. IN THE CODE - FIELDS ACCESSED

**Location:** `backend/app/agents/food_agent.py:523-552`

This shows ALL fields that are read from MongoDB results:

```python
restaurant_info = {
    "_id": str(stored_data.get("place_id", stored_data.get("_id", ""))),
    "title": stored_data.get("title", ""),
    "description": stored_data.get("description", ""),
    "enhanced_description": metadata.get("explanation", ""),
    "address": stored_data.get("address", ""),
    "neighborhood": stored_data.get("neighborhood", ""),
    "city": stored_data.get("city", ""),
    "state": stored_data.get("state", ""),
    "country": stored_data.get("countryCode", ""),
    "postal_code": stored_data.get("postal_code", ""),
    "location": stored_data.get("location", {}),
    "categoryName": stored_data.get("categoryName", ""),
    "categories": stored_data.get("categories", []),
    "totalScore": stored_data.get("totalScore", 0),
    "reviewsCount": stored_data.get("reviewsCount", 0),
    "price": stored_data.get("price", ""),
    "phone": stored_data.get("phone", ""),
    "website": stored_data.get("website", ""),
    "url": stored_data.get("url", ""),                    # ← Google Maps URL
    "distance_km": distance_km,
    "distance_string": distance_string,
    "openingHours": stored_data.get("open_hours", stored_data.get("openingHours", [])),
    "permanentlyClosed": stored_data.get("permanentlyClosed", False),
    "temporarilyClosed": stored_data.get("temporarilyClosed", False),
    "is_open": is_open,
    "posts": stored_data.get("posts", []),                # ← Social media posts
    "similarity_score": metadata.get("similarity_score", 0),
    "dumplin_score": metadata.get("dumplin_score", 0),   # ← Dumplin composite score
    "quality_score": metadata.get("quality_score", 0),   # ← Quality score
    "distance_score": metadata.get("distance_score", 0), # ← Distance score
}
```

**These fields come from MongoDB place_embeddings collection!**

---

## 3. MONGODB SCHEMA DOCUMENTATION

**Location:** `../abrar-handoff/Dumplin-ETL/mongo_db_samples/collections.md:159-166`

```
posts + places → place_embeddings
- place_embeddings.place_id → places._id
- Combines social content data from posts with detailed place information
- Creates vector embeddings for semantic search by the chat agent
- Aggregates:
  - Post transcripts, captions, and creator information
  - Place details, ratings, categories, and location data
```

**place_embeddings = places data + posts data + embeddings**

---

## 4. COMPLETE FIELD LIST (from code analysis)

### Fields in place_embeddings collection:

```javascript
{
    // IDs:
    _id: ObjectId,
    place_id: ObjectId,

    // Basic Info:
    title: String,
    description: String,
    embedding_text: String,     // Aggregated description for semantic search

    // Location:
    location: {
        type: "Point",
        coordinates: [Number, Number]  // [lng, lat]
    },
    address: String,
    neighborhood: String,
    city: String,
    state: String,
    countryCode: String,
    postal_code: String,
    timezone: String,

    // Categories:
    categoryName: String,
    categories: [String],

    // Ratings:
    totalScore: Number,
    reviewsCount: Number,

    // Dumplin Scoring (calculated at search time):
    dumplin_score: Number,      // Composite score (relevancy + quality + distance) 0-1
    quality_score: Number,      // Quality score from ratings/reviews 0-1
    distance_score: Number,     // Distance score (inverse, closer=higher) 0-1

    // Pricing:
    price: String,              // e.g., "$$"
    price_tier: Number,         // 1-5

    // Contact:
    phone: String,
    website: String,
    url: String,                // ← Google Maps URL

    // Hours:
    open_hours: [               // or openingHours
        {
            day: String,
            hours_string: String,
            time_ranges: [Object]
        }
    ],

    // Status:
    permanentlyClosed: Boolean,
    temporarilyClosed: Boolean,

    // Social Media:
    posts: [                    // ← Instagram/TikTok posts
        {
            _id: ObjectId,
            caption: String,
            thumbnail_url: String,
            media_url: String,
            permalink: String,
            media_type: String,
            timestamp: Date
        }
    ],

    // Search:
    embedding: [Number],        // 1536 floats - EXCLUDED in queries
    similarity_score: Number    // ADDED by $vectorSearch during query
}
```

---

## 5. HOW TO SEE ACTUAL DATA

### Option A: Query MongoDB directly

You can use the MongoDB connection string from `.env` to query:

```bash
# In backend directory
mongosh "your_mongodb_uri"

use DumplinAI
db.place_embeddings.findOne()
```

This will show you one complete document with all fields.

### Option B: Add logging to see what MongoDB returns

**Location:** `backend/app/utils/vector_search.py:413`

Add after line 413:

```python
results = list(self.collection.aggregate(pipeline))

# Add this to see what MongoDB returns:
import json
if results:
    print("MongoDB returned fields:", list(results[0].keys()))
    print("First result:", json.dumps(serialize_mongodb_document(results[0]), indent=2))
```

Run a search and check logs to see all fields.

### Option C: Check what's saved to state

**Location:** `backend/app/tools/restaurant_search.py:216`

Add after line 216:

```python
state["restaurant_metadata"][place_id] = serialize_mongodb_document(result_copy)

# Add this:
print("Saved to state, fields:", list(result_copy.keys()))
```

---

## 6. PROOF URLs AND POSTS ARE INCLUDED

**From the code at `backend/app/agents/food_agent.py:523-552`:**

```python
"url": stored_data.get("url", ""),          # ← This field exists in MongoDB!
"posts": stored_data.get("posts", []),      # ← This field exists in MongoDB!
```

**If these fields didn't exist in MongoDB, the code would:**
1. Always get empty strings for url
2. Always get empty arrays for posts
3. Frontend would show nothing

**But we know the app works and shows:**
- Google Maps links (from url field)
- Instagram posts (from posts field)

**Therefore, these fields MUST be in place_embeddings collection!**

---

## 7. THE COMPLETE QUERY

Here's what happens:

```python
# 1. Vector search finds similar restaurants
{
    "$vectorSearch": {
        "queryVector": [0.123, -0.456, ...],
        "limit": 50
    }
}

# 2. Add similarity score
{
    "$addFields": {
        "similarity_score": {"$meta": "vectorSearchScore"}
    }
}

# 3. Filter by location, city, etc.
{
    "$match": {
        "location": {"$geoWithin": {...}},
        "city": {"$regex": "New York"},
        "place_id": {"$nin": [exclude_ids]}
    }
}

# 4. Sort by similarity
{
    "$sort": {"similarity_score": -1}
}

# 5. Limit results
{
    "$limit": 5
}

# 6. Exclude only embedding field
{
    "$project": {
        "embedding": 0  # ← Only this is excluded
    }
}

# MongoDB returns:
{
    _id: "...",
    place_id: "...",
    title: "Joe's Pizza",
    url: "https://maps.google.com/...",     # ← INCLUDED
    posts: [{...}, {...}],                   # ← INCLUDED
    phone: "+1 212-555-0100",                # ← INCLUDED
    website: "https://joespizza.com",        # ← INCLUDED
    address: "7 Carmine St",                 # ← INCLUDED
    open_hours: [...],                       # ← INCLUDED
    similarity_score: 0.89,                  # ← ADDED
    # ... ALL OTHER FIELDS INCLUDED
    # embedding: [...] ← ONLY THIS IS EXCLUDED
}
```

---

## SUMMARY

**Where to see MongoDB columns being selected:**

1. **Code:** `backend/app/utils/vector_search.py:330-332` - Only excludes "embedding"
2. **Code:** `backend/app/agents/food_agent.py:523-552` - Shows all fields accessed
3. **Schema:** `../abrar-handoff/Dumplin-ETL/mongo_db_samples/collections.md` - Describes place_embeddings
4. **Database:** Query MongoDB directly with `db.place_embeddings.findOne()`
5. **Logs:** Add print statements to see actual data returned

**Key point:** MongoDB $project with `{"embedding": 0}` means "exclude ONLY embedding, return EVERYTHING else"

This is why url, posts, phone, website, and all other fields are available immediately!
