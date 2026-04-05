"""Auto-evaluator for the deep research agent.

Runs the agent against the trajectory dataset and scores:
  - tool_recall:     fraction of reference tool types present in actual run
  - tool_precision:  fraction of actual tool types that appear in reference
  - tool_f1:         harmonic mean of recall and precision
  - sequence_sim:    longest-common-subsequence similarity on ordered tool sequences

Usage:
    uv run python evaluate_agent.py
"""

from __future__ import annotations

import uuid
from difflib import SequenceMatcher

from dotenv import load_dotenv

load_dotenv()

from langsmith.evaluation import evaluate

from agent import agent

DATASET_NAME = "deep-research-agent-trajectories"
TRAJECTORY_TOOLS = {"write_todos", "write_file", "edit_file", "task", "tavily_search", "think_tool"}


# ---------------------------------------------------------------------------
# Target function
# ---------------------------------------------------------------------------

def run_agent(inputs: dict) -> dict:
    """Run the research agent and capture the tool trajectory."""
    question = inputs["question"]
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
    )

    # Extract tool call sequence from output messages
    trajectory: list[dict] = []
    for msg in result.get("messages", []):
        msg_type = msg.__class__.__name__ if not isinstance(msg, dict) else msg.get("type", "")
        if "AI" in msg_type or msg_type == "ai":
            content = msg.content if hasattr(msg, "content") else msg.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        name = item.get("name", "")
                        if name in TRAJECTORY_TOOLS:
                            trajectory.append({
                                "tool": name,
                                "input": item.get("input", {}),
                            })

    final_response = ""
    for msg in reversed(result.get("messages", [])):
        msg_type = msg.__class__.__name__ if not isinstance(msg, dict) else msg.get("type", "")
        if "AI" in msg_type or msg_type == "ai":
            content = msg.content if hasattr(msg, "content") else msg.get("content", "")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text" and item["text"].strip():
                        final_response = item["text"].strip()
                        break
            elif isinstance(content, str) and content.strip():
                final_response = content.strip()
            if final_response:
                break

    return {"trajectory": trajectory, "final_response": final_response}


# ---------------------------------------------------------------------------
# Evaluators
# ---------------------------------------------------------------------------

def _tool_names(trajectory: list[dict]) -> list[str]:
    return [step["tool"] for step in trajectory if "tool" in step]


def tool_recall(outputs: dict, reference_outputs: dict) -> dict:
    """Fraction of reference tool types that appear in the actual run."""
    actual = set(_tool_names(outputs.get("trajectory", [])))
    reference = set(_tool_names(reference_outputs.get("trajectory", [])))
    if not reference:
        return {"key": "tool_recall", "score": 1.0}
    score = len(actual & reference) / len(reference)
    return {"key": "tool_recall", "score": round(score, 3)}


def tool_precision(outputs: dict, reference_outputs: dict) -> dict:
    """Fraction of actual tool types that appear in the reference."""
    actual = set(_tool_names(outputs.get("trajectory", [])))
    reference = set(_tool_names(reference_outputs.get("trajectory", [])))
    if not actual:
        return {"key": "tool_precision", "score": 0.0}
    score = len(actual & reference) / len(actual)
    return {"key": "tool_precision", "score": round(score, 3)}


def tool_f1(outputs: dict, reference_outputs: dict) -> dict:
    """F1 score combining recall and precision over tool types."""
    actual = set(_tool_names(outputs.get("trajectory", [])))
    reference = set(_tool_names(reference_outputs.get("trajectory", [])))
    if not actual and not reference:
        return {"key": "tool_f1", "score": 1.0}
    if not actual or not reference:
        return {"key": "tool_f1", "score": 0.0}
    p = len(actual & reference) / len(actual)
    r = len(actual & reference) / len(reference)
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"key": "tool_f1", "score": round(f1, 3)}


def sequence_similarity(outputs: dict, reference_outputs: dict) -> dict:
    """LCS-based similarity of ordered tool-call sequences."""
    actual = _tool_names(outputs.get("trajectory", []))
    reference = _tool_names(reference_outputs.get("trajectory", []))
    if not actual and not reference:
        return {"key": "sequence_similarity", "score": 1.0}
    if not actual or not reference:
        return {"key": "sequence_similarity", "score": 0.0}
    score = SequenceMatcher(None, reference, actual).ratio()
    return {"key": "sequence_similarity", "score": round(score, 3)}


# ---------------------------------------------------------------------------
# Run evaluation
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    results = evaluate(
        run_agent,
        data=DATASET_NAME,
        evaluators=[tool_recall, tool_precision, tool_f1, sequence_similarity],
        experiment_prefix="tool-call-match",
        max_concurrency=1,  # sequential to avoid rate limits
    )

    print("\n=== Results ===")
    for r in results:
        ex_input = r["example"].inputs.get("question", "")[:55]
        eval_results = r["evaluation_results"]["results"]
        scores = {res.key: res.score for res in eval_results}
        print(f"\n  Q: {ex_input}...")
        for k, v in scores.items():
            print(f"    {k:25s} {v:.3f}")
