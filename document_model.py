"""Модель документа. Единая структура, все 11 параметров, множественные роли, цепочка стилей."""

import re
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'


class DocumentModel:
    def __init__(self, doc_path, doc_metadata, doc):
        self.doc_path = doc_path
        self.metadata = doc_metadata
        self.doc = doc
        self._styles_xml = doc._element.find(f'{{{W}}}styles')

        body = doc._element.body
        children = list(body)

        self.elements = []
        pi, ti = 0, 0

        for idx, child in enumerate(children):
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

            if tag == 'p':
                para = doc.paragraphs[pi]
                elem = self._make_element(para, pi, idx)
                self.elements.append(elem)
                pi += 1

            elif tag == 'tbl':
                table = doc.tables[ti]
                elem = self._make_table_element(table, ti, idx)
                self.elements.append(elem)
                ti += 1
            
            elif tag == 'sdt':
                # Обрабатываем автособираемое содержание (SDT)
                sdt_content = child.find(f'.//{{{W}}}sdtContent')
                if sdt_content is not None:
                    for p_elem in sdt_content.findall(f'.//{{{W}}}p'):
                        # Ищем соответствующий параграф в doc.paragraphs
                        for para in doc.paragraphs:
                            if para._element is p_elem:
                                text = para.text.strip() if para.text else ''
                                style = para.style.name if para.style and para.style.name else ''
                                style_lower = style.lower()
                                
                                elem = {
                                    'id': len(self.elements),
                                    'index': idx,  # привязываем к индексу SDT
                                    'kind': 'paragraph',
                                    'text': text,
                                    'style_name': style,
                                    'style_lower': style_lower,
                                    'is_heading': False, 'heading_level': None, 'heading_number': None,
                                    'is_caption': False, 'caption_type': None, 'caption_number': None,
                                    'is_continuation': False, 'is_list_item': False, 'is_code': False,
                                    'has_border': False, 'is_toc': True,  # ← ВАЖНО: помечаем как TOC
                                    'has_drawing': False, 'has_formula': False, 'is_table': False,
                                    'text_category': None, 'linked_to': None, 'linked_from': None,
                                    'font_name': None, 'font_size_pt': None, 'bold': False, 'italic': False,
                                    'alignment': None, 'space_before': None, 'space_after': None,
                                    'line_spacing': None, 'first_line_indent': None,
                                    'left_indent': None, 'right_indent': None,
                                }
                                self._extract_all_props(para, elem)
                                self.elements.append(elem)
                                pi += 1  # увеличиваем счётчик параграфов
                                break

        self._link()
        self._categorize_text()

        self.headings = [e for e in self.elements if e['is_heading']]
        self.tables = [e for e in self.elements if e['is_table']]
        self.drawings = [e for e in self.elements if e['has_drawing']]
        self.captions = [e for e in self.elements if e['is_caption']]
        self.list_items = [e for e in self.elements if e['is_list_item']]
        self.formulas = [e for e in self.elements if e['has_formula']]
        self.code_blocks = [e for e in self.elements if e['is_code']]
        self.toc_entries = [e for e in self.elements if e['is_toc']]
        self.main_text = [e for e in self.elements if e['text_category'] in ('main', 'bibliography', 'appendix')]
        self.body_text = ' '.join(
            e['text'] for e in self.elements 
            if e['text'] and not e.get('is_caption') and not e.get('is_toc') and not e.get('is_table')
        )
        self.page_setup = self._extract_page_setup(doc)

    # ═══════════════════════════════════════════════════════════════
    # СОЗДАНИЕ ЭЛЕМЕНТА
    # ═══════════════════════════════════════════════════════════════

    def _make_element(self, para, pi, idx):
        text = para.text.strip() if para.text else ''
        style = para.style.name if para.style and para.style.name else ''
        style_lower = style.lower()

        elem = {
            'id': idx, 'index': idx, 'kind': 'paragraph',
            'text': text, 'style_name': style, 'style_lower': style_lower,
            'is_heading': False, 'heading_level': None, 'heading_number': None,
            'is_caption': False, 'caption_type': None, 'caption_number': None,
            'is_continuation': False, 'is_list_item': False, 'is_code': False,
            'has_border': False, 'is_toc': False, 'has_drawing': False,
            'has_formula': False, 'is_table': False,
            'text_category': None, 'linked_to': None, 'linked_from': None,
            'font_name': None, 'font_size_pt': None, 'bold': False, 'italic': False,
            'alignment': None, 'space_before': None, 'space_after': None,
            'line_spacing': None, 'first_line_indent': None,
            'left_indent': None, 'right_indent': None,
        }

        self._extract_all_props(para, elem)
        self._assign_roles(elem, para)
        return elem

    def _make_table_element(self, table, ti, idx):
        rows = []
        for row in table.rows:
            r = []
            for cell in row.cells:
                ct = cell.text.strip()
                pp = cell.paragraphs[0] if cell.paragraphs else None
                cell_elem = {
                    'text': ct, 'is_empty': not bool(ct),
                    'font_name': None, 'font_size_pt': None,
                    'bold': False, 'italic': False, 'alignment': None,
                    'space_before': None, 'space_after': None,
                    'line_spacing': None, 'first_line_indent': None,
                }
                if pp:
                    self._extract_all_props(pp, cell_elem)
                r.append(cell_elem)
            rows.append(r)

        return {
            'id': idx, 'index': idx, 'kind': 'table',
            'text': '', 'style_name': '', 'style_lower': '',
            'is_heading': False, 'heading_level': None, 'heading_number': None,
            'is_caption': False, 'caption_type': None, 'caption_number': None,
            'is_continuation': False, 'is_list_item': False, 'is_code': False,
            'has_border': False, 'is_toc': False, 'has_drawing': False,
            'has_formula': False, 'is_table': True,
            'text_category': None, 'linked_to': None, 'linked_from': None,
            'font_name': None, 'font_size_pt': None, 'bold': False, 'italic': False,
            'alignment': None, 'space_before': None, 'space_after': None,
            'line_spacing': None, 'first_line_indent': None,
            'left_indent': None, 'right_indent': None,
            'rows': rows,
            'rows_count': len(table.rows),
            'cols_count': len(table.columns) if table.columns else 0,
        }

    # ═══════════════════════════════════════════════════════════════
    # ИЗВЛЕЧЕНИЕ 11 ПАРАМЕТРОВ
    # ═══════════════════════════════════════════════════════════════

    def _extract_all_props(self, para, target):
        target['font_name'] = self._get_font_name(para)
        target['font_size_pt'] = self._get_font_size(para)
        target['bold'] = self._get_bold(para) or False
        target['italic'] = self._get_italic(para) or False
        target['alignment'] = para.alignment
        target['space_before'] = self._get_space_before(para)
        target['space_after'] = self._get_space_after(para)
        target['line_spacing'] = self._get_line_spacing(para)
        target['first_line_indent'] = self._get_first_line_indent(para)
        target['left_indent'] = self._get_left_indent(para)
        target['right_indent'] = self._get_right_indent(para)

    def _first_run(self, para):
        for run in para.runs:
            if run.text.strip():
                return run
        return None

    def _get_font_name(self, para):
        run = self._first_run(para)
        if run and run.font.name: return run.font.name
        if run:
            try:
                rpr = run._element.find(f'{{{W}}}rPr')
                if rpr is not None:
                    rf = rpr.find(f'{{{W}}}rFonts')
                    if rf is not None:
                        f = rf.get(f'{{{W}}}ascii') or rf.get(f'{{{W}}}hAnsi')
                        if f: return f
            except: pass
        try:
            if para.style and para.style.font and para.style.font.name:
                return para.style.font.name
        except: pass
        try:
            if para.style:
                rpr = para.style._element.find(f'{{{W}}}rPr')
                if rpr is not None:
                    rf = rpr.find(f'{{{W}}}rFonts')
                    if rf is not None:
                        f = rf.get(f'{{{W}}}ascii') or rf.get(f'{{{W}}}hAnsi')
                        if f: return f
        except: pass
        return self._chain(para, 'font_name')

    def _get_font_size(self, para):
        run = self._first_run(para)
        if run and run.font.size and hasattr(run.font.size, 'pt'):
            return run.font.size.pt
        if run:
            try:
                rpr = run._element.find(f'{{{W}}}rPr')
                if rpr is not None:
                    sz = rpr.find(f'{{{W}}}sz')
                    if sz is not None:
                        v = sz.get(f'{{{W}}}val')
                        if v: return int(v)/2.0
            except: pass
        try:
            if para.style and para.style.font and para.style.font.size and hasattr(para.style.font.size, 'pt'):
                return para.style.font.size.pt
        except: pass
        try:
            if para.style:
                rpr = para.style._element.find(f'{{{W}}}rPr')
                if rpr is not None:
                    sz = rpr.find(f'{{{W}}}sz')
                    if sz is not None:
                        v = sz.get(f'{{{W}}}val')
                        if v: return int(v)/2.0
        except: pass
        return self._chain(para, 'font_size_pt')

    def _get_bold(self, para):
        run = self._first_run(para)
        if run and run.font.bold is True: return True
        if run:
            try:
                rpr = run._element.find(f'{{{W}}}rPr')
                if rpr is not None:
                    b = rpr.find(f'{{{W}}}b')
                    if b is not None:
                        return b.get(f'{{{W}}}val','true') not in ('false','0')
            except: pass
        try:
            if para.style and para.style.font and para.style.font.bold is True: return True
        except: pass
        try:
            if para.style:
                rpr = para.style._element.find(f'{{{W}}}rPr')
                if rpr is not None:
                    b = rpr.find(f'{{{W}}}b')
                    if b is not None:
                        return b.get(f'{{{W}}}val','true') not in ('false','0')
        except: pass
        return self._chain(para, 'bold') or False

    def _get_italic(self, para):
        run = self._first_run(para)
        if run and run.font.italic is True: return True
        if run:
            try:
                rpr = run._element.find(f'{{{W}}}rPr')
                if rpr is not None:
                    i_el = rpr.find(f'{{{W}}}i')
                    if i_el is not None:
                        return i_el.get(f'{{{W}}}val','true') not in ('false','0')
            except: pass
        try:
            if para.style and para.style.font and para.style.font.italic is True: return True
        except: pass
        try:
            if para.style:
                rpr = para.style._element.find(f'{{{W}}}rPr')
                if rpr is not None:
                    i_el = rpr.find(f'{{{W}}}i')
                    if i_el is not None:
                        return i_el.get(f'{{{W}}}val','true') not in ('false','0')
        except: pass
        return self._chain(para, 'italic') or False

    def _get_space_before(self, para):
        v = self._pt(para.paragraph_format.space_before)
        if v is not None: return v
        v = self._xml_para(para, 'space_before')
        if v is not None: return v
        try:
            if para.style and para.style.paragraph_format:
                v = self._pt(para.style.paragraph_format.space_before)
                if v is not None: return v
        except: pass
        v = self._xml_style(para, 'space_before')
        if v is not None: return v
        return self._chain(para, 'space_before')

    def _get_space_after(self, para):
        v = self._pt(para.paragraph_format.space_after)
        if v is not None: return v
        v = self._xml_para(para, 'space_after')
        if v is not None: return v
        try:
            if para.style and para.style.paragraph_format:
                v = self._pt(para.style.paragraph_format.space_after)
                if v is not None: return v
        except: pass
        v = self._xml_style(para, 'space_after')
        if v is not None: return v
        return self._chain(para, 'space_after')

    def _get_line_spacing(self, para):
        v = self._ls(para.paragraph_format.line_spacing)
        if v is not None: return v
        v = self._xml_para(para, 'line_spacing')
        if v is not None: return v
        try:
            if para.style and para.style.paragraph_format:
                v = self._ls(para.style.paragraph_format.line_spacing)
                if v is not None: return v
        except: pass
        v = self._xml_style(para, 'line_spacing')
        if v is not None: return v
        return self._chain(para, 'line_spacing')

    def _get_first_line_indent(self, para):
        v = self._cm(para.paragraph_format.first_line_indent)
        if v is not None: return v
        v = self._xml_para(para, 'first_line_indent')
        if v is not None: return v
        try:
            if para.style and para.style.paragraph_format:
                v = self._cm(para.style.paragraph_format.first_line_indent)
                if v is not None: return v
        except: pass
        v = self._xml_style(para, 'first_line_indent')
        if v is not None: return v
        return self._chain(para, 'first_line_indent')

    def _get_left_indent(self, para):
        v = self._cm(para.paragraph_format.left_indent)
        if v is not None: return v
        v = self._xml_para(para, 'left_indent')
        if v is not None: return v
        try:
            if para.style and para.style.paragraph_format:
                v = self._cm(para.style.paragraph_format.left_indent)
                if v is not None: return v
        except: pass
        v = self._xml_style(para, 'left_indent')
        if v is not None: return v
        return self._chain(para, 'left_indent')

    def _get_right_indent(self, para):
        v = self._cm(para.paragraph_format.right_indent)
        if v is not None: return v
        v = self._xml_para(para, 'right_indent')
        if v is not None: return v
        try:
            if para.style and para.style.paragraph_format:
                v = self._cm(para.style.paragraph_format.right_indent)
                if v is not None: return v
        except: pass
        v = self._xml_style(para, 'right_indent')
        if v is not None: return v
        return self._chain(para, 'right_indent')

    # ═══════════════════════════════════════════════════════════════
    # ЦЕПОЧКА НАСЛЕДОВАНИЯ СТИЛЕЙ
    # ═══════════════════════════════════════════════════════════════

    def _chain(self, para, prop):
        """Ищет свойство в цепочке basedOn стилей"""
        if not para.style or self._styles_xml is None:
            return None
        try:
            current_id = para.style._element.get(f'{{{W}}}styleId')
            for _ in range(5):
                found = False
                for s in self._styles_xml.findall(f'{{{W}}}style'):
                    if s.get(f'{{{W}}}styleId') == current_id:
                        val = self._extract_from_style_elem(s, prop)
                        if val is not None:
                            return val
                        based = s.find(f'{{{W}}}basedOn')
                        if based is not None:
                            current_id = based.get(f'{{{W}}}val')
                            found = True
                            break
                        else:
                            return None
                if not found:
                    break
        except: pass
        return None

    def _extract_from_style_elem(self, style_elem, prop):
        if prop == 'bold':
            rpr = style_elem.find(f'{{{W}}}rPr')
            if rpr is not None:
                b = rpr.find(f'{{{W}}}b')
                if b is not None:
                    return b.get(f'{{{W}}}val', 'true') not in ('false', '0')
        elif prop == 'italic':
            rpr = style_elem.find(f'{{{W}}}rPr')
            if rpr is not None:
                i_el = rpr.find(f'{{{W}}}i')
                if i_el is not None:
                    return i_el.get(f'{{{W}}}val', 'true') not in ('false', '0')
        elif prop == 'font_name':
            rpr = style_elem.find(f'{{{W}}}rPr')
            if rpr is not None:
                rf = rpr.find(f'{{{W}}}rFonts')
                if rf is not None:
                    return rf.get(f'{{{W}}}ascii') or rf.get(f'{{{W}}}hAnsi')
        elif prop == 'font_size_pt':
            rpr = style_elem.find(f'{{{W}}}rPr')
            if rpr is not None:
                sz = rpr.find(f'{{{W}}}sz')
                if sz is not None:
                    v = sz.get(f'{{{W}}}val')
                    if v: return int(v) / 2.0
        elif prop == 'space_before':
            ppr = style_elem.find(f'{{{W}}}pPr')
            if ppr is not None:
                sp = ppr.find(f'{{{W}}}spacing')
                if sp is not None:
                    v = sp.get(f'{{{W}}}before')
                    if v: return int(v) / 20.0
        elif prop == 'space_after':
            ppr = style_elem.find(f'{{{W}}}pPr')
            if ppr is not None:
                sp = ppr.find(f'{{{W}}}spacing')
                if sp is not None:
                    v = sp.get(f'{{{W}}}after')
                    if v: return int(v) / 20.0
        elif prop == 'line_spacing':
            ppr = style_elem.find(f'{{{W}}}pPr')
            if ppr is not None:
                sp = ppr.find(f'{{{W}}}spacing')
                if sp is not None:
                    v = sp.get(f'{{{W}}}line')
                    if v: return int(v) / 240.0
        elif prop in ('first_line_indent', 'left_indent', 'right_indent'):
            attr = {'first_line_indent': 'firstLine', 'left_indent': 'left', 'right_indent': 'right'}[prop]
            ppr = style_elem.find(f'{{{W}}}pPr')
            if ppr is not None:
                ind = ppr.find(f'{{{W}}}ind')
                if ind is not None:
                    v = ind.get(f'{{{W}}}{attr}')
                    if v: return int(v) / 360000.0
        return None

    def _xml_para(self, para, prop):
        return self._extract_from_style_elem(para._element, prop)

    def _xml_style(self, para, prop):
        try:
            if para.style:
                return self._extract_from_style_elem(para.style._element, prop)
        except: pass
        return None

    # ═══════════════════════════════════════════════════════════════
    # РОЛИ, СВЯЗИ, КАТЕГОРИИ, СТРАНИЦЫ, ВИЗУАЛИЗАЦИЯ — без изменений
    # ═══════════════════════════════════════════════════════════════

    def _assign_roles(self, elem, para):
        text = elem['text']
        style = elem['style_lower']

        if self._has_drawing(para): elem['has_drawing'] = True
        if self._has_formula(para): elem['has_formula'] = True
        if self._get_border(para): elem['has_border'] = True

        if elem['font_name'] and 'courier' in elem['font_name'].lower(): elem['is_code'] = True
        if 'листинг' in style: elem['is_code'] = True

        if text:
            is_h, level = False, None
            if 'heading 1' in style or 'заголовок 1' in style or '1загаловок' in style: is_h, level = True, 1
            elif 'heading 2' in style or 'заголовок 2' in style or '2загаловок' in style: is_h, level = True, 2
            elif 'heading 3' in style or 'заголовок 3' in style or '3загаловок' in style: is_h, level = True, 3
            if is_h:
                elem['is_heading'], elem['heading_level'] = True, level
                number = None
                if level == 1:
                    m = re.match(r'^(\d+)[\.\s]', text)
                    if m: number = m.group(1)
                elif level == 2:
                    m = re.match(r'^(\d+)\.(\d+)', text)
                    if m: number = f'{m.group(1)}.{m.group(2)}'
                    else:
                        app = re.match(r'^Приложение\s+([А-ЯA-Z])', text, re.I)
                        if app: number = app.group(1).upper()
                elif level == 3:
                    m = re.match(r'^(\d+\.\d+\.\d+)', text)
                    if m: number = m.group(1)
                elem['heading_number'] = number

        if text:
            if 'toc' in style or 'content' in style or 'оглавление' in style: elem['is_toc'] = True
            elif re.search(r'\.{2,}\s*\d+$', text) and len(text) < 150 and not any(
                text.startswith(w) for w in ('Таблица','Рисунок','Листинг','Продолжение')): elem['is_toc'] = True

        if text:
            if re.match(r'^(?:Таблица|Продолжение\s+Таблицы)\s+[\dА-ЯA-Z]+\.\d+', text, re.I):
                elem['is_caption'], elem['caption_type'] = True, 'table'
                elem['is_continuation'] = text.startswith('Продолжение')
                m = re.match(r'^(?:Таблица|Продолжение\s+Таблицы)\s+([\dА-ЯA-Z]+)\.(\d+)', text, re.I)
                if m: elem['caption_number'] = f'{m.group(1)}.{m.group(2)}'
            elif re.match(r'^Рис(?:унок|\.)\s+[\dА-ЯA-Z]+\.\d+', text, re.I):
                elem['is_caption'], elem['caption_type'] = True, 'figure'
                m = re.match(r'^Рис(?:унок|\.)\s+([\dА-ЯA-Z]+)\.(\d+)', text, re.I)
                if m: elem['caption_number'] = f'{m.group(1)}.{m.group(2)}'
            elif re.match(r'^Листинг\s+[\dА-ЯA-Z]+\.\d+\s+[—–\-]{1,2}\s+\S', text, re.I):
                elem['is_caption'], elem['caption_type'] = True, 'listing'
                m = re.match(r'^Листинг\s+([\dА-ЯA-Z]+)\.(\d+)', text, re.I)
                if m: elem['caption_number'] = f'{m.group(1)}.{m.group(2)}'

        if text and self._has_list_numbering(para): elem['is_list_item'] = True
        if self._is_inside_table(para): elem['text_category'] = 'table_cell'

    def _has_drawing(self, para):
        try:
            if para._element.findall(f'.//{{{W}}}drawing'): return True
            for run in para.runs:
                if run._element.findall(f'.//{{{W}}}drawing'): return True
        except: pass
        return False

    def _has_formula(self, para):
        try:
            if para._element.findall(f'.//{{{M}}}oMath'): return True
            if para._element.findall(f'.//{{{W}}}object'): return True
        except: pass
        return False

    def _has_list_numbering(self, para):
        try: return para._element.find(f'.//{{{W}}}numPr') is not None
        except: return False

    def _get_border(self, para):
        try:
            ppr = para._element.find(f'{{{W}}}pPr')
            if ppr is not None and ppr.find(f'{{{W}}}pBdr') is not None: return True
        except: pass
        return False

    def _is_inside_table(self, para):
        try:
            parent = para._element.getparent()
            while parent is not None:
                if parent.tag.endswith('}tc'): return True
                parent = parent.getparent()
        except: pass
        return False

    def _link(self):
        caps = [e for e in self.elements if e['is_caption']]
        tables = [e for e in self.elements if e['is_table']]
        drawings = [e for e in self.elements if e['has_drawing']]
        codes = [e for e in self.elements if e['is_code']]

        for cap in caps:
            cap_idx = cap['index']; cap_type = cap['caption_type']
            if cap_type == 'table':
                for t in tables:
                    if 0 < t['index'] - cap_idx <= 5:
                        cap['linked_to'] = t['id']; t['linked_from'] = cap['id']; break
            elif cap_type == 'figure':
                for d in sorted(drawings, key=lambda x: abs(x['index'] - cap_idx)):
                    if -3 <= d['index'] - cap_idx <= 0:
                        cap['linked_to'] = d['id']; d['linked_from'] = cap['id']; break
            elif cap_type == 'listing':
                refs = []
                for c in codes:
                    if 0 < c['index'] - cap_idx <= 100: refs.append(c['id'])
                    elif c['index'] - cap_idx > 100: break
                if refs: cap['code_refs'] = refs

    def _categorize_text(self):
        used = set()
        biblio_idx = -1
        appendix_idx = -1
        for e in self.elements:
            if e['is_heading'] or e['is_caption'] or e['is_list_item'] or e['is_code'] or e['has_drawing'] or e['has_formula']:
                used.add(e['index'])
            if e['text'].upper() == 'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ' and biblio_idx < 0:
                biblio_idx = e['index']
            if appendix_idx < 0 and e['is_heading'] and re.match(r'^Приложени[еяю]\s+[А-ЯA-Z]', e['text'], re.I):
                appendix_idx = e['index']
        for e in self.elements:
            if e['is_table'] or e['text_category'] == 'table_cell': continue
            if e['index'] in used: continue
            if not e['text']: continue
            if biblio_idx >= 0 and e['index'] > biblio_idx:
                e['text_category'] = 'bibliography'
            elif appendix_idx >= 0 and e['index'] > appendix_idx:
                e['text_category'] = 'appendix'
            else:
                e['text_category'] = 'main'

    def _find_heading_index(self, text_upper):
        for e in self.elements:
            if e['is_heading'] and e['text'].upper() == text_upper: return e['index']
        return -1

    def _extract_page_setup(self, doc):
        secs = []
        for sec in doc.sections:
            try:
                pr = sec._sectPr
                pm = pr.find(f'.//{{{W}}}pgMar'); ps = pr.find(f'.//{{{W}}}pgSz')
                def tw(v):
                    try: return float(v)*25.4/1440.0
                    except: return 0.0
                margins = {}
                if pm is not None:
                    for side in ('top','bottom','left','right'): margins[side] = tw(pm.get(f'{{{W}}}{side}','0'))
                w = tw(ps.get(f'{{{W}}}w','0')) if ps else 0
                h = tw(ps.get(f'{{{W}}}h','0')) if ps else 0
                orient = 'landscape' if w>h else 'portrait'
                secs.append({'margins':margins, 'width':w, 'height':h, 'orientation':orient})
            except: pass
        return secs

    def render_structure_html(self):
        html = '''
        <div class="structure-toggle" onclick="var d=document.getElementById('structure-detail');d.classList.toggle('hidden');this.querySelector('span').textContent=d.classList.contains('hidden')?'Показать':'Скрыть';">
            <span style="cursor:pointer;color:#5b7fff;font-weight:500;font-size:0.95em;">Показать</span> структуру документа
        </div>
        <div id="structure-detail" class="hidden">
        <div class="structure-summary"><h3>Структура документа</h3><p class="structure-hint">Все найденные объекты и связи между ними.</p>'''
        html += f'<div class="structure-section"><h4>Таблицы ({len(self.tables)})</h4>'
        if self.tables:
            html += '<table class="struct-table"><thead><tr><th>№</th><th>Подпись</th><th>Размер</th><th>Связь</th></tr></thead><tbody>'
            for i, t in enumerate(self.tables, 1):
                cap = self._find_by_id(t['linked_from']) if t.get('linked_from') else None
                cap_text = cap['text'][:80] if cap else '<span class="missing">НЕТ ПОДПИСИ</span>'
                link = '<span class="ok">связана</span>' if cap else '<span class="missing">нет</span>'
                html += f'<tr><td>{i}</td><td>{cap_text}</td><td>{t["rows_count"]}x{t["cols_count"]}</td><td>{link}</td></tr>'
            html += '</tbody></table>'
        html += '</div>'
        html += f'<div class="structure-section"><h4>Рисунки ({len(self.drawings)})</h4>'
        if self.drawings:
            html += '<table class="struct-table"><thead><tr><th>№</th><th>Подпись</th><th>Связь</th></tr></thead><tbody>'
            for i, d in enumerate(self.drawings, 1):
                cap = self._find_by_id(d['linked_from']) if d.get('linked_from') else None
                cap_text = cap['text'][:80] if cap else '<span class="missing">НЕТ ПОДПИСИ</span>'
                link = '<span class="ok">связан</span>' if cap else '<span class="missing">нет</span>'
                html += f'<tr><td>{i}</td><td>{cap_text}</td><td>{link}</td></tr>'
            html += '</tbody></table>'
        html += '</div>'
        tc = [c for c in self.captions if c['caption_type']=='table']
        html += f'<div class="structure-section"><h4>Подписи к таблицам ({len(tc)})</h4>'
        if tc:
            html += '<table class="struct-table"><thead><tr><th>№</th><th>Текст</th><th>Связь</th></tr></thead><tbody>'
            for i, c in enumerate(tc, 1):
                link = '<span class="ok">связана с таблицей</span>' if c.get('linked_to') else '<span class="missing">НЕТ ТАБЛИЦЫ</span>'
                html += f'<tr><td>{i}</td><td>{c["text"][:80]}</td><td>{link}</td></tr>'
            html += '</tbody></table>'
        html += '</div>'
        fc = [c for c in self.captions if c['caption_type']=='figure']
        html += f'<div class="structure-section"><h4>Подписи к рисункам ({len(fc)})</h4>'
        if fc:
            html += '<table class="struct-table"><thead><tr><th>№</th><th>Текст</th><th>Связь</th></tr></thead><tbody>'
            for i, c in enumerate(fc, 1):
                link = '<span class="ok">связана с рисунком</span>' if c.get('linked_to') else '<span class="missing">НЕТ РИСУНКА</span>'
                html += f'<tr><td>{i}</td><td>{c["text"][:80]}</td><td>{link}</td></tr>'
            html += '</tbody></table>'
        html += '</div>'
        lc = [c for c in self.captions if c['caption_type']=='listing']
        html += f'<div class="structure-section"><h4>Листинги ({len(lc)})</h4>'
        if lc:
            html += '<table class="struct-table"><thead><tr><th>№</th><th>Подпись</th><th>Строк кода</th><th>Рамка</th><th>Связь</th></tr></thead><tbody>'
            for i, c in enumerate(lc, 1):
                code_count = len(c.get('code_refs', []))
                has_border = False
                if c.get('code_refs'):
                    first = self._find_by_id(c['code_refs'][0])
                    if first and first.get('has_border'): has_border = True
                border_str = '<span class="ok">есть</span>' if has_border else '<span class="missing">нет</span>'
                link = '<span class="ok">связан с кодом</span>' if c.get('code_refs') else '<span class="missing">НЕТ КОДА</span>'
                html += f'<tr><td>{i}</td><td>{c["text"][:80]}</td><td>{code_count}</td><td>{border_str}</td><td>{link}</td></tr>'
            html += '</tbody></table>'
        html += '</div>'
        html += f'<div class="structure-section"><h4>Заголовки ({len(self.headings)})</h4>'
        if self.headings:
            html += '<table class="struct-table"><thead><tr><th>№</th><th>Уровень</th><th>Текст</th></tr></thead><tbody>'
            for i, h in enumerate(self.headings, 1): html += f'<tr><td>{i}</td><td>{h["heading_level"]}</td><td>{h["text"][:100]}</td></tr>'
            html += '</tbody></table>'
        html += '</div>'
        groups = []
        if self.list_items:
            cur = [self.list_items[0]]
            for i in range(1, len(self.list_items)):
                if self.list_items[i]['index'] == cur[-1]['index'] + 1: cur.append(self.list_items[i])
                else: groups.append(cur); cur = [self.list_items[i]]
            groups.append(cur)
        html += f'<div class="structure-section"><h4>Списки ({len(groups)} групп)</h4>'
        if groups:
            html += '<table class="struct-table"><thead><tr><th>№</th><th>Элементов</th><th>Первый элемент</th></tr></thead><tbody>'
            for i, g in enumerate(groups, 1): html += f'<tr><td>{i}</td><td>{len(g)}</td><td>{g[0]["text"][:80]}</td></tr>'
            html += '</tbody></table>'
        html += '</div>'
        html += f'<div class="structure-section"><h4>Формулы ({len(self.formulas)})</h4>'
        html += f'<div class="structure-section"><h4>Основной текст ({len(self.main_text)} абзацев)</h4></div>'
        html += '</div>'   
        html += '</div>'   
        html += '</div>'   
        html += '''<style>
            .structure-toggle{margin:16px 0;padding:10px 16px;background:#f7fafc;border:1px solid #e2e8f0;border-radius:8px;user-select:none;}
            .hidden{display:none;}
            .structure-summary{background:#fafbfc;padding:20px 24px;margin:12px 0 20px 0;border-radius:10px;border:1px solid #e1e5e9;font-family:'Segoe UI',system-ui,sans-serif;}
            .structure-summary h3{margin:0 0 4px 0;color:#1a202c;font-size:1.2em;font-weight:600;}
            .structure-hint{color:#718096;font-size:.85em;margin-bottom:16px;}
            .structure-section{margin:16px 0;}
            .structure-section h4{margin:0 0 8px 0;color:#4a5568;font-size:1em;font-weight:600;}
            .struct-table{width:100%;border-collapse:collapse;background:#fff;border-radius:6px;overflow:hidden;border:1px solid #e2e8f0;}
            .struct-table th{background:#f7fafc;padding:8px 12px;text-align:left;font-size:.8em;font-weight:600;color:#718096;text-transform:uppercase;letter-spacing:.5px;border-bottom:2px solid #e2e8f0;}
            .struct-table td{padding:8px 12px;font-size:.85em;color:#2d3748;border-bottom:1px solid #edf2f7;}
            .struct-table tr:last-child td{border-bottom:none;}
            .ok{color:#1a7a2e;font-weight:500;}.missing{color:#c0392b;font-weight:600;}
            </style>'''
        return html

    def _find_by_id(self, eid):
        for e in self.elements:
            if e['id'] == eid: return e
        return None

    def _pt(self, v):
        try: return float(v.pt) if v else None
        except: return None
    def _cm(self, v):
        try: return float(v.cm) if v else None
        except: return None
    def _ls(self, v):
        if v is None: return None
        if hasattr(v,'pt'):
            try: return f"fixed_{v.pt:.0f}pt"
            except: return None
        try: return float(v)
        except: return None