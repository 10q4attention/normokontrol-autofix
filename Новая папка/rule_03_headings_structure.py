import re
from .base_rule import BaseRule, RuleResult

class HeadingsStructureRule(BaseRule):
    @property
    def rule_id(self): return "headings_structure"
    @property
    def name(self): return "Структура заголовков первого уровня"
    @property
    def description(self): return "Проверка наличия обязательных разделов, порядка и нумерации"

    REQUIRED = [
        'АННОТАЦИЯ', 'ОГЛАВЛЕНИЕ', 'ВВЕДЕНИЕ',
        'ЗАКЛЮЧЕНИЕ', 'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ', 'ПРИЛОЖЕНИЯ'
    ]

    OPTIONAL = ['СПИСОК ИСПОЛЬЗУЕМЫХ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ']

    # Правильный порядок
    ORDER = [
        'АННОТАЦИЯ', 'ОГЛАВЛЕНИЕ',
        'СПИСОК ИСПОЛЬЗУЕМЫХ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ',  # опционально
        'ВВЕДЕНИЕ', '__NUMBERED__', 'ЗАКЛЮЧЕНИЕ',
        'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ', 'ПРИЛОЖЕНИЯ'
    ]

    def check(self, model):
        l1 = [h for h in model.headings if h['level'] == 1]
        if not l1:
            return RuleResult(status='fail', summary='Заголовки первого уровня не найдены',
                details=['Нет абзацев со стилем "Заголовок 1"'])

        errors = []
        found_upper = [h['text'].upper() for h in l1]

        # 1. Наличие обязательных
        missing = [r for r in self.REQUIRED if r not in found_upper]
        if missing:
            errors.append(f"Отсутствуют обязательные разделы: {', '.join(missing)}")

        # 2. Правильные названия
        if 'СОДЕРЖАНИЕ' in found_upper and 'ОГЛАВЛЕНИЕ' not in found_upper:
            errors.append("Раздел должен называться «ОГЛАВЛЕНИЕ», а не «СОДЕРЖАНИЕ»")
        if 'ПРИЛОЖЕНИЕ' in found_upper and 'ПРИЛОЖЕНИЯ' not in found_upper:
            errors.append("Раздел должен называться «ПРИЛОЖЕНИЯ», а не «ПРИЛОЖЕНИЕ»")

        # 3. Порядок следования
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
                f"Нарушен порядок разделов.\n"
                f"Ожидается: {' -> '.join(expected_order)}\n"
                f"Фактически: {' -> '.join(actual_order)}"
            )

        # 4. Нумерация
        numbered = [(int(m.group(1)), h) for h in l1 if (m := re.match(r'^(\d+)', h['text']))]
        if not numbered:
            errors.append("Нет нумерованных разделов (основная часть)")
        else:
            exp = 1
            for n, h in numbered:
                if n != exp:
                    errors.append(f"Нарушение нумерации: после раздела {exp-1} идёт раздел {n} ('{h['text']}')")
                exp = n + 1

        lines = '\n'.join(f"  — {h['text']}" for h in l1)
        received = f"Найдено: {len(l1)}\n{lines}"

        if errors:
            return RuleResult(status='fail', summary=f'Нарушений: {len(errors)}', details=errors,
                received=received,
                expected=f"Обязательные: {', '.join(self.REQUIRED)}. "
                         f"Порядок: АННОТАЦИЯ -> ОГЛАВЛЕНИЕ -> [СОКРАЩЕНИЯ] -> ВВЕДЕНИЕ -> разделы -> ЗАКЛЮЧЕНИЕ -> СПИСОК ИСТОЧНИКОВ -> ПРИЛОЖЕНИЯ")

        return RuleResult(status='pass', summary=f'Все {len(l1)} заголовков верны', received=received)