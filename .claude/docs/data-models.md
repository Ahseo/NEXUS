# NEXUS Data Models

## Pydantic Model Catalog

### Event Models

```python
class EventSource(str, Enum):
    EVENTBRITE = "eventbrite"
    LUMA = "luma"
    MEETUP = "meetup"
    PARTIFUL = "partiful"
    TWITTER = "twitter"
    OTHER = "other"

class EventType(str, Enum):
    CONFERENCE = "conference"
    MEETUP = "meetup"
    DINNER = "dinner"
    WORKSHOP = "workshop"
    HAPPY_HOUR = "happy_hour"
    DEMO_DAY = "demo_day"

class EventStatus(str, Enum):
    DISCOVERED = "discovered"
    ANALYZED = "analyzed"
    SUGGESTED = "suggested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    APPLIED = "applied"
    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    ATTENDED = "attended"
    SKIPPED = "skipped"

class ApplicationResult(BaseModel):
    status: Literal["applied", "waitlisted", "failed", "payment_required"]
    confirmation_id: str | None
    yutori_task_id: str

class Event(BaseModel):
    id: str
    url: str
    title: str
    description: str
    source: EventSource
    event_type: EventType
    date: datetime
    end_date: datetime | None
    location: str
    capacity: int | None
    price: float | None
    speakers: list[Person]
    topics: list[str]
    target_audience: str
    application_required: bool
    relevance_score: int  # 0-100
    status: EventStatus
    rejection_reason: str | None
    application_result: ApplicationResult | None
    calendar_event_id: str | None
    user_rating: int | None  # 1-5
    created_at: datetime
    updated_at: datetime
```

### Person Models

```python
class Person(BaseModel):
    id: str
    name: str
    title: str | None
    company: str | None
    linkedin: str | None
    twitter: str | None
    connection_score: int  # how valuable is this connection
    mutual_connections: list[Person]
    shared_topics: list[str]
    research_summary: str | None  # from Tavily deep research
```

### Message Models

```python
class MessageChannel(str, Enum):
    TWITTER_DM = "twitter_dm"
    LINKEDIN = "linkedin"
    EMAIL = "email"

class MessageStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    EDITED = "edited"
    SENT = "sent"
    REJECTED = "rejected"

class ColdMessage(BaseModel):
    id: str
    recipient: Person
    event: Event
    channel: MessageChannel
    content: str
    status: MessageStatus
    user_edits: str | None
    sent_at: datetime | None
    response_received: bool | None
```

### Target Person Models

```python
class TargetPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TargetStatus(str, Enum):
    SEARCHING = "searching"
    FOUND_EVENT = "found_event"
    MESSAGED = "messaged"
    CONNECTED = "connected"

class TargetPerson(BaseModel):
    id: str
    name: str
    company: str | None
    role: str | None
    reason: str
    priority: TargetPriority
    status: TargetStatus
    added_at: datetime
    matched_events: list[Event] | None
```

### Feedback Models

```python
class FeedbackAction(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    EDIT = "edit"
    RATE = "rate"
    SKIP = "skip"

class Feedback(BaseModel):
    id: str
    user_id: str
    event_id: str | None
    person_id: str | None
    message_id: str | None
    action: FeedbackAction
    reason: str | None
    free_text: str | None
    rating: int | None
    created_at: datetime
```

### User Profile Models

```python
class MessageTone(str, Enum):
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"

class UserProfile(BaseModel):
    id: str
    name: str
    role: str
    company: str
    product: str
    interests: list[str]
    goals: list[str]
    preferred_event_types: list[str]
    max_events_per_week: int
    max_event_spend: float
    preferred_days: list[str]
    preferred_times: list[str]
    message_tone: MessageTone
    auto_apply_threshold: int  # score 80+ = auto-apply
    suggest_threshold: int     # score 50+ = suggest
    auto_schedule_threshold: int  # score 85+ = auto-calendar
```

## SQLAlchemy Schema

Tables map to the Pydantic models above. Key tables:

- `users` - User profiles and preferences
- `events` - Discovered events with status tracking
- `people` - Discovered people
- `messages` - Draft/sent cold messages
- `targets` - Target people to find
- `feedback` - All user feedback signals

Relationships are managed in PostgreSQL for transactional data and in Neo4j for graph queries.

## Neo4j Schema

### Node Types

```cypher
(:User {id, name, role, company, product, interests[], goals[]})
(:Event {url, title, date, location, type, score, status})
(:Person {name, title, company, linkedin, twitter})
(:Company {name, industry, stage, size})
(:Topic {name, category})
(:Role {name})  // e.g., "investor", "founder", "engineer"
```

### Relationship Types

```cypher
(:User)-[:INTERESTED_IN {weight}]->(:Topic)
(:User)-[:WANTS_TO_MEET]->(:Role)
(:User)-[:WANTS_TO_MEET_PERSON {reason, priority, added_at}]->(:Person)
(:User)-[:TARGETS]->(:Company)
(:User)-[:ATTENDED {feedback, rating}]->(:Event)
(:User)-[:REJECTED {reason, timestamp}]->(:Event)
(:User)-[:KNOWS {strength}]->(:Person)
(:Event)-[:HAS_SPEAKER]->(:Person)
(:Event)-[:TAGGED]->(:Topic)
(:Person)-[:WORKS_AT]->(:Company)
(:Person)-[:EXPERT_IN]->(:Topic)
(:Person)-[:CONNECTED_TO {source}]->(:Person)
(:Company)-[:IN_INDUSTRY]->(:Topic)
```

### Key Graph Queries

- "Find people who share my interests AND attend the same event AND work at companies I'm targeting"
- "What topics connect me to this person through mutual connections?"
- "Which events have the highest density of people I want to meet?"

## TypeScript-Python Type Mapping

| TypeScript | Python (Pydantic) |
|-----------|-------------------|
| `string` | `str` |
| `number` | `int` or `float` |
| `boolean` | `bool` |
| `DateTime` | `datetime` |
| `string[]` | `list[str]` |
| `T \| null` | `T \| None` |
| `"a" \| "b" \| "c"` | `Literal["a", "b", "c"]` or `str Enum` |
| `interface` | `BaseModel` |
| `T[]` | `list[T]` |
