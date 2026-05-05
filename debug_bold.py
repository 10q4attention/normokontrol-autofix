from docx import Document
from lxml import etree
import zipfile

doc_path = input("Путь к файлу DOCX: ").strip()
doc = Document(doc_path)

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

# Читаем styles.xml напрямую из архива
styles_xml = None
with zipfile.ZipFile(doc_path, 'r') as zf:
    if 'word/styles.xml' in zf.namelist():
        styles_xml = etree.fromstring(zf.read('word/styles.xml'))

if styles_xml is None:
    print("styles.xml не найден в архиве!")
    exit()

# Находим Heading 2
heading2_para = None
for para in doc.paragraphs:
    style = para.style.name if para.style and para.style.name else ''
    if 'Heading 2' in style or 'heading 2' in style.lower():
        heading2_para = para
        break

if heading2_para is None:
    print("Heading 2 не найден")
    exit()

style_elem = heading2_para.style._element
style_id = style_elem.get(f'{{{W}}}styleId')
print(f"Стиль: {heading2_para.style.name}, styleId={style_id}")

# Идём по цепочке
current = style_id
for level in range(5):
    print(f"\nУровень {level}: ищем стиль '{current}'")
    found = False
    for s in styles_xml.findall(f'{{{W}}}style'):
        if s.get(f'{{{W}}}styleId') == current:
            print(f"  Найден!")
            based_on = s.find(f'{{{W}}}basedOn')
            if based_on is not None:
                current = based_on.get(f'{{{W}}}val')
                print(f"  basedOn = {current}")
                found = True
            else:
                print(f"  basedOn отсутствует — конец цепочки")
            rpr = s.find(f'{{{W}}}rPr')
            if rpr is not None:
                b = rpr.find(f'{{{W}}}b')
                if b is not None:
                    val = b.get(f'{{{W}}}val', 'true')
                    print(f"  w:b = {val} -> bold={val not in ('false', '0')}")
                else:
                    print(f"  w:b = НЕТ")
            else:
                print(f"  w:rPr = НЕТ")
            break
    if not found:
        print(f"  Стиль '{current}' НЕ НАЙДЕН в styles.xml!")
        break