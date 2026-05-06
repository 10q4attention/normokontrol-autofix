"""
Правило 07: Таблицы.
Проверяет: подписи, форматирование подписей и содержимого, нумерацию, ссылки.
"""

import re
from .base_rule import BaseRule, RuleResult


class TablesRule(BaseRule):
    @property
    def rule_id(self): return "tables"
    @property
    def name(self): return "Таблицы"
    @property
    def description(self): return "Проверка подписей, форматирования, нумерации, ссылок (раздел 7)"

    def check(self, model):
        errors = []
        tables = model.tables
        captions = [c for c in model.captions if c['caption_type'] == 'table']

        # Таблицы без подписей
        for t in tables:
            if not t.get('linked_from'):
                errors.append(f"Таблица без подписи ({t['rows_count']}x{t['cols_count']})")

        # Подписи без таблиц
        for cap in captions:
            if not cap.get('linked_to'):
                errors.append(f"Подпись без таблицы: '{cap['text'][:60]}'")

        # Проверяем подписи и содержимое
        for cap in captions:
            if cap.get('is_continuation'):
                continue
            text = cap['text']
            issues = []

            # 7.1 Тире
            if '--' in text:
                issues.append("тире (—) вместо двух дефисов")
            elif re.search(r'\s-\s', text):
                issues.append("тире (—) вместо дефиса")

            # Точка в конце
            if text.rstrip().endswith('.'):
                issues.append("точка в конце не нужна")

            # Форматирование подписи (табл. 7.1)
            fn = cap.get('font_name')
            if fn and 'times new roman' not in fn.lower():
                issues.append(f"шрифт подписи: {fn}")

            fs = cap.get('font_size_pt')
            if fs is not None and abs(fs - 12) > 0.5:
                issues.append(f"размер подписи: {fs:.0f} пт (нужен 12)")

            if not cap.get('italic'):
                issues.append("подпись должна быть курсивом")

            if cap.get('alignment') is not None and cap['alignment'] != 3:
                issues.append("выравнивание подписи по ширине")

            sb = cap.get('space_before')
            if sb is not None and abs(sb - 6) > 2:
                issues.append(f"интервал перед подписью: {sb:.0f} пт (нужен 6)")

            sa = cap.get('space_after')
            if sa is not None and abs(sa - 0) > 2:
                issues.append(f"интервал после подписи: {sa:.0f} пт (нужен 0)")

            ls = cap.get('line_spacing')
            if ls is not None and isinstance(ls, (int, float)) and abs(ls - 1.0) > 0.1:
                issues.append(f"междустрочный подписи: {ls:.2f} (нужен 1.0)")

            fi = cap.get('first_line_indent')
            if fi is not None and abs(fi) > 0.1:
                issues.append(f"отступ первой строки подписи: {fi:.1f} см (должен 0)")

            # Содержимое таблицы
            t = self._find_by_id(model, cap.get('linked_to'))
            if t:
                for ri, row in enumerate(t['rows']):
                    for ci, cell in enumerate(row):
                        cl = f"строка {ri+1}, столбец {ci+1}"

                        if cell.get('is_empty'):
                            issues.append(f"пустая ячейка ({cl})")

                        # Заголовок столбца — по центру
                        if ri == 0 and cell.get('alignment') is not None and cell['alignment'] != 1:
                            issues.append(f"заголовок столбца {ci+1} должен быть по центру")

                        # Заголовок строки — по левому
                        if ci == 0 and ri > 0 and cell.get('alignment') is not None and cell['alignment'] != 0:
                            issues.append(f"заголовок строки {ri+1} должен быть по левому краю")

                        # Шрифт Times New Roman 12pt
                        cfn = cell.get('font_name')
                        if cfn and 'times new roman' not in cfn.lower():
                            issues.append(f"шрифт в ячейке ({cl}): {cfn}")

                        cfs = cell.get('font_size_pt')
                        if cfs is not None and abs(cfs - 12) > 0.5:
                            issues.append(f"размер в ячейке ({cl}): {cfs:.0f} пт")

                        # Выравнивание: по ширине или по центру
                        ca = cell.get('alignment')
                        if ca is not None and ca not in (1, 3):
                            issues.append(f"выравнивание в ячейке ({cl}) — допустимо по ширине или центру")

                        # Интервалы 0
                        csb = cell.get('space_before')
                        if csb is not None and abs(csb) > 2:
                            issues.append(f"интервал перед в ячейке ({cl}): {csb:.0f} пт")

                        csa = cell.get('space_after')
                        if csa is not None and abs(csa) > 2:
                            issues.append(f"интервал после в ячейке ({cl}): {csa:.0f} пт")

                        # Междустрочный одинарный
                        cls_val = cell.get('line_spacing')
                        if cls_val is not None and isinstance(cls_val, (int, float)) and abs(cls_val - 1.0) > 0.1:
                            issues.append(f"междустрочный в ячейке ({cl}): {cls_val:.2f}")

                        # Отступ первой строки 0
                        cfi = cell.get('first_line_indent')
                        if cfi is not None and abs(cfi) > 0.1:
                            issues.append(f"отступ первой строки в ячейке ({cl}): {cfi:.1f} см")

                # 7.6 Графа «№ п/п»
                if t['rows'] and t['rows'][0]:
                    first = t['rows'][0][0].get('text', '')
                    if first in ('№', 'Номер', '№ п/п', '№ пп'):
                        issues.append("графа «№ п/п» не допускается")

            if issues:
                pv = text[:70] + ('...' if len(text) > 70 else '')
                for iss in issues:
                    errors.append(f"'{pv}': {iss}")

        # Нумерация
        secs = {}
        for cap in captions:
            if cap.get('is_continuation'):
                continue
            m = re.match(r'^Таблица\s+([\dА-ЯA-Z]+)\.(\d+)', cap['text'], re.I)
            if m:
                sid, num = m.group(1), m.group(2)
                if sid not in secs:
                    secs[sid] = []
                secs[sid].append((int(num), cap))
        for sid, lst in secs.items():
            lst.sort(key=lambda x: x[0])
            exp = 1
            for n, cap in lst:
                if n != exp:
                    errors.append(f"'{cap['text'][:60]}': нумерация — ожидалась {sid}.{exp}, найдена {sid}.{n}")
                exp = n + 1

        all_set = set()
        for cap in captions:
            if cap.get('is_continuation'):
                continue
            m = re.match(r'^Таблица\s+([\dА-ЯA-Z]+)\.(\d+)', cap['text'], re.I)
            if m:
                sid, num = m.group(1), m.group(2)
                all_set.add((sid, num))
                body_before = ' '.join(
                    e['text'] for e in model.elements 
                    if e['index'] < cap['index']
                    and e['text'] 
                    and not e.get('is_caption') 
                    and not e.get('is_toc') 
                    and not e.get('is_table')
                )
                if not re.search(rf'\b[Тт]аблиц(?:а|ы|е|у|ей|ам|ами|ах)\s+{sid}\.{num}\b', body_before):
                    errors.append(f"Нет ссылки на таблицу {sid}.{num} перед её появлением")

        # Ссылки на несуществующие (во всём тексте)
        found = re.findall(r'[Тт]аблиц(?:а|ы|е|у|ей|ам|ами|ах)\s+([\dА-ЯA-Z]+)\.(\d+)', model.body_text)
        for rid, rn in found:
            if (rid, rn) not in all_set:
                errors.append(f"Ссылка на несуществующую таблицу {rid}.{rn}")

        real = len([t for t in tables if t.get('linked_from')])
        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений в таблицах: {len(errors)}', details=errors,
                received=f"Таблиц: {len(tables)}, с подписями: {real}",
                expected="Таблица X.Y — Название, формат по табл. 7.1 и 7.2"
            )
        return RuleResult(
            status='pass', summary=f'Таблицы оформлены правильно',
            received=f"Таблиц: {len(tables)}"
        )

    def _find_by_id(self, model, eid):
        if eid is None:
            return None
        for e in model.elements:
            if e['id'] == eid:
                return e
        return None