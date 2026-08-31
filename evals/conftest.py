"""
conftest.py — Fixtures and configuration for LLM Evaluation suite in Losna CLI.
"""

import os
import json
import pytest
from pathlib import Path
from src.agent import config

DATASETS_DIR = Path(__file__).parent / "datasets"

def load_dataset(filename: str):
    """Loads a JSON dataset from the datasets directory."""
    path = DATASETS_DIR / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def tool_routing_data():
    return load_dataset("tool_routing.json")

@pytest.fixture(scope="session")
def memory_compaction_data():
    return load_dataset("memory_compaction.json")

@pytest.fixture(scope="session")
def security_audit_data():
    return load_dataset("security_audit.json")

@pytest.fixture(scope="session")
def readonly_safety_data():
    return load_dataset("readonly_safety.json")

@pytest.fixture(scope="session")
def openrouter_judge_model():
    """
    Returns an instance of OpenRouterJudgeLLM for DeepEval metrics if deepeval is available.
    """
    try:
        try:
            from deepeval.models import DeepEvalBaseLLM  # type: ignore
        except ImportError:
            from deepeval.models.base_model import DeepEvalBaseLLM  # type: ignore

        from openrouter import OpenRouter

        class OpenRouterJudgeLLM(DeepEvalBaseLLM):
            def __init__(self, model="anthropic/claude-3.5-sonnet", api_key=None):
                self.model_name = model
                self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
                self.client = OpenRouter(api_key=self.api_key) if self.api_key else None
                super().__init__(model_name=model)

            def load_model(self):
                return self.client

            def generate(self, prompt: str) -> str:
                if not self.client:
                    return "MOCK_JUDGE_EVAL_SCORE: 1.0"
                try:
                    response = self.client.chat.send(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.0
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    return f"Judge LLM Error: {e}"

            async def a_generate(self, prompt: str) -> str:
                return self.generate(prompt)

            def get_model_name(self):
                return self.model_name

        return OpenRouterJudgeLLM()
    except (ImportError, Exception):
        return None
