import re
from .base_rule import BaseRule, RuleResult

class BibliographyRule(BaseRule):
    @property
    def rule_id(self): return "bibliography"
    @property
    def name(self): return "Список использованных источников"
    @property
    def description(self): return "Проверка оформления и ссылок"

    def check(self, model):
        errors = []

        # Находим заголовок
        biblio_heading = None
        for h in model.headings:
            if h['text'].upper() == 'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ':
                biblio_heading = h
                break

        if not biblio_heading:
            return RuleResult(status='fail', summary='Раздел не найден',
                details=['Добавьте раздел с заголовком первого уровня «СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ»'],
                expected="Заголовок первого уровня")

        start_idx = biblio_heading['para_index']

        # Собираем все элементы после заголовка
        # Из list_items (нумерованный список) + из main_text (текст с номером)
        candidates = []

        for li in model.list_items:
            if li['para_index'] > start_idx:
                candidates.append({'source': 'list', 'text': li['text'], 'para_index': li['para_index'],
                                   'font_name': li.get('font_name'), 'font_size_pt': li.get('font_size_pt'),
                                   'alignment': li.get('alignment'), 'line_spacing': li.get('line_spacing'),
                                   'first_line_indent': li.get('first_line_indent')})

        for mt in model.main_text:
            if mt['para_index'] > start_idx:
                candidates.append({'source': 'main', 'text': mt['text'], 'para_index': mt['para_index'],
                                   'font_name': mt.get('font_name'), 'font_size_pt': mt.get('font_size_pt'),
                                   'alignment': mt.get('alignment'), 'line_spacing': mt.get('line_spacing'),
                                   'first_line_indent': mt.get('first_line_indent')})

        # Сортируем по позиции
        candidates.sort(key=lambda x: x['para_index'])

        # Отбираем подряд идущие элементы с правильной нумерацией
        items = []
        expected_num = 1

        for c in candidates:
            text = c['text']
            if not text:  # пустые пропускаем
                continue

            # Проверяем, является ли элемент списком источников
            m = re.match(r'^(\d+)[\.\s]', text)
            if m:
                num = int(m.group(1))
                if num == expected_num:
                    items.append(c)
                    expected_num += 1
                else:
                    # Нарушение нумерации — возможно, конец списка
                    break
            elif c['source'] == 'list':
                # Нет номера в тексте, но это нумерованный список — считаем продолжением
                items.append(c)
                expected_num += 1
            else:
                # Не список и не начинается с номера — конец списка
                break

        if not items:
            return RuleResult(status='fail', summary='Список источников пуст',
                details=['Добавьте пронумерованные источники после заголовка'],
                expected="Не менее одного источника")

        # Проверяем нумерацию
        exp = 1
        for item in items:
            m = re.match(r'^(\d+)', item['text'])
            if m:
                n = int(m.group(1))
                if n != exp:
                    errors.append(f"Нумерация: ожидался {exp}, найден {n} ('{item['text'][:60]}')")
                exp = n + 1
            else:
                exp += 1

        # Форматирование
        for item in items:
            pv = item['text'][:50] + ('...' if len(item['text']) > 50 else '')
            fn = item.get('font_name')
            if fn and 'times new roman' not in fn.lower():
                errors.append(f"'{pv}': шрифт {fn}")
            fs = item.get('font_size_pt')
            if fs and abs(fs - 14) > 0.5:
                errors.append(f"'{pv}': размер {fs:.0f} пт")
            if item.get('alignment') is not None and item['alignment'] != 3:
                errors.append(f"'{pv}': выравнивание по ширине")
            ls = item.get('line_spacing')
            if ls and isinstance(ls, float) and abs(ls - 1.5) > 0.1:
                errors.append(f"'{pv}': междустрочный {ls:.2f}")
            indent = item.get('first_line_indent')
            if indent is not None and abs(indent - 1.25) > 0.2:
                errors.append(f"'{pv}': отступ первой строки {indent:.2f} см")

        # Ссылки
        body_refs = self._extract_refs(model.body_text)
        expected = set(range(1, len(items) + 1))
        for n in sorted(expected - body_refs):
            errors.append(f"На источник [{n}] нет ссылки в тексте")
        for n in sorted(body_refs - expected)[:5]:
            errors.append(f"Ссылка на несуществующий источник [{n}]")
        if len(body_refs - expected) > 5:
            errors.append(f"... и ещё {len(body_refs - expected) - 5} несуществующих ссылок")

        if errors:
            return RuleResult(status='fail', summary=f'Нарушений: {len(errors)}', details=errors,
                received=f"Источников: {len(items)}", expected="Пронумерованный список, ссылки в квадратных скобках")
        return RuleResult(status='pass', summary=f'Список оформлен верно ({len(items)} источников)',
            received=f"Источников: {len(items)}")

    def _extract_refs(self, text):
        refs = set()
        for b in re.findall(r'\[([^\]]+)\]', text):
            for part in b.split(';'):
                has_page_marker = any(m in part for m in ['с.', 'c.', 'стр.'])
                if has_page_marker:
                    # Обрезаем по маркеру, берём только первое число
                    for marker in ['с.', 'c.', 'стр.']:
                        idx = part.find(marker)
                        if idx > 0:
                            part = part[:idx]
                            break
                    numbers = re.findall(r'\d+', part)
                    if numbers:
                        refs.add(int(numbers[0]))  # только первый номер
                else:
                    # Все числа — номера источников
                    for n in re.findall(r'\d+', part):
                        refs.add(int(n))
        return refs