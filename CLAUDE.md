# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                          # Install dependencies
uv run python main.py "question" # Run the agent CLI
uv run python main.py            # Interactive mode
langgraph dev                    # Start LangGraph Studio server (uses langgraph.json)
uv run python evaluate_agent.py  # Run LangSmith evaluation
```

Linting (no test suite):
```bash
uv run ruff check .
uv run ruff format .
```

## Architecture

This is a **deep research agent** built on the `deepagents` framework (LangChain/LangGraph). The entry point is `agent.py`, which exports an `agent` object that `langgraph.json` registers as the `research` graph.

### Agent structure

`create_deep_agent()` in `agent.py` wires together:

1. **Orchestrator** — receives the user's question, creates a todo plan, delegates research tasks to sub-agents via `task()`, synthesizes findings, and writes `/final_report.md` and `/research_request.md` to the virtual filesystem
2. **`research-agent` sub-agent** — receives a single research topic, runs 2–5 `tavily_search` + `think_tool` cycles, and returns structured findings with citations
3. **`arxiv` skill** — loaded via `SkillsMiddleware`; the agent reads `skills/arxiv/SKILL.md` on demand when academic paper searches are relevant, then calls `arxiv_search`

### Backend / filesystem

A `CompositeBackend` splits the virtual filesystem:
- `/skills/` → `FilesystemBackend(root_dir="skills")` — skill SKILL.md files read from disk
- Everything else → `FilesystemBackend(root_dir="reports", virtual_mode=True)` — report files written here (e.g., `/final_report.md` → `reports/final_report.md`)

### Skills

Skills live in `skills/<name>/` and require:
- `SKILL.md` — YAML frontmatter (`name`, `description`) + instructions; loaded by `SkillsMiddleware` into the system prompt
- `tools.py` — LangChain `@tool`-decorated functions; imported directly in `agent.py` and passed to `tools=`

The skill name in `SKILL.md` frontmatter must match the directory name exactly.

### Tools

| Tool | Module | Purpose |
|------|--------|---------|
| `tavily_search` | `research_agent/tools.py` | Tavily URL discovery + full-page fetch via httpx → markdown |
| `think_tool` | `research_agent/tools.py` | Strategic reflection between searches |
| `arxiv_search` | `skills/arxiv/tools.py` | arXiv paper search via `arxiv` Python client |

`InjectedToolArg` is used for `max_results` and `topic` parameters that should not be exposed to the LLM.

### Prompts

All prompt templates are in `research_agent/prompts.py`. Three instruction sets are composed at startup:
- `RESEARCH_WORKFLOW_INSTRUCTIONS` — orchestrator workflow (plan → delegate → synthesize → write report)
- `SUBAGENT_DELEGATION_INSTRUCTIONS` — parallelization rules (max 3 concurrent, max 3 rounds)
- `RESEARCHER_INSTRUCTIONS` — sub-agent search budget (2–3 searches simple, max 5 complex)

### Evaluation

`evaluate_agent.py` runs the agent against a LangSmith dataset (`deep-research-agent-trajectories`) and scores tool recall/precision/F1 and sequence similarity. `extract_dataset.py` extracts trajectory data from LangSmith traces to build the dataset.

## Environment variables

Required: `ANTHROPIC_API_KEY`, `TAVILY_API_KEY`
Optional: `LANGSMITH_API_KEY` (for tracing/evaluation), `GOOGLE_API_KEY` (for Gemini)
