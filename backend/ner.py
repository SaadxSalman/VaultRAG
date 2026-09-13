"""Optional local NER adapter. It is disabled unless a local model is explicitly configured."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NERMatch:
    kind: str
    start: int
    end: int
    value: str


class LocalNER:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._pipeline: Any = None

    def _load(self) -> None:
        if self._pipeline is not None:
            return
        try:
            from transformers import pipeline
        except ImportError as error:
            raise RuntimeError("Transformers is required for local NER") from error
        self._pipeline = pipeline("token-classification", model=self.model_name, tokenizer=self.model_name, aggregation_strategy="simple", local_files_only=True)

    def detect(self, text: str) -> list[NERMatch]:
        self._load()
        return [NERMatch(kind=str(item["entity_group"]).upper(), start=int(item["start"]), end=int(item["end"]), value=str(item["word"])) for item in self._pipeline(text)]
