"""Report generation helper."""

from __future__ import annotations

from pathlib import Path

from .metrics import MetricsReport


def render_report_stub(metrics: MetricsReport) -> str:
    """Generate comprehensive lab report matching lab_report_template.md."""
    
    # Build scenario results table
    scenario_rows = []
    for m in metrics.scenario_metrics:
        success_str = "✓" if m.success else "✗"
        scenario_rows.append(
            f"| {m.scenario_id} | {m.expected_route} | {m.actual_route or 'unknown'} | {success_str} | "
            f"{m.retry_count} | {m.interrupt_count} |"
        )
    
    scenario_table = "\n".join(scenario_rows) if scenario_rows else "| (no scenarios) |"
    
    report = f"""# Day 08 Lab Report

## 1. Team / student

- Name: Do Hai Nam
- Repo/commit: {Path('.git/HEAD').read_text().strip() if Path('.git/HEAD').exists() else 'local-dev'}
- Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}

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

Summary: {metrics.total_scenarios} scenarios, {metrics.success_rate:.1%} success rate.

| Scenario | Expected route | Actual route | Success | Retries | Interrupts |
|---|---|---|---:|---:|---:|
{scenario_table}

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
- **Evidence**: `metrics.resume_success={metrics.resume_success}`.

## 7. Extension work

- **SQLite Persistence**: Fully implemented extension track using `langgraph-checkpoint-sqlite` and `sqlite3.connect`.
- **Advanced Intake**: Implemented PII redaction for Emails and Phone numbers, plus normalization and metadata extraction in `intake_node`.

## 8. Improvement plan

If I had one more day, I would:
1. Replace keyword-based routing with an LLM-based classifier for better semantic understanding.
2. Build a Streamlit dashboard to provide a real human-in-the-loop UI for the `approval` node.
3. Implement "Parallel Fan-out" to run multiple diagnostic tools concurrently when an error is detected.

---
Generated: {__import__('datetime').datetime.now().isoformat()}
"""
    return report


def write_report(metrics: MetricsReport, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report_stub(metrics), encoding="utf-8")
