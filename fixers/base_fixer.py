from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class FixResult:
    fixer_id: str
    name: str
    changes: List[str] = field(default_factory=list)
    status: str = 'ok'  # 'ok' | 'skipped' | 'error'
    error: str = ''


class BaseFixer(ABC):
    @property
    @abstractmethod
    def fixer_id(self) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def fix(self, doc, model) -> FixResult: ...
