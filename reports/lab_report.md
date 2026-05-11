# Day 08 Lab Report

## 1. Team / student

- Name: Đỗ Hải Nam
- Repo/commit: ref: refs/heads/main
- Date: 2026-05-11

## 2. Architecture

The workflow implements a support-ticket agent using LangGraph with a hub-and-spoke architecture centered around a `classify` node.
- **Nodes**: `intake` (normalization/PII), `classify` (keyword-based routing), `tool` (execution), `evaluate` (gate), `clarify` (missing info), `risky_action` (preparation), `approval` (HITL), `retry` (increment attempt), `dead_letter` (escalation), `answer` (result formatting), and `finalize` (cleanup).
- **Edges**: Conditional edges after `classify`, `evaluate`, `approval`, and `retry` control the state machine flow.
- **Reducers**: `Annotated[list, add]` is used for `messages`, `tool_results`, `errors`, and `events` to maintain a full audit trail.

## 3. State schema

Important fields used in the `AgentState` TypedDict:

| Field | Reducer | Why |
|---|---|---|
| messages | add | audit conversation history |
| tool_results | add | track all tool execution attempts |
| errors | add | log failures for retry logic |
| events | add | audit trail of node execution for grading |
| route | (overwrite) | current routing decision |
| attempt | (overwrite) | track bounded retry count |

## 4. Scenario results

Summary: 7 scenarios, 100.0% success rate.

| Scenario | Expected route | Actual route | Success | Retries | Interrupts |
|---|---|---|---:|---:|---:|
| S01_simple | simple | simple | ✓ | 0 | 0 |
| S02_tool | tool | tool | ✓ | 0 | 0 |
| S03_missing | missing_info | missing_info | ✓ | 0 | 0 |
| S04_risky | risky | risky | ✓ | 0 | 1 |
| S05_error | error | error | ✓ | 3 | 0 |
| S06_delete | risky | risky | ✓ | 0 | 1 |
| S07_dead_letter | error | error | ✓ | 1 | 0 |

## 5. Failure analysis

1. **Retry or tool failure**:
   - Handled by `evaluate_node` which detects error keywords in tool results.
   - Routes to `retry` node to increment count, then back to `tool`.
   - Bounded by `max_attempts` check in `route_after_retry` to prevent infinite loops.

2. **Risky action without approval**:
   - Handled by `risky_action` node which prepares the payload but does **not** execute it.
   - Flow **must** pass through `approval` node.
   - `route_after_approval` ensures that if `approved=False`, the flow is redirected to `clarify` instead of the `tool` node.

## 6. Persistence / recovery evidence

- **Checkpointer**: Implemented SQLite persistence using `SqliteSaver`.
- **Thread ID**: Every run uses a unique `thread_id` derived from the scenario ID (e.g., `thread-S01_simple`).
- **Crash-resume**: Verified that state is stored in `checkpoints.db`, allowing runs to survive process restarts.
- **Evidence**: `metrics.resume_success=True`.

## 7. Extension work

- **SQLite Persistence**: Fully implemented extension track using `langgraph-checkpoint-sqlite` and `sqlite3.connect`.
- **Advanced Intake**: Implemented PII redaction for Emails and Phone numbers, plus normalization and metadata extraction in `intake_node`.

## 8. Improvement plan

If I had one more day, I would:
1. Replace keyword-based routing with an LLM-based classifier for better semantic understanding.
2. Build a Streamlit dashboard to provide a real human-in-the-loop UI for the `approval` node.
3. Implement "Parallel Fan-out" to run multiple diagnostic tools concurrently when an error is detected.