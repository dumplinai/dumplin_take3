# Restaurant Search Tool - Visual Breakdown

## THE TOOL

```
backend/app/tools/restaurant_search.py
```

This is a function that searches for restaurants. It gets called by an AI agent.

---

## SIMPLE EXAMPLE - WHAT HAPPENS

```
USER TYPES: "Find pizza places"
              ↓
AI CALLS TOOL: search_restaurants(search_text="pizza restaurants")
              ↓
TOOL RETURNS: [Joe's Pizza, Prince Street Pizza, ...]
              ↓
USER SEES: Restaurant cards in chat
```

---

## WHO TRIGGERS IT? (Step by Step)

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: USER                                                 │
│ ------------------------------------------------------------ │
│ Action: Types "Find pizza places" in Flutter app             │
│ Location: frontend/lib/views/screen/Chat/chat_screen.dart   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: FRONTEND CONTROLLER                                  │
│ ------------------------------------------------------------ │
│ Action: Collects all data and sends POST request            │
│ Location: frontend/lib/controllers/chat_controller.dart     │
│                                                              │
│ Sends:                                                       │
│   • input: "Find pizza places"                              │
│   • latitude: 40.7128  (from GPS)                           │
│   • longitude: -74.0060 (from GPS)                          │
│   • city_data: {name: "New York", ...}                      │
│   • exclude_place_ids: ["id1", "id2", ...]                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: API ENDPOINT                                         │
│ ------------------------------------------------------------ │
│ Action: Receives HTTP POST /chat                             │
│ Location: backend/app/api/chat.py                            │
│                                                              │
│ Does: Validates API key, converts to ChatInput model        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: CHATBOT SERVICE                                      │
│ ------------------------------------------------------------ │
│ Action: Creates "state" dictionary with all variables       │
│ Location: backend/app/services/chatbot_service.py           │
│                                                              │
│ state = {                                                    │
│   "input": "Find pizza places",                             │
│   "latitude": 40.7128,                                      │
│   "longitude": -74.0060,                                    │
│   "search_latitude": 40.7589,  ← calculated                │
│   "search_longitude": -73.9851, ← calculated               │
│   "city_data": {...},                                       │
│   "exclude_place_ids": ["id1", "id2"],                     │
│   ...                                                        │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: FOOD AGENT - CREATES THE TOOL                       │
│ ------------------------------------------------------------ │
│ Action: Builds search_restaurants tool with context         │
│ Location: backend/app/agents/food_agent.py:176-190          │
│                                                              │
│ # Extract from state:                                       │
│ search_lat = state["search_latitude"]  # 40.7589           │
│ user_lat = state["latitude"]           # 40.7128           │
│ city_name = state["city_data"]["name"] # "New York"        │
│                                                              │
│ # Calculate timezone:                                       │
│ current_day = "Monday"     ← from coordinates              │
│ current_time = "18:30"     ← from coordinates              │
│                                                              │
│ # CREATE TOOL:                                              │
│ search_restaurants = create_search_restaurants_tool(        │
│     vector_search,          ← service                      │
│     places_service,         ← service                      │
│     search_latitude,        ← 40.7589                      │
│     search_longitude,       ← -73.9851                     │
│     user_latitude,          ← 40.7128                      │
│     user_longitude,         ← -74.0060                     │
│     restaurant_id,          ← None                         │
│     current_day,            ← "Monday"                     │
│     current_time_24h,       ← "18:30"                      │
│     state,                  ← entire state dict            │
│     city_name,              ← "New York"                   │
│     exclude_place_ids,      ← ["id1", "id2"]              │
│     should_exclude          ← False                        │
│ )                                                            │
│                                                              │
│ Tool is now ready, but NOT called yet!                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: AI AGENT RECEIVES TOOL                               │
│ ------------------------------------------------------------ │
│ Action: GPT-4 gets the tool and user message                │
│ Location: backend/app/agents/food_agent.py:400-407          │
│                                                              │
│ AI has:                                                      │
│   • User message: "Find pizza places"                       │
│   • Tool: search_restaurants                                │
│   • History: previous conversation                          │
│                                                              │
│ AI thinks: "User wants pizza. I should call the tool."      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: AI CALLS THE TOOL                                    │
│ ------------------------------------------------------------ │
│ Action: AI decides parameters and invokes tool              │
│                                                              │
│ AI executes:                                                 │
│   search_restaurants(                                        │
│       search_text="pizza restaurants",  ← AI decides this   │
│       radius_km=35.0,                   ← AI decides this   │
│       nearby_only=True,                 ← AI decides this   │
│       specific_name_search=False,       ← AI decides this   │
│       should_exclude=False              ← AI decides this   │
│   )                                                          │
│                                                              │
│ NOW the tool actually runs!                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 8: TOOL EXECUTES                                        │
│ ------------------------------------------------------------ │
│ Action: Searches database and returns results               │
│ Location: backend/app/tools/restaurant_search.py:93-299     │
│                                                              │
│ Returns JSON to AI:                                          │
│ [                                                            │
│   {                                                          │
│     "place_id": "abc123",                                   │
│     "title": "Joe's Pizza",                                 │
│     "similarity_score": 0.89,                               │
│     "distance_km": 2.5,                                     │
│     "is_open": true,                                        │
│     "price_tier": 2                                         │
│   },                                                         │
│   ... 4 more restaurants                                    │
│ ]                                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 9: AI FORMATS RESPONSE                                  │
│ ------------------------------------------------------------ │
│ Action: AI creates user-friendly message                    │
│                                                              │
│ AI creates:                                                  │
│   "Here are 5 amazing pizza places nearby! 🍕"             │
│   [Restaurant Cards]                                         │
│   "Let me know if you want more options!"                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 10: USER SEES RESULTS                                   │
│ ------------------------------------------------------------ │
│ Action: Flutter app displays restaurant cards               │
│ Location: frontend/lib/views/screen/Chat/chat_screen.dart   │
└─────────────────────────────────────────────────────────────┘
```

---

## THE CRITICAL POINT

**WHO ACTUALLY TRIGGERS THE TOOL?**

```
NOT the code → THE AI MODEL (GPT-4)
```

The tool is created in Step 5, but not called until Step 7 when the AI decides to.

---

## TWO TYPES OF VARIABLES - VISUAL BREAKDOWN

### TYPE 1: INITIALIZATION VARIABLES
**Set when tool is CREATED (Step 5)**

```
┌─────────────────────────────────────────────────────────────┐
│ THESE ARE "BAKED IN" TO THE TOOL                             │
└─────────────────────────────────────────────────────────────┘

VARIABLE               WHERE IT COMES FROM               VALUE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
vector_search          FoodAgent service                 <service object>
places_service         FoodAgent service                 <service object>
search_latitude        Frontend GPS or city center       40.7589
search_longitude       Frontend GPS or city center       -73.9851
user_latitude          Frontend GPS                      40.7128
user_longitude         Frontend GPS                      -74.0060
restaurant_id          Frontend (usually None)           None
current_day            Calculated from coordinates       "Monday"
current_time_24h       Calculated from coordinates       "18:30"
state                  Full conversation state           {entire dict}
city_name              Frontend selected city            "New York"
exclude_place_ids      Frontend last 20 shown           ["id1", "id2", ...]
should_exclude         Hardcoded                         False
```

**THESE NEVER CHANGE DURING THE CONVERSATION**
Once the tool is created, these are locked in.

---

### TYPE 2: INVOCATION VARIABLES
**Set when tool is CALLED (Step 7)**

```
┌─────────────────────────────────────────────────────────────┐
│ THE AI DECIDES THESE EVERY TIME IT CALLS THE TOOL            │
└─────────────────────────────────────────────────────────────┘

VARIABLE               WHO SETS IT       EXAMPLE VALUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
search_text            AI                "pizza restaurants"
                                         "Italian food"
                                         "Casa Cruda"

limit                  AI (fixed at 5)   5

radius_km              AI                35.0 (default)
                                         50.0 (if "wider area")
                                         100.0 (if "more options")

nearby_only            AI                True (search nearby)
                                         False (search everywhere)

specific_name_search   AI                False (normal search)
                                         True (searching for "Casa Cruda")

price_tier_min         AI                None (any price)
                                         1 (cheapest only)

price_tier_max         AI                None (any price)
                                         2 (cheap/moderate only)

sort_by_price          AI                False (sort by relevance)
                                         True (sort by price)

should_exclude         AI                False (show all results)
                                         True (exclude previously shown)
```

**THE AI CAN SET DIFFERENT VALUES EACH TIME**

---

## VISUAL EXAMPLE - COMPLETE FLOW

```
┌──────────────────────────────────────────────────────────────────┐
│ USER SCENARIO: "Find cheap pizza"                                │
└──────────────────────────────────────────────────────────────────┘

STEP 1: Frontend Collects Data
┌────────────────────────────────┐
│ GPS Reading                     │
│ ─────────────────────────────── │
│ latitude: 40.7128              │
│ longitude: -74.0060            │
│                                 │
│ Selected City                   │
│ ─────────────────────────────── │
│ city_data: {                   │
│   name: "New York",            │
│   center: {...}                │
│ }                               │
│                                 │
│ Recent History                  │
│ ─────────────────────────────── │
│ exclude_place_ids: [           │
│   "id1", "id2", "id3"          │
│ ]                               │
└────────────────────────────────┘
              ↓
STEP 2: Backend Calculates Search Location
┌────────────────────────────────┐
│ determine_search_coordinates()  │
│ ─────────────────────────────── │
│ User is INSIDE New York bounds  │
│ → Use user GPS for search      │
│                                 │
│ search_latitude: 40.7128       │
│ search_longitude: -74.0060     │
└────────────────────────────────┘
              ↓
STEP 3: Backend Calculates Time
┌────────────────────────────────┐
│ TimezoneFinder                  │
│ ─────────────────────────────── │
│ Coordinates → Timezone          │
│ 40.7128, -74.0060 → EST         │
│                                 │
│ Current time in EST:            │
│ current_day: "Monday"          │
│ current_time_24h: "18:30"      │
└────────────────────────────────┘
              ↓
STEP 4: Tool Creation
┌────────────────────────────────────────────────────────┐
│ create_search_restaurants_tool(                        │
│     vector_search = <MongoDB service>,                │
│     places_service = <Places service>,                │
│     search_latitude = 40.7128,    ← from GPS          │
│     search_longitude = -74.0060,  ← from GPS          │
│     user_latitude = 40.7128,      ← from GPS          │
│     user_longitude = -74.0060,    ← from GPS          │
│     restaurant_id = None,         ← not asking for 1  │
│     current_day = "Monday",       ← calculated        │
│     current_time_24h = "18:30",   ← calculated        │
│     state = {full state},         ← everything        │
│     city_name = "New York",       ← from city_data    │
│     exclude_place_ids = ["id1", "id2", "id3"], ← last │
│     should_exclude = False        ← default           │
│ )                                                       │
│                                                         │
│ → Tool created with context "baked in"                 │
└────────────────────────────────────────────────────────┘
              ↓
STEP 5: AI Analyzes User Message
┌────────────────────────────────┐
│ AI reads: "Find cheap pizza"   │
│ ─────────────────────────────── │
│ AI thinks:                      │
│ • User wants: pizza            │
│ • User wants: cheap options    │
│ • Should call: search_restaurants │
│ • Should filter: by price      │
└────────────────────────────────┘
              ↓
STEP 6: AI Calls Tool
┌────────────────────────────────────────────────────────┐
│ search_restaurants(                                     │
│     search_text = "pizza restaurants",  ← AI decides   │
│     limit = 5,                          ← AI decides   │
│     radius_km = 35.0,                   ← AI decides   │
│     nearby_only = True,                 ← AI decides   │
│     specific_name_search = False,       ← AI decides   │
│     price_tier_min = 1,                 ← AI decides ✓ │
│     price_tier_max = 2,                 ← AI decides ✓ │
│     sort_by_price = True,               ← AI decides ✓ │
│     should_exclude = False              ← AI decides   │
│ )                                                       │
└────────────────────────────────────────────────────────┘
              ↓
STEP 7: Tool Executes
┌────────────────────────────────────────────────────────┐
│ Tool uses:                                              │
│                                                         │
│ FROM INITIALIZATION (baked in):                         │
│ • search_latitude: 40.7128    (where to search)        │
│ • search_longitude: -74.0060                           │
│ • user_latitude: 40.7128      (for distance calc)      │
│ • user_longitude: -74.0060                             │
│ • current_day: "Monday"       (for open status)        │
│ • current_time_24h: "18:30"   (for open status)        │
│ • city_name: "New York"       (filter to city)         │
│ • exclude_place_ids: [...]    (prevent repeats)        │
│                                                         │
│ FROM INVOCATION (AI set):                               │
│ • search_text: "pizza restaurants"                     │
│ • radius_km: 35.0                                      │
│ • price_tier_min: 1           ← filters cheap         │
│ • price_tier_max: 2           ← filters cheap         │
│ • sort_by_price: True         ← sorts by price        │
│                                                         │
│ Calls: vector_search.search_by_text()                  │
│   → OpenAI embedding for "pizza restaurants"           │
│   → MongoDB Vector Search                              │
│   → Filter: city = "New York"                          │
│   → Filter: price_tier >= 1 AND <= 2   ← cheap only!  │
│   → Filter: location within 35km radius                │
│   → Filter: exclude ["id1", "id2", "id3"]             │
│   → Sort: by price_tier ascending      ← cheapest first! │
│   → Limit: 5 results                                   │
└────────────────────────────────────────────────────────┘
              ↓
STEP 8: Process Results
┌────────────────────────────────────────────────────────┐
│ For each restaurant found:                              │
│                                                         │
│ Restaurant 1: "Dollar Pizza"                           │
│ ├─ Calculate distance from user                        │
│ │  haversine(40.7128, -74.0060, 40.7200, -74.0100)    │
│ │  = 0.8 km                                            │
│ ├─ Format: "0.8 km (3-5 min)"                         │
│ ├─ Check if open                                       │
│ │  Monday 18:30 in restaurant's timezone               │
│ │  Hours: 11:00-23:00 → OPEN ✓                        │
│ ├─ Price tier: 1 (cheapest)                           │
│ └─ Similarity score: 0.91                              │
│                                                         │
│ Restaurant 2: "Joe's Pizza"                            │
│ ├─ Distance: 2.5 km → "2.5 km (10-15 min)"           │
│ ├─ Open: Monday 18:30 → OPEN ✓                        │
│ ├─ Price tier: 2 (moderate)                           │
│ └─ Similarity score: 0.89                              │
│                                                         │
│ ... 3 more restaurants                                 │
│                                                         │
│ Sort by:                                                │
│ 1. is_open (True first)                                │
│ 2. price_tier (1, then 2, then 3...)  ← sorted!       │
└────────────────────────────────────────────────────────┘
              ↓
STEP 9: Return to AI
┌────────────────────────────────────────────────────────┐
│ [                                                       │
│   {                                                     │
│     "place_id": "place_123",                           │
│     "title": "Dollar Pizza",                           │
│     "similarity_score": 0.91,                          │
│     "distance_km": 0.8,                                │
│     "distance_string": "0.8 km (3-5 min)",            │
│     "is_open": true,                                   │
│     "price_tier": 1                                    │
│   },                                                    │
│   {                                                     │
│     "place_id": "place_456",                           │
│     "title": "Joe's Pizza",                            │
│     "similarity_score": 0.89,                          │
│     "distance_km": 2.5,                                │
│     "distance_string": "2.5 km (10-15 min)",          │
│     "is_open": true,                                   │
│     "price_tier": 2                                    │
│   },                                                    │
│   ... 3 more                                           │
│ ]                                                       │
└────────────────────────────────────────────────────────┘
              ↓
STEP 10: AI Formats Response
┌────────────────────────────────────────────────────────┐
│ AI creates response:                                    │
│                                                         │
│ "Here are 5 cheap pizza spots near you! 🍕💰"         │
│                                                         │
│ [Restaurant Card: Dollar Pizza]                        │
│ [Restaurant Card: Joe's Pizza]                         │
│ [Restaurant Card: ...]                                 │
│                                                         │
│ "All under $10! Want more options?"                    │
└────────────────────────────────────────────────────────┘
```

---

## WHERE VARIABLES COME FROM - VISUAL MAP

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ User Device                                             │ │
│ │                                                         │ │
│ │ GPS Sensor → latitude, longitude                       │ │
│ │ User Selection → city_data                             │ │
│ │ Chat History → exclude_place_ids (last 20 shown)       │ │
│ │ User Input → "Find cheap pizza"                        │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP POST
┌─────────────────────────────────────────────────────────────┐
│                         BACKEND                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ChatbotService                                          │ │
│ │                                                         │ │
│ │ Receives all frontend data                             │ │
│ │ ├─ determine_search_coordinates()                      │ │
│ │ │  → search_latitude, search_longitude                │ │
│ │ └─ Creates state dict                                  │ │
│ └─────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ FoodAgent                                               │ │
│ │                                                         │ │
│ │ Receives state                                          │ │
│ │ ├─ TimezoneFinder(search_latitude, search_longitude)   │ │
│ │ │  → current_day, current_time_24h                    │ │
│ │ ├─ Extracts city_name from city_data                   │ │
│ │ └─ Creates tool with all context                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ AI Agent (GPT-4)                                        │ │
│ │                                                         │ │
│ │ Receives:                                               │ │
│ │ • Tool: search_restaurants                             │ │
│ │ • User message: "Find cheap pizza"                     │ │
│ │                                                         │ │
│ │ Decides:                                                │ │
│ │ • search_text = "pizza restaurants"                    │ │
│ │ • price_tier_min = 1                                   │ │
│ │ • price_tier_max = 2                                   │ │
│ │ • sort_by_price = True                                 │ │
│ │                                                         │ │
│ │ Calls tool with these parameters                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ search_restaurants Tool                                 │ │
│ │                                                         │ │
│ │ Uses BOTH sets of variables:                           │ │
│ │ • From initialization (context)                        │ │
│ │ • From AI invocation (search params)                   │ │
│ │                                                         │ │
│ │ Calls vector_search.search_by_text()                   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ MongoDB Vector Search                                   │ │
│ │                                                         │ │
│ │ • Generate embedding for "pizza restaurants"           │ │
│ │ • Find similar restaurants in database                 │ │
│ │ • Apply filters (city, price, radius, exclusions)      │ │
│ │ • Return 5 results                                     │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## VARIABLE LIFECYCLE - VISUAL TIMELINE

```
TIME →
─────────────────────────────────────────────────────────────

T1: User Types Message
│
│   "Find cheap pizza"
│
└─→ CREATES: input = "Find cheap pizza"

T2: Frontend Gets GPS
│
│   Device GPS reading
│
└─→ CREATES: latitude = 40.7128, longitude = -74.0060

T3: Frontend Sends Request
│
│   POST /chat
│
└─→ SENDS: input, latitude, longitude, city_data, exclude_place_ids

T4: Backend Determines Search Location
│
│   determine_search_coordinates()
│
└─→ CREATES: search_latitude, search_longitude

T5: Backend Calculates Timezone
│
│   TimezoneFinder(search_latitude, search_longitude)
│
└─→ CREATES: current_day = "Monday", current_time_24h = "18:30"

T6: Tool Creation
│
│   create_search_restaurants_tool(...)
│
└─→ LOCKS IN: All initialization variables
             (search_lat, user_lat, current_day, city_name, etc.)

T7: AI Analyzes Message
│
│   GPT-4 reads: "Find cheap pizza"
│   GPT-4 decides parameters
│
└─→ CREATES: search_text = "pizza restaurants"
             price_tier_min = 1
             price_tier_max = 2
             sort_by_price = True

T8: Tool Execution
│
│   search_restaurants(search_text="pizza", price_tier_min=1, ...)
│
└─→ USES: Both initialization vars (locked in at T6)
          AND invocation vars (created at T7)

T9: Vector Search
│
│   MongoDB query with all filters
│
└─→ RETURNS: 5 restaurants

T10: Process Results
│
│   Calculate distance, open status
│
└─→ USES: user_latitude, user_longitude (from T2)
          current_day, current_time_24h (from T5)

T11: Return to AI
│
│   JSON array of 5 restaurants
│
└─→ AI formats response

T12: User Sees Results
│
│   Restaurant cards in chat
│
└─→ END
```

---

## CRITICAL INSIGHT - THE TWO-STAGE INJECTION

```
┌─────────────────────────────────────────────────────────────┐
│                      STAGE 1: TOOL CREATION                  │
│                                                              │
│  When: FoodAgent processes request                          │
│  File: backend/app/agents/food_agent.py:176-190             │
│                                                              │
│  Variables injected:                                         │
│  ├─ Services (vector_search, places_service)                │
│  ├─ Location context (search_lat/lng, user_lat/lng)         │
│  ├─ Time context (current_day, current_time_24h)            │
│  ├─ City context (city_name)                                │
│  ├─ Exclusion list (exclude_place_ids)                      │
│  └─ Full state                                              │
│                                                              │
│  These are "BAKED IN" - Cannot change during conversation   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    STAGE 2: TOOL INVOCATION                  │
│                                                              │
│  When: AI decides to call the tool                          │
│  File: AI agent runtime (GPT-4 decision)                    │
│                                                              │
│  Variables set by AI:                                        │
│  ├─ search_text (what to search for)                        │
│  ├─ radius_km (how far to search)                           │
│  ├─ nearby_only (search nearby or everywhere)               │
│  ├─ specific_name_search (searching for specific name?)     │
│  ├─ price_tier_min/max (price filtering)                    │
│  ├─ sort_by_price (how to sort)                             │
│  └─ should_exclude (exclude previously shown?)              │
│                                                              │
│  These CAN CHANGE - AI decides fresh each invocation        │
└─────────────────────────────────────────────────────────────┘
```

---

## FILE REFERENCES

**Where variables are SET:**

```
latitude, longitude
  ↓ frontend/lib/utils/location_service.dart
  ↓ Device GPS sensor

city_data
  ↓ frontend/lib/controllers/cities_controller.dart
  ↓ User selection

exclude_place_ids
  ↓ frontend/lib/controllers/chat_controller.dart
  ↓ Tracked from chat history

search_latitude, search_longitude
  ↓ backend/app/services/chatbot_service.py:213-215
  ↓ determine_search_coordinates()

current_day, current_time_24h
  ↓ backend/app/agents/food_agent.py:135-157
  ↓ TimezoneFinder + pytz

Tool with initialization vars
  ↓ backend/app/agents/food_agent.py:176-190
  ↓ create_search_restaurants_tool()

AI sets invocation vars
  ↓ backend/app/agents/food_agent.py:400-407
  ↓ agent.invoke() - GPT-4 runtime

Vector search executes
  ↓ backend/app/tools/restaurant_search.py:148-185
  ↓ vector_search.search_by_text()

MongoDB query
  ↓ backend/app/utils/vector_search.py
  ↓ collection.aggregate()
```

---

## SUMMARY - THE COMPLETE PICTURE

```
┌──────────────┐
│ USER DEVICE  │  GPS → latitude, longitude
│              │  Selection → city_data
└──────┬───────┘  History → exclude_place_ids
       │
       ↓ POST /chat
┌──────────────┐
│ BACKEND API  │  Receives all frontend data
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ CHATBOT SVC  │  Calculates → search_latitude, search_longitude
└──────┬───────┘  Creates state dict
       │
       ↓
┌──────────────┐
│ FOOD AGENT   │  Calculates → current_day, current_time_24h
└──────┬───────┘  Extracts → city_name
       │          CREATES TOOL ← with all context
       │
       ↓
┌──────────────┐
│ AI AGENT     │  Receives tool + user message
│  (GPT-4)     │  DECIDES → search_text, price_tier_min, etc.
└──────┬───────┘  CALLS TOOL
       │
       ↓
┌──────────────┐
│ TOOL         │  Uses initialization vars (context)
│ search_      │  Uses invocation vars (AI decisions)
│ restaurants  │  Calls vector_search
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ MONGO DB     │  Vector search + filters
└──────┬───────┘  Returns 5 restaurants
       │
       ↓
┌──────────────┐
│ BACK TO AI   │  AI formats response
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ USER SEES    │  Restaurant cards
└──────────────┘
```

**The key: Variables flow from USER → BACKEND → TOOL (initialization) → AI → TOOL (invocation) → DATABASE → RESULTS**
