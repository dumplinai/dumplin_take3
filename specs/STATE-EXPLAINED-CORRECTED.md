# STATE - THE COMPLETE EXPLANATION

## WHAT IS STATE?

**State is a Python dictionary** that carries all data through the conversation flow.

Think of it as a **shared data container** that gets passed through the system.

```python
Location: backend/app/services/chatbot_service.py:218-235

state = {
    "input": "Find pizza places",
    "latitude": 40.7128,
    "longitude": -74.0060,
    # ... more data
}
```

---

## STATE LIFECYCLE - STEP BY STEP

### STEP 1: STATE IS CREATED
**Location:** `backend/app/services/chatbot_service.py:218-235`
**Who:** ChatbotService (Python code)

```python
# Python code creates state dictionary:
state = {
    # FROM FRONTEND:
    "input": "Find pizza places",
    "history": [...],
    "latitude": 40.7128,
    "longitude": -74.0060,
    "city_data": {"name": "New York", ...},
    "weather_data": {...},
    "user_id": "user_123",
    "restaurant_id": None,
    "favorite_ids": ["id1", "id2"],
    "exclude_place_ids": ["id3", "id4"],
    "exclude_fav_ids": ["id5", "id6"],

    # ADDED BY BACKEND:
    "search_latitude": 40.7589,      # Calculated
    "search_longitude": -73.9851,    # Calculated
    "restaurant_metadata": {},       # Empty, for later
    "restaurants": None,
    "execution_time_ms": None,
    "structured_response": None
}
```

**State now exists and contains:**
- Everything frontend sent
- Backend calculations (search coordinates)
- Empty placeholders for results

---

### STEP 2: STATE GOES TO FOODAGENT
**Location:** `backend/app/agents/food_agent.py:94`
**Who:** Python code (FoodAgent.process method)

```python
def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
```

**FoodAgent receives the entire state dictionary.**

---

### STEP 3: PYTHON CODE READS FROM STATE
**Location:** `backend/app/agents/food_agent.py:98-118`
**Who:** Python code (NOT GPT-4)

```python
# PYTHON CODE extracts values from state:
input_message = state.get("input")              # "Find pizza places"
history = state.get("history")                  # [...]
latitude = state.get("latitude")                # 40.7128
longitude = state.get("longitude")              # -74.0060
search_latitude = state.get("search_latitude")  # 40.7589
search_longitude = state.get("search_longitude")# -73.9851
weather_data = state.get("weather_data")        # {...}
city_data = state.get("city_data")              # {...}
restaurant_id = state.get("restaurant_id")      # None
user_id = state.get("user_id")                  # "user_123"
exclude_place_ids = state.get("exclude_place_ids")  # ["id3", "id4"]
exclude_fav_ids = state.get("exclude_fav_ids")      # ["id5", "id6"]
```

**These are simple Python dictionary reads.**
**State is NOT modified yet.**

---

### STEP 4: PYTHON CODE CALCULATES NEW VALUES
**Location:** `backend/app/agents/food_agent.py:127-157`
**Who:** Python code using libraries (NOT GPT-4)

```python
# PYTHON CODE calculates timezone:
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime

tf = TimezoneFinder()
timezone_str = tf.timezone_at(lat=search_latitude, lng=search_longitude)
# Result: "America/New_York"

local_tz = pytz.timezone(timezone_str)
local_time_obj = datetime.now(local_tz)

# PYTHON CODE formats day:
day_of_week = local_time_obj.strftime("%A")
# Result: "Monday"

# PYTHON CODE formats time:
current_time_24h = local_time_obj.strftime("%H:%M")
# Result: "18:30"

current_time = local_time_obj.strftime("%I:%M %p")
# Result: "06:30 PM"
```

**These are LOCAL VARIABLES in the Python code.**
**They are NOT added to state.**
**GPT-4 does NOT do this calculation.**

---

### STEP 5: PYTHON CODE EXTRACTS CITY NAME
**Location:** `backend/app/agents/food_agent.py:148-152`
**Who:** Python code (NOT GPT-4)

```python
# PYTHON CODE extracts from city_data:
city_name = None
if city_data and city_data.get("name"):
    city_name = city_data.get("name")
# Result: "New York"
```

**This is a LOCAL VARIABLE.**
**NOT added to state.**

---

### STEP 6: PYTHON CODE CREATES TOOL
**Location:** `backend/app/agents/food_agent.py:176-190`
**Who:** Python code (NOT GPT-4)

```python
# PYTHON CODE calls factory function:
from app.tools.restaurant_search import create_search_restaurants_tool

search_restaurants = create_search_restaurants_tool(
    # FROM FOODAGENT ITSELF (services):
    self.vector_search,        # MongoDB service
    self.places_service,       # Places service

    # FROM STATE:
    search_latitude,           # 40.7589 (state["search_latitude"])
    search_longitude,          # -73.9851 (state["search_longitude"])
    latitude,                  # 40.7128 (state["latitude"])
    longitude,                 # -74.0060 (state["longitude"])
    restaurant_id,             # None (state["restaurant_id"])

    # CALCULATED BY PYTHON CODE (local variables):
    day_of_week,               # "Monday"
    current_time_24h,          # "18:30"

    # PASSED THROUGH:
    state,                     # Entire state dict
    city_name,                 # "New York" (extracted by Python)
    exclude_place_ids,         # ["id3", "id4"] (from state)
    False                      # should_exclude (hardcoded)
)
```

**Tool is now created with:**
- Services from FoodAgent
- Values from state
- Calculated values (day, time)
- Reference to entire state

**GPT-4 does NOT create this tool.**
**Python code creates it.**

---

### STEP 7: PYTHON CODE GIVES TOOL TO GPT-4
**Location:** `backend/app/agents/food_agent.py:224-407`
**Who:** Python code calls GPT-4

```python
# PYTHON CODE creates list of tools:
tools = [search_restaurants, get_restaurant_details]

# PYTHON CODE creates LangChain agent with GPT-4:
from langchain.agents import create_react_agent

agent = create_react_agent(
    llm=self.llm,              # GPT-4 model
    tools=tools,               # Tools we created
    prompt=system_message      # Instructions
)

# PYTHON CODE invokes GPT-4:
agent_response = agent.invoke({
    "messages": messages
})
```

**Now GPT-4 gets involved.**
**GPT-4 receives:**
- User message: "Find pizza places"
- Available tools: [search_restaurants, ...]
- System instructions

---

### STEP 8: GPT-4 DECIDES TO CALL TOOL
**Who:** GPT-4 (the LLM)

```
GPT-4 reads: "Find pizza places"

GPT-4 thinks:
"User wants to find pizza restaurants. I should call the
search_restaurants tool with search_text='pizza restaurants'"

GPT-4 generates tool call:
{
    "tool": "search_restaurants",
    "arguments": {
        "search_text": "pizza restaurants",
        "radius_km": 35.0,
        "nearby_only": true
    }
}
```

**This is AI decision-making.**
**GPT-4 decided:**
- To call the tool
- What search_text should be
- What radius to use
- Whether to search nearby only

---

### STEP 9: PYTHON CODE EXECUTES TOOL
**Location:** `backend/app/tools/restaurant_search.py:93-299`
**Who:** Python code (tool function)

**For detailed breakdown of what MongoDB returns, see:** `specs/MONGODB-SEARCH-RESULTS.md`

```python
# LangChain (Python framework) executes:
def search_restaurants(
    search_text: str,
    limit: int = 5,
    radius_km: float = 35.0,
    nearby_only: bool = True,
    # ... other params
) -> str:
```

**Tool uses VALUES FROM THREE SOURCES:**

1. **From initialization (baked in earlier):**
   - search_latitude: 40.7589 (from state)
   - user_latitude: 40.7128 (from state)
   - current_day: "Monday" (calculated by Python)
   - current_time_24h: "18:30" (calculated by Python)
   - city_name: "New York" (extracted by Python)
   - exclude_place_ids: ["id3", "id4"] (from state)

2. **From GPT-4 invocation:**
   - search_text: "pizza restaurants" (GPT-4 decided)
   - radius_km: 35.0 (GPT-4 decided)
   - nearby_only: True (GPT-4 decided)

3. **From FoodAgent:**
   - vector_search service
   - places_service

**Tool executes MongoDB search and returns JSON.**

---

### STEP 10: TOOL WRITES TO STATE
**Location:** `backend/app/tools/restaurant_search.py:208-216`
**Who:** Python code (tool writes to state)

```python
# TOOL writes results to state:
if state is not None:
    if "restaurant_metadata" not in state:
        state["restaurant_metadata"] = {}

    for result in results:
        place_id = str(result.get("place_id"))
        if place_id:
            state["restaurant_metadata"][place_id] = result
```

**STATE IS MODIFIED:**

```python
state["restaurant_metadata"] = {
    "place_123": {
        "title": "Joe's Pizza",
        "location": {...},
        "openingHours": [...],
        "posts": [...]
    },
    "place_456": {...},
    # ... 3 more
}
```

**This is the first time state is modified!**

---

### STEP 11: GPT-4 RECEIVES TOOL RESULTS

```
Tool returns to GPT-4:
[
    {"place_id": "place_123", "title": "Joe's Pizza", ...},
    {"place_id": "place_456", "title": "Prince St Pizza", ...},
    ...
]

GPT-4 formats response:
"Here are 5 amazing pizza places nearby! 🍕"

[Restaurant cards in JSON format]

"Let me know if you want more options!"
```

**GPT-4 creates user-facing message.**

---

### STEP 12: PYTHON CODE PROCESSES GPT-4 RESPONSE
**Location:** `backend/app/agents/food_agent.py:449-633`
**Who:** Python code (NOT GPT-4)

```python
# PYTHON CODE parses GPT-4's response:
response_text = agent_response["messages"][-1].content

# PYTHON CODE extracts place_ids from response:
place_ids = extract_place_ids(response_text)
# ["place_123", "place_456", ...]

# PYTHON CODE fetches full data from state:
restaurants = []
for place_id in place_ids:
    metadata = state["restaurant_metadata"].get(place_id)
    if metadata:
        restaurants.append(metadata)

# PYTHON CODE updates state:
state["restaurants"] = restaurants
state["structured_response"] = structured_parts
state["history"].append(ai_message)
```

**STATE IS MODIFIED AGAIN:**

```python
state["restaurants"] = [
    {full restaurant 1 object},
    {full restaurant 2 object},
    # ... 5 total
]

state["structured_response"] = [
    {"message_type": "reply_start", "text": "Here are 5..."},
    {"message_type": "reply_end", "text": "Let me know..."}
]

state["history"] = [
    {"role": "user", "content": "Find pizza places"},
    {"role": "assistant", "content": "Here are 5..."}
]
```

---

### STEP 13: STATE RETURNS TO CHATBOTSERVICE
**Location:** `backend/app/services/chatbot_service.py:240-260`
**Who:** Python code

```python
# FoodAgent returns modified state:
result = self.food_agent.process(state)

# result is the state dictionary with all additions:
{
    "input": "Find pizza places",         # Original
    "latitude": 40.7128,                  # Original
    "search_latitude": 40.7589,           # Original
    "exclude_place_ids": ["id3", "id4"],  # Original
    "restaurant_metadata": {...},         # ADDED by tool
    "restaurants": [5 objects],           # ADDED by FoodAgent
    "structured_response": [...],         # ADDED by FoodAgent
    "history": [updated]                  # UPDATED by FoodAgent
}
```

---

## WHAT COMES FROM WHERE - COMPLETE BREAKDOWN

### 1. FROM FRONTEND → STATE

```python
# Frontend sends via HTTP POST:
{
  "input": "Find pizza places",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "history": [...],
  "city_data": {"name": "New York", ...},
  "weather_data": {...},
  "user_id": "user_123",
  "restaurant_id": null,
  "favorite_ids": ["id1", "id2"],
  "exclude_place_ids": ["id3", "id4"],
  "exclude_fav_ids": ["id5", "id6"]
}

# Backend copies to state:
state["input"] = "Find pizza places"
state["latitude"] = 40.7128
state["longitude"] = -74.0060
# ... all copied directly
```

**These go INTO state.**

---

### 2. CALCULATED BY CHATBOTSERVICE → STATE

```python
# File: backend/app/services/chatbot_service.py:213-215

# PYTHON CODE calculates search coordinates:
search_latitude, search_longitude = determine_search_coordinates(
    latitude, longitude, city_data, city_boundaries_service
)

# PYTHON CODE adds to state:
state["search_latitude"] = 40.7589
state["search_longitude"] = -73.9851
state["restaurant_metadata"] = {}  # Empty
```

**These go INTO state.**

---

### 3. CALCULATED BY FOODAGENT - NOT IN STATE

```python
# File: backend/app/agents/food_agent.py:135-157

# PYTHON CODE calculates (LOCAL VARIABLES):
day_of_week = "Monday"              # ← NOT in state
current_time_24h = "18:30"          # ← NOT in state
current_time = "06:30 PM"           # ← NOT in state
city_name = "New York"              # ← NOT in state
context_info = "..."                # ← NOT in state
```

**These are LOCAL VARIABLES in Python code.**
**NOT added to state.**
**Passed directly to tool creation.**

---

### 4. OWNED BY FOODAGENT - NOT IN STATE

```python
# File: backend/app/agents/food_agent.py:48-50

class FoodAgent:
    def __init__(self):
        self.vector_search = VectorSearch()      # ← NOT in state
        self.places_service = PlacesService()    # ← NOT in state
        self.llm = ChatOpenAI(model="gpt-4")     # ← NOT in state
```

**These are PROPERTIES of the FoodAgent class.**
**NOT in state.**
**Services used by tool.**

---

### 5. WRITTEN BY TOOL → STATE

```python
# File: backend/app/tools/restaurant_search.py:208-216

# TOOL writes to state:
state["restaurant_metadata"]["place_123"] = {
    "title": "Joe's Pizza",
    "location": {...},
    # ... full data
}
```

**This is ADDED to state.**

---

### 6. WRITTEN BY FOODAGENT → STATE

```python
# File: backend/app/agents/food_agent.py:600-633

# PYTHON CODE updates state:
state["restaurants"] = [5 restaurant objects]
state["structured_response"] = [cards]
state["history"] = [updated messages]
state["execution_time_ms"] = 1234
```

**These are ADDED/UPDATED in state.**

---

## STATE BEFORE AND AFTER

### STATE AT START (ChatbotService creates it):

```python
{
    # From frontend:
    "input": "Find pizza places",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "city_data": {...},
    "exclude_place_ids": ["id3", "id4"],

    # Added by backend:
    "search_latitude": 40.7589,
    "search_longitude": -73.9851,
    "restaurant_metadata": {},      # EMPTY
    "restaurants": None,            # NULL
    "structured_response": None,    # NULL
    "history": [old messages]
}
```

### STATE AT END (FoodAgent returns it):

```python
{
    # Unchanged:
    "input": "Find pizza places",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "city_data": {...},
    "exclude_place_ids": ["id3", "id4"],
    "search_latitude": 40.7589,
    "search_longitude": -73.9851,

    # Modified by tool:
    "restaurant_metadata": {        # FILLED
        "place_123": {...},
        "place_456": {...}
    },

    # Added by FoodAgent:
    "restaurants": [5 objects],     # FILLED
    "structured_response": [...],   # FILLED
    "history": [updated messages],  # UPDATED
    "execution_time_ms": 1234       # ADDED
}
```

---

## WHO DOES WHAT - CLEAR BREAKDOWN

### CHATBOTSERVICE (Python code)
```
Creates state
Adds search coordinates to state
Passes state to FoodAgent
Receives modified state back
```

### FOODAGENT (Python code)
```
Receives state
Reads from state
Calculates day/time (local variables, not in state)
Extracts city name (local variable, not in state)
Creates tool with values from state + calculations
Calls GPT-4 with tool
Processes GPT-4 response
Writes to state (restaurants, structured_response, history)
Returns modified state
```

### GPT-4 (AI)
```
Receives user message
Receives available tools
Decides to call search_restaurants
Decides parameters (search_text, radius_km, etc.)
Formats user-facing response
Does NOT touch state directly
```

### TOOL (Python function)
```
Receives parameters from GPT-4
Uses initialization values (from state + FoodAgent)
Executes MongoDB search
Writes results to state["restaurant_metadata"]
Returns results to GPT-4
```

---

## KEY POINTS

1. **State is a dictionary** - passed through the system

2. **State contains:**
   - Frontend data
   - Backend calculations (search coords)
   - Tool results (restaurant_metadata)
   - Final results (restaurants, structured_response)

3. **State does NOT contain:**
   - Services (vector_search, places_service)
   - Local calculations (day_of_week, current_time_24h)
   - Python classes/objects

4. **Two separate "agents":**
   - FoodAgent = Python code class
   - AI Agent = GPT-4

5. **FoodAgent Python code calculates:**
   - day_of_week using TimezoneFinder
   - current_time_24h using pytz
   - city_name by extracting from state

6. **GPT-4 decides:**
   - Which tool to call
   - What parameters to pass
   - How to format response

7. **State gets modified by:**
   - Tool (writes restaurant_metadata)
   - FoodAgent (writes restaurants, structured_response, history)

8. **State flows:**
   Frontend → ChatbotService creates → FoodAgent modifies → Returns to ChatbotService → Sent to Frontend

---

## VISUAL SUMMARY

```
┌─────────────────────────────────────────────────────────┐
│                       STATE                              │
│  (Python dictionary that flows through system)           │
│                                                           │
│  Created by: ChatbotService                              │
│  Modified by: Tool, FoodAgent                            │
│  Returned to: ChatbotService                             │
│                                                           │
│  Contains:                                               │
│  ✓ Frontend data (input, lat/lng, city, excludes)      │
│  ✓ Backend calculations (search coords)                 │
│  ✓ Tool results (restaurant_metadata)                   │
│  ✓ Final results (restaurants, structured_response)     │
│                                                           │
│  Does NOT contain:                                       │
│  ✗ Services (vector_search, places_service)             │
│  ✗ Local variables (day_of_week, current_time)         │
│  ✗ Python classes/objects                               │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│                   FOODAGENT                              │
│  (Python class - backend code)                           │
│                                                           │
│  Has:                                                    │
│  ✓ Services (vector_search, places_service)             │
│  ✓ GPT-4 model (self.llm)                               │
│                                                           │
│  Does:                                                   │
│  ✓ Reads from state                                     │
│  ✓ Calculates day/time (local variables)                │
│  ✓ Creates tool                                          │
│  ✓ Calls GPT-4                                           │
│  ✓ Writes to state                                       │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│                     GPT-4                                │
│  (AI language model - external)                          │
│                                                           │
│  Does:                                                   │
│  ✓ Reads user message                                   │
│  ✓ Decides to call tool                                 │
│  ✓ Decides parameters                                    │
│  ✓ Formats response                                      │
│                                                           │
│  Does NOT:                                               │
│  ✗ Calculate day/time                                   │
│  ✗ Access state directly                                │
│  ✗ Query database                                        │
└─────────────────────────────────────────────────────────┘
```

**State is the data. FoodAgent is the processor. GPT-4 is the decision-maker.**
