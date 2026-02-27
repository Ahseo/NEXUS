# NEXUS Testing Strategy

## Overview

NEXUS uses a layered test pyramid with 5 tiers. All tests live under `backend/tests/` and run with pytest. HTTP mocking uses `respx` for async httpx clients. The target is 367+ tests passing, 0 pyright errors, and a clean frontend build.

## Test Pyramid

### 1. Unit Tests (`tests/unit/`)

Lowest level, no external dependencies. Cover pure logic and data models.

| File | Focus | Count |
|------|-------|-------|
| `test_models.py` | Pydantic model validation, enum values, field defaults | 36 |
| `test_scoring.py` | ScoringEngine: topic match, speaker match, type preference, price penalty, weighted formula | 30 |
| `test_deduplication.py` | URL normalization, fuzzy title matching, cross-source dedup | 11 |
| `test_preference_engine.py` | Feedback learning, weight adjustment, accept/reject signals, threshold updates | 26 |
| `test_tool_definitions.py` | Tool schema validation, required fields, all 12 tools registered | 18 |
| `test_routers.py` | FastAPI endpoint responses, status codes, request/response shapes | 18 |
| `test_config.py` | Settings loading, NexusMode enum, environment variable parsing | 6 |
| `test_websocket_manager.py` | Connect/disconnect, broadcast, per-user messaging | 13 |
| `test_message_generator.py` | Tone selection, template rendering, channel-specific formatting | 7 |
| `test_profile_richness.py` | Weighted completeness scoring, gap identification | 5 |
| `test_target_matching.py` | Fuzzy name matching (fuzz.ratio), score boosting, multi-target scenarios | 6 |

### 2. Contract Tests (`tests/contract/`)

Verify integration client behavior against mocked HTTP responses using `respx`. Each client has its own test file that validates request construction and response parsing.

| File | Client | Count |
|------|--------|-------|
| `test_tavily_client.py` | TavilyClient: search, domain filtering, time_range, error handling | 8 |
| `test_yutori_client.py` | YutoriClient: browsing_create, scouting_create, task status | 10 |
| `test_neo4j_client.py` | Neo4jClient: execute_query, execute_write, merge_event/person/company/topic | 13 |
| `test_reka_client.py` | RekaClient: analyze, compare, conversation_hooks extraction | 9 |

### 3. Agent Tests (`tests/agents/`)

Test each specialized agent's logic with mocked integration clients.

| File | Agent | Count |
|------|-------|-------|
| `test_discovery_agent.py` | Query building, Tavily search orchestration, dedup pipeline, scout setup | 16 |
| `test_analyze_agent.py` | Entity extraction, scoring integration, Neo4j graph population | 6 |
| `test_action_agent.py` | Decision matrix (auto_apply/suggest/skip), apply with retry, rate limiting | 11 |
| `test_connect_agent.py` | Attendee scraping, deep research loop, social resolution, target matching, connection ranking | 15 |

### 4. Orchestrator Tests (`tests/orchestrator/`)

Test the NexusAgent orchestrator's control logic.

| File | Focus | Count |
|------|-------|-------|
| `test_routing_rules.py` | Tool dispatch mapping, unknown tool handling, all 12 tools routable | 19 |
| `test_state_transitions.py` | Conversation history growth, trim_history at 100, cycle continuation, pause/resume | 39 |
| `test_safety_modes.py` | dry_run blocking, replay blocking, canary rate limits, live passthrough | 24 |

### 5. E2E Tests (`tests/e2e/`)

Full pipeline tests that exercise multiple agents and services together.

| File | Scenario | Count |
|------|----------|-------|
| `test_full_cycle_replay.py` | Discovery -> Analyze -> Action -> Connect full cycle with mocked APIs | 4 |
| `test_feedback_cycle.py` | User feedback -> preference update -> scoring adjustment -> re-ranking | 8 |
| `test_target_flow.py` | Add target person -> discovery finds event -> fuzzy match -> score boost -> message draft | 8 |

## Quality Metrics

| Metric | Target | Gate |
|--------|--------|------|
| Tests passing | 367+ | CI blocks on any failure |
| pyright errors | 0 | CI blocks on type errors |
| Frontend build | Clean | `npm run build` must succeed |
| Contract coverage | All 4 sponsor clients | Each has dedicated test file |
| Agent coverage | All 4 agents + orchestrator | Each has dedicated test file |

## Running Tests

```bash
cd backend
python -m pytest tests/ -v                     # all tests
python -m pytest tests/unit/ -v                 # unit only
python -m pytest tests/contract/ -v             # contract only
python -m pytest tests/agents/ -v               # agent tests
python -m pytest tests/orchestrator/ -v         # orchestrator tests
python -m pytest tests/e2e/ -v                  # end-to-end
pyright                                          # type checking
```

## Key Testing Patterns

- **respx** for HTTP mocking: contract tests mock httpx responses at the transport level
- **pytest fixtures** in `conftest.py`: shared `test_user_profile` and `sample_raw_event`
- **Dataclass agents**: Discovery, Action, Connect agents use `@dataclass` for easy test construction with injected mock clients
- **No real API calls**: all external services are mocked in every test tier
