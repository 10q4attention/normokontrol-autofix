"""
Правило 14: Приложения.
Проверяет: заголовки, нумерацию, перечень, ссылки.
"""

import re
from .base_rule import BaseRule, RuleResult


class AppendicesRule(BaseRule):
    @property
    def rule_id(self): return "appendices"
    @property
    def name(self): return "Приложения"
    @property
    def description(self): return "Проверка оформления приложений (раздел 14)"

    FORBIDDEN = ['Ё', 'З', 'Й', 'О', 'Ч', 'Ь', 'Ы', 'Ъ']

    def check(self, model):
        errors = []

        # 14.1 Ищем раздел «ПРИЛОЖЕНИЯ» (заголовок 1 уровня)
        app_heading = None
        for h in model.headings:
            if h['heading_level'] == 1 and h['text'].upper() == 'ПРИЛОЖЕНИЯ':
                app_heading = h
                break

        if not app_heading:
            return RuleResult(
                status='pass',
                summary='Приложения не найдены (допустимо, если их нет)'
            )

        # Собираем приложения: заголовки 2 уровня «Приложение А», «Приложение Б» и т.д.
        appendices = []
        for h in model.headings:
            if h['heading_level'] == 2 and h['index'] > app_heading['index']:
                m = re.match(r'^Приложение\s+([А-ЯA-Z])\b', h['text'], re.I)
                if m:
                    appendices.append({'letter': m.group(1).upper(), 'heading': h})

        if not appendices:
            errors.append("Не найдены заголовки приложений (Приложение А, Приложение Б...)")

        # 14.3 Проверка букв
        valid_letters = [l for l in 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ' if l not in self.FORBIDDEN]
        found_letters = [a['letter'] for a in appendices]

        for a in appendices:
            letter = a['letter']
            if letter in self.FORBIDDEN:
                errors.append(
                    f"Приложение {letter}: буква '{letter}' не используется для приложений"
                )

        # Проверка порядка букв
        ordered = sorted(found_letters, key=lambda x: valid_letters.index(x) if x in valid_letters else 999)
        if found_letters != ordered:
            errors.append(
                f"Нарушен порядок приложений. Ожидается: {', '.join(ordered)}. "
                f"Фактически: {', '.join(found_letters)}"
            )

        # 14.4 Проверка разделов внутри приложений (Приложение А.3)
        for h in model.headings:
            if h['heading_level'] == 3:
                m = re.match(r'^Приложение\s+([А-ЯA-Z])\.(\d+)', h['text'], re.I)
                if m:
                    letter = m.group(1).upper()
                    # Проверяем, что такое приложение существует
                    if letter not in found_letters:
                        errors.append(
                            f"'{h['text'][:60]}': приложение {letter} не найдено среди заголовков"
                        )

        # 14.5 Проверка нумерации объектов в приложениях
        for cap in model.captions:
            if cap.get('is_continuation'):
                continue
            m = None
            if cap['caption_type'] == 'table':
                m = re.match(r'^Таблица\s+([А-ЯA-Z])\.(\d+)', cap['text'], re.I)
            elif cap['caption_type'] == 'figure':
                m = re.match(r'^Рис(?:унок|\.)\s+([А-ЯA-Z])\.(\d+)', cap['text'], re.I)
            elif cap['caption_type'] == 'listing':
                m = re.match(r'^Листинг\s+([А-ЯA-Z])\.(\d+)', cap['text'], re.I)

            if m:
                letter = m.group(1).upper()
                if letter not in found_letters:
                    errors.append(
                        f"'{cap['text'][:60]}': приложение {letter} не найдено"
                    )

        # 14.6 Ссылки на приложения в тексте
        for a in appendices:
            letter = a['letter']
            pattern = rf'\b[Пп]риложени(?:е|я|ю|ем|и|й|ям|ями|ях)\s+{letter}\b'
            if not re.search(pattern, model.body_text):
                errors.append(f"Нет ссылки на Приложение {letter}")

        # 14.7 Проверка форматирования заголовка приложения
        for a in appendices:
            h = a['heading']
            pv = h['text'][:50]

            # Должен быть стиль «Заголовок третьего уровня» (heading_level == 2 по структуре, но это заголовок 2 уровня)
            # По методичке: стиль «Заголовок третьего уровня»
            if h['heading_level'] != 2:
                errors.append(f"'{pv}': должен быть стиль «Заголовок 2» (Заголовок третьего уровня)")

            # Выравнивание по центру
            if h.get('alignment') is not None and h['alignment'] != 1:
                errors.append(f"'{pv}': выравнивание должно быть по центру")

            # Интервалы 0
            sb = h.get('space_before')
            if sb is not None and abs(sb) > 2:
                errors.append(f"'{pv}': интервал перед {sb:.0f} пт (должен 0)")

            sa = h.get('space_after')
            if sa is not None and abs(sa) > 2:
                errors.append(f"'{pv}': интервал после {sa:.0f} пт (должен 0)")

        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений в приложениях: {len(errors)}', details=errors,
                received=f"Приложений: {len(appendices)}",
                expected="Приложение А, Б, В... (без Ё,З,Й,О,Ч,Ь,Ы,Ъ), заголовок по центру, интервалы 0, ссылки в тексте"
            )

        return RuleResult(
            status='pass',
            summary=f'Приложения оформлены правильно ({len(appendices)} шт.)',
            received=f"Приложений: {len(appendices)}"
        )