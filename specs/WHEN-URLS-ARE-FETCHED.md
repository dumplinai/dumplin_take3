# WHEN DO WE GET URLs AND POSTS?

## YOUR QUESTION
"Do we not really get the social media URL or the Google Maps URL until after this?"

## THE ANSWER

**NO - We get them immediately from MongoDB!**

The URLs and posts are included in the FIRST MongoDB search.

---

## WHAT MONGODB RETURNS (place_embeddings collection)

### MongoDB Vector Search Returns EVERYTHING except embedding:
**Location:** `backend/app/utils/vector_search.py:330-347`

```python
# MongoDB projection:
{
    "$project": {
        "embedding": 0  # ONLY exclude embedding field
    }
}
```

**This means MongoDB returns ALL other fields including:**
- `url` (Google Maps URL)
- `posts` (Social media posts array)
- `title`, `description`, `address`
- `location`, `open_hours`, `price_tier`
- Everything else!

---

## THE COMPLETE DATA FLOW

### STEP 1: MongoDB Vector Search
**Location:** `backend/app/utils/vector_search.py:413`

```python
results = list(self.collection.aggregate(pipeline))

# Returns from place_embeddings collection:
results = [
    {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "place_id": ObjectId("507f1f77bcf86cd799439011"),
        "title": "Joe's Pizza",
        "embedding_text": "Classic New York pizza...",
        "location": {"type": "Point", "coordinates": [-74.0020, 40.7300]},
        "city": "New York",
        "timezone": "America/New_York",
        "open_hours": [...],
        "price_tier": 2,
        "similarity_score": 0.8934567,

        # THESE ARE INCLUDED:
        "url": "https://maps.google.com/?cid=12345",  ← Google Maps URL
        "website": "https://joespizza.com",
        "phone": "+1 212-555-0100",
        "address": "7 Carmine St, New York, NY 10014",
        "posts": [                                     ← Social media posts
            {
                "_id": ObjectId("..."),
                "caption": "Best pizza in NYC!",
                "thumbnail_url": "https://...",
                "media_url": "https://...",
                "permalink": "https://instagram.com/p/...",
                "media_type": "IMAGE",
                "timestamp": "2024-01-15T12:00:00Z"
            },
            # ... more posts
        ],

        # embedding field EXCLUDED (would be 1536 numbers)
        # BUT EVERYTHING ELSE IS INCLUDED!
    },
    # ... 4 more restaurants with same structure
]
```

**MongoDB returns FULL data immediately!**

---

### STEP 2: Tool Saves to State
**Location:** `backend/app/tools/restaurant_search.py:208-216`

```python
# Tool saves FULL data to state:
for result in results:
    place_id = str(result.get("place_id"))
    state["restaurant_metadata"][place_id] = result  # Includes url, posts, everything!
```

**State now contains:**
```python
state["restaurant_metadata"] = {
    "507f1f77bcf86cd799439011": {
        "title": "Joe's Pizza",
        "url": "https://maps.google.com/?cid=12345",  ← HERE!
        "website": "https://joespizza.com",
        "posts": [{...}, {...}],                      ← HERE!
        "open_hours": [...],
        # ... ALL fields
    },
    # ... other restaurants
}
```

---

### STEP 3: FoodAgent Uses State
**Location:** `backend/app/agents/food_agent.py:511-552`

```python
# FoodAgent reads from state:
for place_id in place_ids:
    stored_data = state["restaurant_metadata"].get(place_id)

    restaurant_info = {
        "title": stored_data.get("title", ""),
        "url": stored_data.get("url", ""),          ← From state (from MongoDB)
        "website": stored_data.get("website", ""),
        "posts": stored_data.get("posts", []),      ← From state (from MongoDB)
        "phone": stored_data.get("phone", ""),
        # ... all fields
    }
```

**FoodAgent pulls URLs and posts from state (which came from MongoDB in Step 1).**

---

## WHAT ABOUT include_posts=True?

You might see this in the code:

```python
# backend/app/agents/food_agent.py:496-501
fetched_restaurants = self.vector_search.get_by_place_ids(
    place_ids,
    lat=latitude,
    lng=longitude,
    include_posts=True  ← What's this?
)
```

**This is ONLY used when restaurant_metadata is empty** (line 488).

**When does that happen?**
- When user asks to filter existing results (e.g., "only show Italian")
- No new search was done, so state["restaurant_metadata"] is empty
- FoodAgent needs to fetch the full data

**In normal search flow:**
- MongoDB returns posts immediately
- `include_posts=True` is NOT needed
- Posts are already in state["restaurant_metadata"]

---

## place_embeddings COLLECTION STRUCTURE

The `place_embeddings` MongoDB collection contains:

```javascript
{
    _id: ObjectId,
    place_id: ObjectId,

    // Basic info:
    title: String,
    description: String,
    embedding_text: String,  // For semantic search

    // Location:
    location: {type: "Point", coordinates: [lng, lat]},
    address: String,
    city: String,
    state: String,
    postal_code: String,
    timezone: String,

    // Details:
    categories: [String],
    categoryName: String,
    price: String,        // "$$"
    price_tier: Number,   // 1-5
    phone: String,

    // URLs - THESE ARE IN place_embeddings!
    url: String,          // Google Maps URL
    website: String,      // Restaurant website

    // Hours:
    open_hours: [Object],

    // Rating:
    totalScore: Number,
    reviewsCount: Number,

    // Social media - THESE ARE IN place_embeddings!
    posts: [Object],      // Instagram posts

    // Search:
    embedding: [Number],  // 1536 numbers (excluded in queries)

    // Status:
    permanentlyClosed: Boolean,
    temporarilyClosed: Boolean
}
```

**place_embeddings is a COMPLETE copy** of restaurant data + embeddings for search.

---

## WHY DOES place_embeddings HAVE EVERYTHING?

The place_embeddings collection is designed for **fast vector search**.

**Instead of:**
1. Vector search on place_embeddings (fast)
2. Join to places collection for full data (slow)

**We do:**
1. Vector search on place_embeddings returns EVERYTHING (fast)
2. No join needed!

**All data is duplicated in place_embeddings for performance.**

---

## TIMELINE - WHEN DO WE GET URLs?

```
T1: User types "Find pizza"
    ↓
T2: GPT-4 calls search_restaurants tool
    ↓
T3: Tool calls vector_search.search_by_text()
    ↓
T4: MongoDB vector search executes
    MongoDB returns:
    ✓ url field                    ← WE GET IT HERE!
    ✓ posts field                  ← WE GET IT HERE!
    ✓ All other fields
    ✗ embedding (excluded)
    ↓
T5: Python calculates distance
    ↓
T6: Tool saves to state["restaurant_metadata"]
    state now contains:
    ✓ url                          ← SAVED TO STATE
    ✓ posts                        ← SAVED TO STATE
    ↓
T7: GPT-4 receives simplified JSON (without urls)
    (Only 8 fields for efficiency)
    ↓
T8: FoodAgent fetches from state["restaurant_metadata"]
    ✓ url available                ← RETRIEVED FROM STATE
    ✓ posts available              ← RETRIEVED FROM STATE
    ↓
T9: Frontend receives full restaurant objects
    ✓ url: "https://maps.google.com/..."
    ✓ posts: [{...}, {...}]
```

**URLs are fetched in T4 (MongoDB search) and available throughout.**

---

## SUMMARY

**Q: When do we get Google Maps URL and social media URLs?**

**A: IMMEDIATELY in the first MongoDB vector search!**

```
MongoDB Vector Search
    ↓
Returns ALL fields from place_embeddings
    ↓ including:
    • url (Google Maps)
    • posts (Social media)
    • website
    • phone
    • everything!
    ↓
Saved to state["restaurant_metadata"]
    ↓
Used by FoodAgent to build response
    ↓
Sent to frontend
```

**No second fetch needed!** Everything comes from the first search.

---

## EXCEPTION - When Second Fetch Happens

**ONLY when restaurant_metadata is empty:**

```python
# backend/app/agents/food_agent.py:488-501
if not restaurant_metadata and place_ids:
    # This only happens when filtering existing results
    # without doing a new search
    fetched_restaurants = self.vector_search.get_by_place_ids(
        place_ids,
        include_posts=True
    )
```

**When does this happen?**
- User says: "Only show Italian restaurants" (filtering previous results)
- No new search was performed
- state["restaurant_metadata"] is empty
- Need to fetch full data

**In normal "Find pizza" search:**
- restaurant_metadata is filled by the tool
- No second fetch needed
- URLs and posts already there!

---

## KEY TAKEAWAY

**place_embeddings collection = Complete restaurant data + embeddings**

When you do a vector search on place_embeddings:
- You get EVERYTHING (except the embedding vector itself)
- Including url, posts, phone, website, hours, etc.
- No joins, no second queries needed!

**URLs and posts come from the FIRST MongoDB search!**
