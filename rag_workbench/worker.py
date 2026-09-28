"""Placeholder local worker entry point; future jobs use the same platform contracts."""

from rag_workbench.runtime import demo_runtime

if __name__ == "__main__":
    print(f"local worker ready with {len(demo_runtime().evidence)} evidence elements")
