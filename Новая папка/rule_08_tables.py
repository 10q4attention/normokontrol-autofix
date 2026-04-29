import re
from .base_rule import BaseRule, RuleResult

class TablesRule(BaseRule):
    @property
    def rule_id(self): return "tables"
    @property
    def name(self): return "Оформление таблиц"
    @property
    def description(self): return "Проверка подписей, нумерации, ссылок и форматирования"

    def check(self, model):
        errors = []
        tables = model.tables
        captions = [c for c in model.captions if c['caption_type'] == 'table']

        # Таблицы без подписей
        for t in tables:
            if not t.get('caption'):
                errors.append(f"Таблица без подписи ({t['rows_count']}x{t['cols_count']})")

        # Проверяем подписи
        for cap in captions:
            if cap.get('is_continuation'):
                continue
            text = cap['text']
            issues = []

            # ── Тире ─────────────────────────────────────────────
            if '--' in text:
                issues.append("тире (—) вместо двух дефисов")
            elif re.search(r'\s-\s', text):
                issues.append("тире (—) вместо дефиса")

            # ── Точка в конце ────────────────────────────────────
            if text.rstrip().endswith('.'):
                issues.append("точка в конце не нужна")

            # ── Связь с таблицей ─────────────────────────────────
            if not cap.get('linked_object'):
                issues.append("не найдена таблица для подписи")
                # Дальше проверять нечего
                pv = text[:70] + ('...' if len(text) > 70 else '')
                for iss in issues:
                    errors.append(f"'{pv}': {iss}")
                continue

            t = cap['linked_object']

            # ── Форматирование подписи (табл. 7.1) ───────────────
            # Шрифт Times New Roman 12pt
            fn = cap.get('font_name')
            if fn and 'times new roman' not in fn.lower():
                issues.append(f"шрифт подписи: {fn} (нужен Times New Roman)")

            fs = cap.get('font_size_pt')
            if fs and abs(fs - 12) > 0.5:
                issues.append(f"размер подписи: {fs:.0f} пт (нужен 12 пт)")

            # Курсив
            if not cap.get('italic'):
                issues.append("подпись должна быть курсивом")

            # Выравнивание по ширине (3)
            if cap.get('alignment') is not None and cap['alignment'] != 3:
                issues.append("выравнивание подписи по ширине")

            # Интервал перед 6 пт
            sb = cap.get('space_before')
            if sb is not None and abs(sb - 6) > 2:
                issues.append(f"интервал перед подписью: {sb:.0f} пт (нужен 6 пт)")

            # Интервал после 0 пт
            sa = cap.get('space_after')
            if sa is not None and abs(sa - 0) > 2:
                issues.append(f"интервал после подписи: {sa:.0f} пт (нужен 0 пт)")

            # Междустрочный одинарный (1.0)
            ls = cap.get('line_spacing')
            if ls is not None:
                if isinstance(ls, float) and abs(ls - 1.0) > 0.1:
                    issues.append(f"междустрочный подписи: {ls:.2f} (нужен 1.0)")

            # Отступ первой строки 0 см
            indent = cap.get('first_line_indent')
            if indent is not None and abs(indent - 0) > 0.1:
                issues.append(f"отступ первой строки подписи: {indent:.1f} см (должен 0 см)")

            # Отступ слева 0 см
            left = cap.get('left_indent')
            if left is not None and abs(left - 0) > 0.1:
                issues.append(f"отступ слева подписи: {left:.1f} см (должен 0 см)")

            # ── Содержимое таблицы (табл. 7.2) ───────────────────
            for ri, row in enumerate(t['cells']):
                for ci, cell in enumerate(row):
                    cell_label = f"строка {ri+1}, столбец {ci+1}"

                    # Пустые ячейки
                    if cell.get('is_empty'):
                        issues.append(f"пустая ячейка ({cell_label})")

                    # Шрифт Times New Roman 12pt (любое начертание)
                    cfn = cell.get('font_name')
                    if cfn and 'times new roman' not in cfn.lower():
                        issues.append(f"шрифт в ячейке ({cell_label}): {cfn}")

                    cfs = cell.get('font_size_pt')
                    if cfs and abs(cfs - 12) > 0.5:
                        issues.append(f"размер в ячейке ({cell_label}): {cfs:.0f} пт")

                    # Выравнивание: по ширине или по центру (3 или 1)
                    ca = cell.get('alignment')
                    if ca is not None and ca not in (1, 3):
                        issues.append(f"выравнивание в ячейке ({cell_label}) — допустимо по ширине или центру")

                    # Заголовки столбцов (первая строка) — по центру
                    if ri == 0 and ca is not None and ca != 1:
                        issues.append(f"заголовок столбца {ci+1} должен быть по центру")

                    # Заголовки строк (первый столбец, не первая строка) — по левому краю
                    if ci == 0 and ri > 0 and ca is not None and ca != 0:
                        issues.append(f"заголовок строки {ri+1} должен быть по левому краю")

                    # Отступ первой строки — 0 см
                    c_indent = cell.get('first_line_indent')
                    if c_indent is not None and abs(c_indent - 0) > 0.1:
                        issues.append(f"отступ первой строки в ячейке ({cell_label}): {c_indent:.1f} см (должен 0 см)")

                    # Интервал перед 0 пт
                    c_sb = cell.get('space_before')
                    if c_sb is not None and abs(c_sb - 0) > 2:
                        issues.append(f"интервал перед в ячейке ({cell_label}): {c_sb:.0f} пт (нужен 0 пт)")

                    # Интервал после 0 пт
                    c_sa = cell.get('space_after')
                    if c_sa is not None and abs(c_sa - 0) > 2:
                        issues.append(f"интервал после в ячейке ({cell_label}): {c_sa:.0f} пт (нужен 0 пт)")

                    # Междустрочный одинарный (1.0)
                    c_ls = cell.get('line_spacing')
                    if c_ls is not None:
                        if isinstance(c_ls, float) and abs(c_ls - 1.0) > 0.1:
                            issues.append(f"междустрочный в ячейке ({cell_label}): {c_ls:.2f} (нужен 1.0)")

            # ── Графа «№ п/п» ────────────────────────────────────
            if t['cells']:
                first_cell_text = t['cells'][0][0]['text'] if t['cells'][0] else ''
                if first_cell_text in ('№', 'Номер', '№ п/п', '№ пп'):
                    issues.append("графа «№ п/п» не допускается")

            if issues:
                pv = text[:70] + ('...' if len(text) > 70 else '')
                for iss in issues:
                    errors.append(f"'{pv}': {iss}")

        # ── Нумерация ────────────────────────────────────────────
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

        # ── Ссылки ──────────────────────────────────────────────
        all_set = set()
        for cap in captions:
            if cap.get('is_continuation'):
                continue
            m = re.match(r'^Таблица\s+([\dА-ЯA-Z]+)\.(\d+)', cap['text'], re.I)
            if m:
                all_set.add((m.group(1), m.group(2)))
        for sid, num in all_set:
            if not re.search(rf'\b[Тт]аблиц(?:а|ы|е|у|ей|ам|ами|ах)\s+{sid}\.{num}\b', model.body_text):
                errors.append(f"Нет ссылки на таблицу {sid}.{num}")
        found = re.findall(r'[Тт]аблиц(?:а|ы|е|у|ей|ам|ами|ах)\s+([\dА-ЯA-Z]+)\.(\d+)', model.body_text)
        for rid, rn in found:
            if (rid, rn) not in all_set:
                errors.append(f"Ссылка на несуществующую таблицу {rid}.{rn}")

        real = len([t for t in tables if t.get('caption')])
        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений в таблицах: {len(errors)}', details=errors,
                received=f"Таблиц: {len(tables)}, с подписями: {real}",
                expected="Таблица X.Y — Название, формат по табл. 7.1 (подпись) и 7.2 (содержимое)"
            )
        return RuleResult(
            status='pass', summary=f'Таблицы оформлены верно',
            received=f"Таблиц: {len(tables)}"
        )