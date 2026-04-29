"""
Правило 10: Маркированные списки.
Проверяет оформление маркированных списков (раздел 10).
"""

import re
from lxml import etree
from .base_rule import BaseRule, RuleResult

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


class BulletListsRule(BaseRule):
    @property
    def rule_id(self): return "bullet_lists"
    @property
    def name(self): return "Маркированные списки"
    @property
    def description(self): return "Проверка оформления маркированных списков (раздел 10)"

    def check(self, model):
        errors = []

        # Отбираем маркированные: текст начинается с тире/дефиса
        bullet_items = [li for li in model.list_items if re.match(r'^[—–\-]', li['text'])]

        # Также ищем элементы списков, где маркер скрыт (нумерованные Word, но по факту маркированные)
        for li in model.list_items:
            if li not in bullet_items:
                marker = self._get_list_marker(model.doc, li)
                if marker and marker not in ('decimal', None) and not marker.isdigit():
                    bullet_items.append(li)

        if not bullet_items:
            return RuleResult(status='pass', summary='Маркированные списки не найдены')

        # Группируем по последовательности
        bullet_items.sort(key=lambda x: x['index'])
        groups = []
        cur = [bullet_items[0]]
        for i in range(1, len(bullet_items)):
            if bullet_items[i]['index'] == cur[-1]['index'] + 1:
                cur.append(bullet_items[i])
            else:
                groups.append(cur)
                cur = [bullet_items[i]]
        groups.append(cur)

        for group in groups:
            for idx, item in enumerate(group):
                text = item['text']
                pv = text[:50] + ('...' if len(text) > 50 else '')

                # Проверяем маркер через XML
                marker = self._get_list_marker(model.doc, item)

                # 10.1 Маркер должен быть тире
                if marker is not None:
                    if marker == '-':
                        errors.append(f"'{pv}': маркер — дефис (-), должно быть тире (—)")
                    elif marker == '•':
                        errors.append(f"'{pv}': маркер — точка (•), должно быть тире (—)")
                    elif marker not in ('—', '–', '-', '•', 'decimal', None):
                        errors.append(f"'{pv}': маркер '{marker}' нестандартный, должно быть тире (—)")
                else:
                    # Проверяем по тексту
                    if text.startswith('--'):
                        errors.append(f"'{pv}': тире (—) вместо двух дефисов")
                    elif text.startswith('-') and not text.startswith('—') and not text.startswith('–'):
                        errors.append(f"'{pv}': тире (—) вместо дефиса")

                # 10.2 Пунктуация
                content = re.sub(r'^[—–\-]\s*', '', text)
                if content:
                    if content[0].isalpha() and content[0].isupper():
                        errors.append(f"'{pv}': текст должен начинаться со строчной буквы")

                    is_last = (idx == len(group) - 1)
                    if is_last:
                        if not content.rstrip().endswith('.'):
                            errors.append(f"'{pv}': последний элемент должен заканчиваться точкой")
                    else:
                        if not content.rstrip().endswith(';'):
                            errors.append(f"'{pv}': элемент должен заканчиваться точкой с запятой")

                # Форматирование
                fn = item.get('font_name')
                if fn and 'times new roman' not in fn.lower():
                    errors.append(f"'{pv}': шрифт {fn}")

                fs = item.get('font_size_pt')
                if fs is not None and abs(fs - 14) > 0.5:
                    errors.append(f"'{pv}': размер {fs:.0f} пт (нужен 14)")

                if item.get('alignment') is not None and item['alignment'] != 3:
                    errors.append(f"'{pv}': выравнивание по ширине")

                ls = item.get('line_spacing')
                if ls is not None and isinstance(ls, (int, float)) and abs(ls - 1.5) > 0.1:
                    errors.append(f"'{pv}': междустрочный {ls:.2f} (нужен 1.5)")

                li_val = item.get('left_indent')
                if li_val is not None and abs(li_val) > 0.1:
                    errors.append(f"'{pv}': отступ слева {li_val:.1f} см (должен 0)")

                fi = item.get('first_line_indent')
                if fi is not None and abs(fi - 1.25) > 0.3:
                    errors.append(f"'{pv}': отступ первой строки {fi:.1f} см (нужен 1.25)")

        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений в маркированных списках: {len(errors)}',
                details=errors,
                received=f"Групп: {len(groups)}, элементов: {len(bullet_items)}",
                expected="Маркер — тире (—), строчная, точка с запятой (последний — точка), "
                         "Times New Roman 14pt, по ширине, межстрочный 1.5, отступ слева 0, маркер 1.25"
            )

        return RuleResult(
            status='pass',
            summary=f'Маркированные списки оформлены правильно',
            received=f"Групп: {len(groups)}, элементов: {len(bullet_items)}"
        )

    def _get_list_marker(self, doc, item):
        """Извлекает символ маркера из определения списка в XML"""
        try:
            # Получаем paragraph по индексу
            para = doc.paragraphs[item['para_index']]
            numPr = para._element.find(f'.//{{{W}}}numPr')
            if numPr is None:
                return None
            numId = numPr.find(f'{{{W}}}numId')
            if numId is None:
                return None
            numIdVal = numId.get(f'{{{W}}}val')

            numbering = doc._element.find(f'{{{W}}}numbering')
            if numbering is None:
                return None

            for num in numbering.findall(f'{{{W}}}num'):
                if num.get(f'{{{W}}}numId') == numIdVal:
                    lvl = num.find(f'{{{W}}}lvl[@w:ilvl="0"]')
                    if lvl is None:
                        lvl = num.find(f'{{{W}}}lvl')
                    if lvl is not None:
                        numFmt = lvl.find(f'{{{W}}}numFmt')
                        if numFmt is not None:
                            fmt = numFmt.get(f'{{{W}}}val')
                            if fmt == 'bullet':
                                lvlText = lvl.find(f'{{{W}}}lvlText')
                                if lvlText is not None:
                                    return lvlText.get(f'{{{W}}}val', '•')
                            return fmt
        except:
            pass
        return None