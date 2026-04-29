"""
Правило 01: Подготовка письменных материалов. Структура ВКР.
Проверяет:
- Имя файла соответствует шаблону
- Наличие обязательных структурных элементов
- Порядок следования разделов
- Нумерацию разделов
"""

import os, re
from .base_rule import BaseRule, RuleResult


class StructureRule(BaseRule):
    @property
    def rule_id(self): return "structure"
    @property
    def name(self): return "Структура ВКР"
    @property
    def description(self): return "Проверка имени файла, обязательных разделов, порядка и нумерации"

    REQUIRED = [
        'АННОТАЦИЯ', 'ОГЛАВЛЕНИЕ', 'ВВЕДЕНИЕ',
        'ЗАКЛЮЧЕНИЕ', 'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ', 'ПРИЛОЖЕНИЯ'
    ]
    OPTIONAL = ['СПИСОК ИСПОЛЬЗУЕМЫХ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ']
    ORDER = [
        'АННОТАЦИЯ', 'ОГЛАВЛЕНИЕ',
        'СПИСОК ИСПОЛЬЗУЕМЫХ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ',
        'ВВЕДЕНИЕ', '__NUMBERED__', 'ЗАКЛЮЧЕНИЕ',
        'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ', 'ПРИЛОЖЕНИЯ'
    ]

    def check(self, model):
        errors = []

        # ── 1. Имя файла ────────────────────────────────────────
        fn = model.metadata.get('file_name', '')
        fp = model.metadata.get('folder_path', '')
        folder_surname = os.path.basename(fp).split('_')[0].split(' ')[0]
        pattern = r'^090302_22[А-Я][0-9]{4}_[А-Яа-яёЁ]+(?:-[А-Яа-яёЁ]+)?\.docx?$'
        exp = '090302_22[БУКВА][4 ЦИФРЫ]_[ФАМИЛИЯ].docx'
        if not re.match(pattern, fn):
            errors.append(f"Имя файла '{fn}' не соответствует шаблону {exp}")
        else:
            file_surname = os.path.splitext(fn)[0].split('_')[-1]
            if folder_surname.lower() != file_surname.lower():
                errors.append(f"Фамилия в файле ({file_surname}) не совпадает с папкой ({folder_surname})")

        # ── 2. Заголовки первого уровня ─────────────────────────
        l1 = [h for h in model.headings if h['heading_level'] == 1]
        if not l1:
            errors.append("Заголовки первого уровня не найдены. Используйте стиль «Заголовок 1».")
            return RuleResult(status='fail', summary='Заголовки не найдены', details=errors,
                expected="Заголовок 1 для разделов: " + ', '.join(self.REQUIRED))

        found = [h['text'].upper() for h in l1]

        # 2a. Наличие обязательных
        missing = [r for r in self.REQUIRED if r not in found]
        if missing:
            errors.append(f"Отсутствуют обязательные разделы: {', '.join(missing)}")

        # 2b. Правильные названия
        if 'СОДЕРЖАНИЕ' in found and 'ОГЛАВЛЕНИЕ' not in found:
            errors.append("Раздел должен называться «ОГЛАВЛЕНИЕ», а не «СОДЕРЖАНИЕ»")
        if 'ПРИЛОЖЕНИЕ' in found and 'ПРИЛОЖЕНИЯ' not in found:
            errors.append("Раздел должен называться «ПРИЛОЖЕНИЯ», а не «ПРИЛОЖЕНИЕ»")

        # 2c. Порядок следования
        actual_order = []
        for h in l1:
            t = h['text'].upper()
            if re.match(r'^\d+', t):
                if '__NUMBERED__' not in actual_order:
                    actual_order.append('__NUMBERED__')
            elif t in self.REQUIRED or t in self.OPTIONAL:
                actual_order.append(t)
            else:
                actual_order.append(t)

        expected_order = []
        seen_numbered = False
        for item in self.ORDER:
            if item == '__NUMBERED__':
                if '__NUMBERED__' in actual_order and not seen_numbered:
                    expected_order.append('__NUMBERED__')
                    seen_numbered = True
            elif item in actual_order:
                expected_order.append(item)

        if actual_order != expected_order:
            errors.append(
                f"Нарушен порядок разделов. "
                f"Ожидается: {' → '.join(expected_order)}. "
                f"Фактически: {' → '.join(actual_order)}"
            )

        # 2d. Нумерация разделов
        numbered = [(int(m.group(1)), h) for h in l1 if (m := re.match(r'^(\d+)', h['text']))]
        if not numbered:
            errors.append("Нет нумерованных разделов (основная часть)")
        else:
            exp_n = 1
            for n, h in numbered:
                if n != exp_n:
                    errors.append(f"Нарушение нумерации: после раздела {exp_n-1} идёт раздел {n} ('{h['text']}')")
                exp_n = n + 1

        # ── Итог ────────────────────────────────────────────────
        lines = '\n'.join(f"  — {h['text']}" for h in l1)
        received = f"Заголовков: {len(l1)}\n{lines}"

        if errors:
            return RuleResult(status='fail', summary=f'Нарушений: {len(errors)}', details=errors,
                received=received,
                expected=f"Имя: {exp}. Разделы: {', '.join(self.REQUIRED)}. "
                         f"Порядок: АННОТАЦИЯ → ОГЛАВЛЕНИЕ → [СОКРАЩЕНИЯ] → ВВЕДЕНИЕ → разделы → ЗАКЛЮЧЕНИЕ → ИСТОЧНИКИ → ПРИЛОЖЕНИЯ")

        return RuleResult(status='pass', summary=f'Структура ВКР соответствует требованиям', received=received)