from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class RuleResult:
    status: str
    summary: str
    details: List[str] = field(default_factory=list)
    received: str = ""
    expected: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseRule(ABC):
    @property
    @abstractmethod
    def rule_id(self) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def check(self, model) -> RuleResult: ...

    def render_html_row(self, result: RuleResult) -> str:
        st = "Пройдено" if result.status == "pass" else "Ошибка проверки" if result.status == "error" else "Не пройдено"
        return (
            f'<div class="rule-row status-{result.status}">'
            f'<span class="rule-name">{self.name}</span> '
            f'<span class="rule-summary">{result.summary}</span>'
            f'</div>'
        )

    def render_html_full(self, result: RuleResult) -> str:
        st = "Пройдено" if result.status == "pass" else "Ошибка выполнения" if result.status == "error" else "Не пройдено"
        h = (
            f'<div class="full-rule-block status-{result.status}">'
            f'<h3>{self.name}</h3>'
            f'<p>{self.description}</p>'
            f'<p>Статус: {st}</p>'
        )
        if result.received:
            h += f'<div class="rule-detail"><strong>Полученные данные:</strong> {result.received}</div>'
        if result.expected:
            h += f'<div class="rule-detail"><strong>Ожидаемый результат:</strong> {result.expected}</div>'
        if result.details:
            h += '<div class="rule-details"><strong>Нарушения:</strong><ul>'
            for d in result.details:
                h += f'<li>{d}</li>'
            h += '</ul></div>'
        h += '</div>'
        return h