"""Extract trajectory dataset from LangSmith traces.

Pulls all root runs from the deep-research-agent project, extracts
input → tool trajectory → final output, and creates a LangSmith dataset.

Usage:
    uv run python extract_dataset.py
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from langsmith import Client

DATASET_NAME = "deep-research-agent-trajectories"
PROJECT_NAME = "deep-research-agent"

# Tool names worth capturing in the trajectory (filter out middleware noise)
TRAJECTORY_TOOLS = {"write_todos", "write_file", "edit_file", "task", "tavily_search", "think_tool"}


def extract_trajectory(client: Client, trace_id: str) -> list[dict]:
    """Extract ordered tool calls from a trace."""
    steps = list(client.list_runs(
        project_name=PROJECT_NAME,
        trace_id=trace_id,
        run_type="tool",
    ))
    steps.sort(key=lambda r: r.start_time or 0)

    trajectory = []
    for step in steps:
        name = step.name
        if name not in TRAJECTORY_TOOLS:
            continue

        raw_input = (step.inputs or {}).get("input", {})
        tool_input = raw_input if isinstance(raw_input, dict) else {"value": raw_input}

        raw_output = step.outputs or {}
        tool_output = raw_output.get("output", raw_output)

        trajectory.append({
            "tool": name,
            "input": tool_input,
            "output": str(tool_output)[:2000],  # cap for dataset storage
        })

    return trajectory


def get_final_response(run) -> str:
    """Extract the last AI text response from a run's output messages."""
    messages = (run.outputs or {}).get("messages", [])
    for msg in reversed(messages):
        if msg.get("type") != "ai":
            continue
        content = msg.get("content", "")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item["text"].strip()
                    if text:
                        return text
        elif isinstance(content, str) and content.strip():
            return content.strip()
    return ""


def main() -> None:
    client = Client()

    # Fetch all successful root runs
    runs = list(client.list_runs(
        project_name=PROJECT_NAME,
        run_type="chain",
        is_root=True,
        filter='eq(status, "success")',
    ))
    print(f"Found {len(runs)} successful runs in '{PROJECT_NAME}'")

    # Build examples
    examples = []
    for run in runs:
        user_input = ""
        messages = (run.inputs or {}).get("messages", [])
        for msg in messages:
            role = msg.get("role", msg.get("type", ""))
            if role in ("human", "user"):
                user_input = msg.get("content", "")
                break

        if not user_input:
            continue

        trajectory = extract_trajectory(client, str(run.id))
        final_response = get_final_response(run)

        examples.append({
            "inputs": {"question": user_input},
            "outputs": {
                "trajectory": trajectory,
                "final_response": final_response,
            },
        })
        print(f"  Extracted: '{user_input[:60]}...' — {len(trajectory)} steps")

    if not examples:
        print("No examples to upload.")
        return

    # Create or update dataset in LangSmith
    existing = [d for d in client.list_datasets() if d.name == DATASET_NAME]
    if existing:
        dataset = existing[0]
        print(f"\nDataset '{DATASET_NAME}' already exists (id={dataset.id}), adding examples...")
    else:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Trajectory dataset for the deep research agent. Each example captures the user question, ordered tool call sequence, and final response.",
        )
        print(f"\nCreated dataset '{DATASET_NAME}' (id={dataset.id})")

    client.create_examples(
        dataset_id=dataset.id,
        inputs=[e["inputs"] for e in examples],
        outputs=[e["outputs"] for e in examples],
    )

    print(f"Uploaded {len(examples)} examples.")
    print(f"\nView at: https://smith.langchain.com/datasets/{dataset.id}")


if __name__ == "__main__":
    main()
