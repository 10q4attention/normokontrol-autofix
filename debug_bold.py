from docx import Document
from lxml import etree

doc_path = input("Путь к файлу DOCX: ").strip()
doc = Document(doc_path)

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

print("=== ВСЕ ЭЛЕМЕНТЫ СПИСКОВ (numPr) ===\n")

for i, para in enumerate(doc.paragraphs):
    numPr = para._element.find(f'.//{{{W}}}numPr')
    if numPr is None:
        continue
    
    text = para.text.strip()[:80]
    style = para.style.name if para.style and para.style.name else 'None'
    numId_el = numPr.find(f'{{{W}}}numId')
    ilvl_el = numPr.find(f'{{{W}}}ilvl')
    numId = numId_el.get(f'{{{W}}}val') if numId_el is not None else '?'
    ilvl = ilvl_el.get(f'{{{W}}}val') if ilvl_el is not None else '0'

    # Маркер из numbering.xml
    marker = None
    numFmt = None
    lvlText_val = None
    try:
        numbering = doc._element.find(f'{{{W}}}numbering')
        if numbering is not None:
            for num in numbering.findall(f'{{{W}}}num'):
                if num.get(f'{{{W}}}numId') == numId:
                    lvl = num.find(f'{{{W}}}lvl[@w:ilvl="{ilvl}"]')
                    if lvl is None:
                        lvl = num.find(f'{{{W}}}lvl')
                    if lvl is not None:
                        nf = lvl.find(f'{{{W}}}numFmt')
                        if nf is not None:
                            numFmt = nf.get(f'{{{W}}}val')
                        lt = lvl.find(f'{{{W}}}lvlText')
                        if lt is not None:
                            lvlText_val = lt.get(f'{{{W}}}val')
                        if numFmt == 'bullet':
                            marker = lvlText_val
                        elif numFmt == 'decimal':
                            marker = 'decimal'
                        else:
                            marker = numFmt
                    break
    except: pass

    # Отступы
    pf = para.paragraph_format
    left_cm = pf.left_indent.cm if pf.left_indent else None
    first_cm = pf.first_line_indent.cm if pf.first_line_indent else None

    # XML отступы
    xml_left = None
    xml_first = None
    try:
        ppr = para._element.find(f'{{{W}}}pPr')
        if ppr is not None:
            ind = ppr.find(f'{{{W}}}ind')
            if ind is not None:
                v = ind.get(f'{{{W}}}left')
                if v: xml_left = int(v) / 360000.0
                v = ind.get(f'{{{W}}}firstLine')
                if v: xml_first = int(v) / 360000.0
    except: pass

    print(f"Параграф {i}: '{text}'")
    print(f"  Стиль: {style}")
    print(f"  numId={numId}, ilvl={ilvl}")
    print(f"  numFmt={numFmt}, marker='{marker}' (lvlText='{lvlText_val}')")
    print(f"  Отступ слева (direct): {left_cm}")
    print(f"  Отступ первой строки (direct): {first_cm}")
    print(f"  Отступ слева (XML): {xml_left}")
    print(f"  Отступ первой строки (XML): {xml_first}")
    print()

print("Готово.")