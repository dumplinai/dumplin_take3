# WHAT MONGODB RETURNS - COMPLETE BREAKDOWN

## THE QUESTION
What exactly does MongoDB return when the search tool executes in Step 8-9?

---

## THE COMPLETE FLOW

### STEP 8: GPT-4 CALLS TOOL
**Who:** GPT-4 (AI)

```python
GPT-4 calls: search_restaurants(
    search_text="pizza restaurants",
    radius_km=35.0,
    nearby_only=True
)
```

---

### STEP 9A: TOOL CALLS VECTOR SEARCH
**Location:** `backend/app/tools/restaurant_search.py:148-185`
**Who:** Python code

```python
# Tool calls:
results = vector_search.search_by_text(
    query_text="pizza restaurants",
    limit=5,
    lat=40.7589,                    # search_latitude
    lng=-73.9851,                   # search_longitude
    user_lat=40.7128,               # user_latitude
    user_lng=-74.0060,              # user_longitude
    radius_km=35.0,
    exclude_place_ids=["id3", "id4"],
    city_name="New York",
    price_tier_min=None,
    price_tier_max=None,
    sort_by_price=False
)
```

---

### STEP 9B: VECTOR SEARCH GENERATES EMBEDDING
**Location:** `backend/app/utils/vector_search.py:235-242`
**Who:** OpenAI API

```python
# Python code calls OpenAI:
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    api_key=settings.OPENAI_API_KEY,
    model="text-embedding-3-small"
)

query_embedding = embeddings.embed_query("pizza restaurants")
# Result: [0.123, -0.456, 0.789, ..., 0.321]  (1536 numbers)
```

**OpenAI returns:** Array of 1536 floating point numbers representing "pizza restaurants"

---

### STEP 9C: MONGODB VECTOR SEARCH QUERY
**Location:** `backend/app/utils/vector_search.py:269-348`
**Who:** MongoDB Atlas

```python
# Python builds MongoDB aggregation pipeline:
pipeline = [
    # STAGE 1: Vector search
    {
        "$vectorSearch": {
            "index": "embedding_vector_index",
            "path": "embedding",
            "queryVector": [0.123, -0.456, ...],  # The embedding
            "numCandidates": 100,  # 5 * 20
            "limit": 50            # 5 * 10
        }
    },

    # STAGE 2: Add similarity score
    {
        "$addFields": {
            "similarity_score": {"$meta": "vectorSearchScore"}
        }
    },

    # STAGE 3: Filter by location, city, price, exclusions
    {
        "$match": {
            "location": {
                "$geoWithin": {
                    "$centerSphere": [
                        [-73.9851, 40.7589],  # [lng, lat]
                        0.005494  # 35km in radians
                    ]
                }
            },
            "city": {"$regex": "New York", "$options": "i"},
            "place_id": {"$nin": [ObjectId("id3"), ObjectId("id4")]}
        }
    },

    # STAGE 4: Sort by similarity
    {
        "$sort": {"similarity_score": -1}
    },

    # STAGE 5: Limit to 5 results
    {
        "$limit": 5
    },

    # STAGE 6: Exclude embedding field (too large)
    {
        "$project": {
            "embedding": 0
        }
    }
]

# Python executes:
results = list(collection.aggregate(pipeline))
```

---

### STEP 9D: WHAT MONGODB RETURNS
**Location:** `backend/app/utils/vector_search.py:413`
**Database:** MongoDB `place_embeddings` collection

```python
results = [
    {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "place_id": ObjectId("507f1f77bcf86cd799439011"),
        "title": "Joe's Pizza",
        "embedding_text": "Classic New York pizza with thin crust and fresh ingredients. Known for their cheese slices and pepperoni. Casual atmosphere, quick service, great for lunch or late night. Popular with locals and tourists.",
        "location": {
            "type": "Point",
            "coordinates": [-74.0020, 40.7300]  # [lng, lat]
        },
        "city": "New York",
        "timezone": "America/New_York",
        "open_hours": [
            {
                "day": "Monday",
                "hours_string": "11:00 AM - 11:00 PM",
                "time_ranges": [
                    {
                        "open_24h": "11:00",
                        "close_24h": "23:00",
                        "overnight": False
                    }
                ]
            },
            # ... other days
        ],
        "price_tier": 2,
        "similarity_score": 0.8934567  # Added by $vectorSearch
        # NOTE: embedding field is EXCLUDED (would be 1536 numbers)
    },
    {
        "_id": ObjectId("507f1f77bcf86cd799439012"),
        "place_id": ObjectId("507f1f77bcf86cd799439012"),
        "title": "Prince Street Pizza",
        "embedding_text": "Famous for their pepperoni square slices. Thick Sicilian-style pizza with crispy bottom. Small shop, often has a line. Cash only. Must-try for pizza lovers.",
        "location": {
            "type": "Point",
            "coordinates": [-73.9960, 40.7230]
        },
        "city": "New York",
        "timezone": "America/New_York",
        "open_hours": [...],
        "price_tier": 2,
        "similarity_score": 0.8723451
    },
    # ... 3 more restaurants
]
```

**MONGODB RETURNS:**
- Array of 5 restaurant documents
- Each document has all fields EXCEPT "embedding" (excluded to save bandwidth)
- Includes `similarity_score` from vector search (how similar to "pizza restaurants")
- Documents are sorted by similarity_score (highest first)

---

### STEP 9E: PYTHON CALCULATES DISTANCE
**Location:** `backend/app/utils/vector_search.py:416-435`
**Who:** Python code (Haversine formula)

```python
# Python loops through results and calculates distance:
for result in results:
    location = result.get('location', {})
    place_coords = location.get('coordinates', [])
    # place_coords = [-74.0020, 40.7300]  (lng, lat)

    place_lng, place_lat = place_coords[0], place_coords[1]
    # place_lng = -74.0020
    # place_lat = 40.7300

    # Haversine formula:
    distance_km = self.calculate_distance_km(
        user_lat=40.7128,
        user_lng=-74.0060,
        place_lat=40.7300,
        place_lng=-74.0020
    )
    # Result: 1.95 km

    result['distance_km'] = round(1.95, 2)  # 1.95

    # Calculate time estimate:
    distance_string, _, _ = self._calculate_distance_info(1.95)
    # Result: "10-15 min"

    result['distance_string'] = "10-15 min"
```

**AFTER DISTANCE CALCULATION:**

```python
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
        "distance_km": 1.95,              # ← ADDED by Python
        "distance_string": "10-15 min"    # ← ADDED by Python
    },
    # ... 4 more
]
```

**Python ADDED to each result:**
- `distance_km`: Number (kilometers from user)
- `distance_string`: String (human-readable time estimate)

---

### STEP 9F: VECTOR SEARCH RETURNS TO TOOL
**Location:** `backend/app/utils/vector_search.py:437`

```python
# vector_search.search_by_text() returns:
return results  # List of 5 dicts with all fields + distance
```

**Tool receives 5 restaurant documents with:**
- All MongoDB fields (except embedding)
- similarity_score from MongoDB
- distance_km calculated by Python
- distance_string calculated by Python

---

### STEP 9G: TOOL SAVES TO STATE
**Location:** `backend/app/tools/restaurant_search.py:208-216`
**Who:** Python code

```python
# Tool writes FULL data to state:
if state is not None:
    if "restaurant_metadata" not in state:
        state["restaurant_metadata"] = {}

    for result in results:
        place_id = str(result.get("place_id"))
        # place_id = "507f1f77bcf86cd799439011"

        state["restaurant_metadata"][place_id] = result
```

**STATE IS NOW:**

```python
state["restaurant_metadata"] = {
    "507f1f77bcf86cd799439011": {
        # FULL restaurant document with ALL fields
        "title": "Joe's Pizza",
        "embedding_text": "Classic New York pizza...",
        "location": {...},
        "open_hours": [...],
        "price_tier": 2,
        "similarity_score": 0.8934567,
        "distance_km": 1.95,
        "distance_string": "10-15 min",
        # ... ALL fields
    },
    "507f1f77bcf86cd799439012": {...},
    # ... 3 more
}
```

**WHY SAVE TO STATE?**
- If user later asks "What's the address of the first place?"
- FoodAgent can fetch from state instead of querying MongoDB again
- Caching for performance

---

### STEP 9H: TOOL PROCESSES FOR GPT-4
**Location:** `backend/app/tools/restaurant_search.py:12-69, 218-272`
**Who:** Python code

```python
# Tool processes each result:
formatted_results = []

for result in results:
    # Extract key fields:
    place_id = str(result.get("place_id"))
    title = result.get("title")

    # Calculate if open:
    open_hours = result.get("open_hours", [])
    is_open = places_service.is_place_open(
        {"openingHours": open_hours},
        current_day="Monday",
        current_time_24h="18:30"
    )
    # Result: True (open at 6:30 PM on Monday)

    # Build simplified object for GPT-4:
    formatted_results.append({
        "place_id": place_id,
        "title": title,
        "embedding_text": result.get("embedding_text", ""),
        "similarity_score": round(result.get("similarity_score", 0), 4),
        "distance_km": result.get("distance_km", 0),
        "distance_string": result.get("distance_string", ""),
        "is_open": is_open,           # ← CALCULATED by Python
        "price_tier": result.get("price_tier")
    })

# Sort: Open restaurants first, then by similarity
formatted_results.sort(
    key=lambda x: (x.get("is_open", False), x.get("similarity_score", 0)),
    reverse=True
)
```

**AFTER PROCESSING:**

```python
formatted_results = [
    {
        "place_id": "507f1f77bcf86cd799439011",
        "title": "Joe's Pizza",
        "embedding_text": "Classic New York pizza...",
        "similarity_score": 0.8935,
        "distance_km": 1.95,
        "distance_string": "10-15 min",
        "is_open": True,              # ← CALCULATED
        "price_tier": 2
    },
    {
        "place_id": "507f1f77bcf86cd799439012",
        "title": "Prince Street Pizza",
        "embedding_text": "Famous for their pepperoni...",
        "similarity_score": 0.8723,
        "distance_km": 2.1,
        "distance_string": "10-15 min",
        "is_open": True,
        "price_tier": 2
    },
    # ... 3 more
]
```

**SIMPLIFIED FOR GPT-4:**
- Only 8 fields (not all 20+ fields from MongoDB)
- `is_open` calculated from open_hours + current time
- Sorted by open status first, then similarity

---

### STEP 9I: TOOL RETURNS TO GPT-4
**Location:** `backend/app/tools/restaurant_search.py:275`

```python
# Tool converts to JSON string:
result_json = json.dumps(formatted_results, indent=2)

return result_json
```

**GPT-4 RECEIVES:**

```json
[
  {
    "place_id": "507f1f77bcf86cd799439011",
    "title": "Joe's Pizza",
    "embedding_text": "Classic New York pizza with thin crust and fresh ingredients. Known for their cheese slices and pepperoni. Casual atmosphere, quick service, great for lunch or late night. Popular with locals and tourists.",
    "similarity_score": 0.8935,
    "distance_km": 1.95,
    "distance_string": "10-15 min",
    "is_open": true,
    "price_tier": 2
  },
  {
    "place_id": "507f1f77bcf86cd799439012",
    "title": "Prince Street Pizza",
    "embedding_text": "Famous for their pepperoni square slices. Thick Sicilian-style pizza with crispy bottom. Small shop, often has a line. Cash only. Must-try for pizza lovers.",
    "similarity_score": 0.8723,
    "distance_km": 2.1,
    "distance_string": "10-15 min",
    "is_open": true,
    "price_tier": 2
  },
  {
    "place_id": "507f1f77bcf86cd799439013",
    "title": "Artichoke Basille's Pizza",
    "embedding_text": "Unique artichoke pizza and spinach pizza. Thick, cheesy, filling slices. Open late for after-bar crowd. Multiple locations.",
    "similarity_score": 0.8651,
    "distance_km": 1.5,
    "distance_string": "10-15 min",
    "is_open": true,
    "price_tier": 2
  },
  {
    "place_id": "507f1f77bcf86cd799439014",
    "title": "Lombardi's Pizza",
    "embedding_text": "America's first pizzeria, opened in 1905. Coal oven pizza. Historic location. Sit-down restaurant with classic Italian atmosphere.",
    "similarity_score": 0.8598,
    "distance_km": 1.8,
    "distance_string": "10-15 min",
    "is_open": true,
    "price_tier": 3
  },
  {
    "place_id": "507f1f77bcf86cd799439015",
    "title": "John's of Bleecker Street",
    "embedding_text": "Traditional brick oven pizza since 1929. Whole pies only, no slices. Thin crust, charred edges. Cash only. Often crowded.",
    "similarity_score": 0.8542,
    "distance_km": 2.3,
    "distance_string": "10-15 min",
    "is_open": true,
    "price_tier": 2
  }
]
```

**This JSON string is what GPT-4 sees!**

---

## SUMMARY - WHAT MONGODB RETURNS

### WHAT MONGODB ACTUALLY RETURNS:
```python
{
    "_id": ObjectId,
    "place_id": ObjectId,
    "title": string,
    "embedding_text": string (description),
    "location": {type: "Point", coordinates: [lng, lat]},
    "city": string,
    "timezone": string,
    "open_hours": array of objects,
    "price_tier": int (1-5),
    "similarity_score": float (0-1),
    # embedding field EXCLUDED
}
```

### WHAT PYTHON ADDS:
```python
{
    "distance_km": float (calculated by Haversine),
    "distance_string": string (time estimate)
}
```

### WHAT PYTHON CALCULATES:
```python
{
    "is_open": boolean (from open_hours + current time)
}
```

### WHAT GPT-4 RECEIVES (simplified):
```python
{
    "place_id": string,
    "title": string,
    "embedding_text": string,
    "similarity_score": float,
    "distance_km": float,
    "distance_string": string,
    "is_open": boolean,
    "price_tier": int
}
```

### WHAT STATE STORES (full):
```python
state["restaurant_metadata"] = {
    "place_id_1": {ALL MongoDB fields + distance},
    "place_id_2": {ALL MongoDB fields + distance},
    # ... all results
}
```

---

## THE COMPLETE PICTURE

```
MONGODB
├─ Stores: place_embeddings collection
├─ Vector search finds 5 similar restaurants
├─ Returns: All fields except "embedding"
└─ Includes: similarity_score from vector search

                    ↓

PYTHON CODE (vector_search.py)
├─ Calculates: distance_km (Haversine formula)
├─ Calculates: distance_string (time estimate)
└─ Returns: MongoDB results + distance

                    ↓

PYTHON CODE (tool)
├─ Saves: Full data to state["restaurant_metadata"]
├─ Calculates: is_open from open_hours + time
├─ Simplifies: Only 8 fields for GPT-4
└─ Returns: JSON string to GPT-4

                    ↓

GPT-4
├─ Receives: Simplified JSON with 8 fields
├─ Formats: User-friendly response
└─ Returns: "Here are 5 pizza places! 🍕"

                    ↓

PYTHON CODE (FoodAgent)
├─ Gets: place_ids from GPT-4's response
├─ Fetches: Full data from state["restaurant_metadata"]
└─ Returns: Complete restaurant objects to frontend
```

**MongoDB returns restaurant documents. Python calculates distance and open status. GPT-4 gets simplified JSON. State stores everything for later use.**
