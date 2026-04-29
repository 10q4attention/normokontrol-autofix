"""
Правило 06: Оглавление.
Проверяет: наличие заголовка «Оглавление», форматирование текста содержания,
ПРОПИСНЫЕ заголовки в содержании.
"""

from .base_rule import BaseRule, RuleResult


class TOCRule(BaseRule):
    @property
    def rule_id(self): return "toc"
    @property
    def name(self): return "Оглавление"
    @property
    def description(self): return "Проверка оформления оглавления (раздел 6)"

    MAIN_IN_TOC = [
        'ВВЕДЕНИЕ', 'ЗАКЛЮЧЕНИЕ', 'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ',
        'ПРИЛОЖЕНИЯ', 'ТЕОРЕТИЧЕСКИЙ РАЗДЕЛ', 'ПРАКТИЧЕСКИЙ РАЗДЕЛ', 'ТЕХНОЛОГИЧЕСКИЙ РАЗДЕЛ'
    ]

    def check(self, model):
        errors = []

        # 6.1 Найти заголовок «Оглавление»
        toc_heading = None
        for h in model.headings:
            if h['heading_level'] == 1 and h['text'].upper() in ('ОГЛАВЛЕНИЕ', 'СОДЕРЖАНИЕ'):
                toc_heading = h
                break

        if not toc_heading:
            return RuleResult(
                status='fail',
                summary='Заголовок «Оглавление» не найден',
                details=['Добавьте раздел «ОГЛАВЛЕНИЕ» со стилем «Заголовок 1»'],
                expected="Заголовок первого уровня «ОГЛАВЛЕНИЕ»"
            )

        if toc_heading['text'].upper() == 'СОДЕРЖАНИЕ':
            errors.append("Заголовок должен быть «ОГЛАВЛЕНИЕ», а не «СОДЕРЖАНИЕ»")

        # Границы оглавления
        toc_start = toc_heading['index']
        toc_end = None
        for h in model.headings:
            if h['heading_level'] == 1 and h['index'] > toc_start:
                toc_end = h['index']
                break
        if toc_end is None:
            toc_end = model.elements[-1]['index'] if model.elements else toc_start + 1

        # Строки оглавления
        toc_lines = []
        for e in model.elements:
            if toc_start < e['index'] < toc_end and e['text']:
                toc_lines.append(e)

        if not toc_lines:
            errors.append("Оглавление пусто. Добавьте автоматическое содержание.")

        # 6.3 Отсутствие отступа первой строки
        for line in toc_lines:
            indent = line.get('first_line_indent')
            if indent is not None and abs(indent) > 0.1:
                errors.append(
                    f"Отступ первой строки: '{line['text'][:50]}'. "
                    f"Отступ должен быть удалён (0 см)."
                )

        # 6.4 ПРОПИСНЫЕ заголовки в содержании
        for line in toc_lines:
            text = line['text']
            for main_section in self.MAIN_IN_TOC:
                if main_section in text.upper():
                    idx = text.upper().find(main_section)
                    actual = text[idx:idx+len(main_section)]
                    if actual != actual.upper():
                        errors.append(
                            f"Заголовок '{actual}' в содержании должен быть ПРОПИСНЫМИ буквами."
                        )
                    break

        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений в оглавлении: {len(errors)}',
                details=errors,
                received=f"Строк в оглавлении: {len(toc_lines)}",
                expected="Основной текст без отступа, ПРОПИСНЫЕ заголовки"
            )

        return RuleResult(
            status='pass',
            summary=f'Оглавление оформлено правильно ({len(toc_lines)} строк)',
            received=f"Строк: {len(toc_lines)}"
        )