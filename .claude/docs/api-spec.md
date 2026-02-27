# NEXUS API Specification

## REST Endpoints

### Event Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/events` | List events (with filters: status, date range, score) |
| `GET` | `/api/events/:id` | Event detail |
| `POST` | `/api/events/:id/accept` | Accept event recommendation |
| `POST` | `/api/events/:id/reject` | Reject with reason |
| `POST` | `/api/events/:id/apply` | Manually trigger apply (via Yutori Browsing API) |
| `GET` | `/api/events/:id/people` | People at this event |
| `POST` | `/api/events/:id/rate` | Post-event rating (1-5) |

### People Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/people` | List discovered people |
| `GET` | `/api/people/:id` | Person detail + research summary |
| `GET` | `/api/people/:id/graph` | Person's graph connections (Neo4j) |
| `POST` | `/api/people/:id/mark` | Mark as "want to meet" or "not interested" |

### Target People Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/targets` | List target people |
| `POST` | `/api/targets` | Add target person |
| `PUT` | `/api/targets/:id` | Update target (priority, reason) |
| `DELETE` | `/api/targets/:id` | Remove target |
| `GET` | `/api/targets/:id/matches` | Events where this person was found |

### Message Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/messages` | List draft/sent messages |
| `GET` | `/api/messages/:id` | Message detail |
| `POST` | `/api/messages/:id/approve` | Approve and send |
| `POST` | `/api/messages/:id/edit` | Edit then send |
| `POST` | `/api/messages/:id/reject` | Reject message |

### Profile Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/profile` | Get user profile |
| `PUT` | `/api/profile` | Update profile |
| `GET` | `/api/profile/preferences` | Get learned preferences |
| `PUT` | `/api/profile/preferences` | Override preferences |

### Feedback Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/feedback` | Submit any feedback signal |
| `GET` | `/api/feedback/stats` | Feedback analytics |

### Graph Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/graph/network` | Full network graph data (Neo4j) |
| `GET` | `/api/graph/suggestions` | Graph-based suggestions |

### Agent Control Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/agent/status` | Agent health/status |
| `POST` | `/api/agent/pause` | Pause all agents |
| `POST` | `/api/agent/resume` | Resume agents |
| `POST` | `/api/agent/run-now` | Force discovery cycle |

## Webhook Endpoints (Internal)

| Method | Path | Source | Description |
|--------|------|--------|-------------|
| `POST` | `/webhooks/yutori/new-event` | Yutori Scouting API | New event discovered by continuous monitoring |
| `POST` | `/webhooks/yutori/apply-result` | Yutori Browsing API | Application/RSVP result callback |
| `POST` | `/webhooks/google/calendar` | Google Calendar | Calendar sync webhook |

## WebSocket Events

Connection: `ws://localhost:8000/ws`

### Server → Client Events

```typescript
interface WSEvents {
  // Event lifecycle
  "event:discovered": { event: Event };
  "event:analyzed": { event: Event; score: number };
  "event:applied": { event: Event; result: string };
  "event:scheduled": { event: Event; calendar_id: string };

  // People
  "person:discovered": { person: Person; event: Event };

  // Messages
  "message:drafted": { message: ColdMessage };
  "message:sent": { message: ColdMessage };

  // Agent
  "agent:status": { agent: string; status: string };

  // Targets
  "target:found": { target: TargetPerson; event: Event; person: Person };
  "target:updated": { target: TargetPerson };
}
```

Events are pushed in real-time as the agent pipeline processes new data, enabling the frontend to update without polling.
