"""Generation ports: retrieval-only by default, Transformers/Unsloth by explicit opt-in."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GenerationResult:
    answer: str
    model: str
    mode: str


class LocalGenerator(Protocol):
    def generate(self, query: str, context: str) -> GenerationResult:
        """Generate from already-masked text only."""


class RetrievalOnlyGenerator:
    def generate(self, query: str, context: str) -> GenerationResult:
        return GenerationResult(
            answer="Local retrieval complete. Generation is disabled; review the evidence below.",
            model="none",
            mode="retrieval-only",
        )


class TransformersGenerator:
    """Lazy local Transformers adapter; model loading never occurs during import."""

    def __init__(self, model_name: str, max_new_tokens: int = 384):
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self._tokenizer = None
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as error:
            raise RuntimeError("Transformers is required for local generation") from error
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=True)
        self._model = AutoModelForCausalLM.from_pretrained(self.model_name, local_files_only=True, device_map="auto")

    def generate(self, query: str, context: str) -> GenerationResult:
        self._load()
        prompt = (
            "You are a careful local research assistant. Use only the evidence below. "
            "If the evidence is insufficient, say so. Do not invent facts.\n\n"
            f"EVIDENCE:\n{context}\n\nQUESTION:\n{query}\n\nANSWER:\n"
        )
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
        output = self._model.generate(**inputs, max_new_tokens=self.max_new_tokens, do_sample=False)
        answer = self._tokenizer.decode(output[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True).strip()
        return GenerationResult(answer=answer, model=self.model_name, mode="local-transformers")
