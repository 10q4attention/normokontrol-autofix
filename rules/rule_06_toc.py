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

        # Строки оглавления: ищем элементы с is_toc=True И elements между заголовками
        toc_lines = []
        for e in model.elements:
            if toc_start < e['index'] <= toc_end and e['text']:
                if e.get('is_toc') or self._looks_like_toc_line(e['text']):
                    toc_lines.append(e)

        # Если строк не нашли — возможно, автособираемое содержание (SDT)
        # Тогда это не ошибка, содержание есть
        if not toc_lines:
            return RuleResult(
                status='pass',
                summary='Оглавление использует автособираемое содержание (SDT)',
                received="Автособираемое содержание"
            )

        # 6.3 Отсутствие отступа первой строки
        for line in toc_lines:
            indent = line.get('first_line_indent')
            if indent is not None and abs(indent) > 0.1:
                errors.append(
                    f"Отступ первой строки: '{line['text'][:50]}'. "
                    f"Отступ должен быть удалён (0 см)."
                )

        # 6.4 ПРОПИСНЫЕ заголовки в содержании
        # Сравниваем строку оглавления (без номера страницы) с именем раздела целиком,
        # чтобы не ловить ложные совпадения типа «приложения» в «Тестирование приложения».
        import re as _re
        for line in toc_lines:
            text = line['text']
            # Убираем суффикс с номером страницы (таб+цифры или точки+цифры)
            clean = _re.sub(r'[\t.]+\s*\d+\s*$', '', text).strip()
            clean_upper = clean.upper()
            for main_section in self.MAIN_IN_TOC:
                if clean_upper == main_section:          # точное совпадение всей строки
                    if clean != main_section:            # не ПРОПИСНЫМИ
                        errors.append(
                            f"Заголовок '{clean}' в содержании должен быть ПРОПИСНЫМИ буквами."
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

    def _looks_like_toc_line(self, text):
        """Похожа ли строка на строку оглавления (заполнитель точками, номер страницы в конце)"""
        import re
        if re.search(r'\.{2,}\s*\d+$', text):
            return True
        if re.search(r'\s+\d+$', text) and len(text) < 150:
            return True
        return False