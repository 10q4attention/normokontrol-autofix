from docx import Document
from document_model import DocumentModel
from rules.document_loader import safe_load_document

doc_path = input("Путь к файлу DOCX: ").strip()

doc, error = safe_load_document(doc_path)
if error:
    print(f"Ошибка: {error}")
    exit()

metadata = {'file_path': doc_path, 'file_name': 'test.docx', 'folder_path': '.'}
model = DocumentModel(doc_path, metadata, doc)

print("=== ТАБЛИЦЫ ===")
for t in model.tables:
    cap = None
    if t.get('linked_from'):
        cap = next((c for c in model.captions if c.get('linked_to') == t['id']), None)
    cap_text = cap['text'][:60] if cap else 'БЕЗ ПОДПИСИ'
    print(f"  {cap_text}")
print()

print("=== РИСУНКИ ===")
for d in model.drawings:
    cap = None
    if d.get('linked_from'):
        cap = next((c for c in model.captions if c.get('linked_to') == d['id']), None)
    cap_text = cap['text'][:60] if cap else 'БЕЗ ПОДПИСИ'
    print(f"  {cap_text}")
print()

print("=== ЛИСТИНГИ (подписи) ===")
for c in model.captions:
    if c['caption_type'] == 'listing':
        print(f"  {c['text'][:60]}")
print()

print("=== ФОРМУЛЫ ===")
for f in model.formulas:
    num = f"({f.get('section','?')}.{f.get('number','?')})" if f.get('section') else 'без номера'
    print(f"  {num}: {f['text'][:50]}")
print()

print(f"=== BODY TEXT (первые 200 символов) ===")
print(f"  {model.body_text[:200]}...")
print(f"  Всего символов: {len(model.body_text)}")
print()

# Проверяем конкретный поиск ссылки
import re
print("=== ПОИСК ССЫЛОК НА ТАБЛИЦЫ ===")
found_tables = re.findall(r'[Тт]аблиц(?:а|ы|е|у|ей|ам|ами|ах)\s+([\dА-ЯA-Z]+)\.(\d+)', model.body_text)
print(f"  Найдено ссылок на таблицы в тексте: {len(found_tables)}")
for ft in found_tables[:5]:
    print(f"    Таблица {ft[0]}.{ft[1]}")

print("\n=== ПОИСК ССЫЛОК НА РИСУНКИ ===")
found_figures = re.findall(r'[Рр]исун(?:ок|ка|ку|ком|ке|ки|ков|кам|ками|ках)?\s+([\dА-ЯA-Z]+)\.(\d+)', model.body_text)
print(f"  Найдено ссылок на рисунки в тексте: {len(found_figures)}")
for ff in found_figures[:5]:
    print(f"    Рисунок {ff[0]}.{ff[1]}")

print("\n=== ПОИСК ССЫЛОК НА ЛИСТИНГИ ===")
found_listings = re.findall(r'[Лл]истинг(?:а|у|ом|е|и|ов|ам|ами|ах)?\s+([\dА-ЯA-Z]+)\.(\d+)', model.body_text)
print(f"  Найдено ссылок на листинги в тексте: {len(found_listings)}")
for fl in found_listings[:5]:
    print(f"    Листинг {fl[0]}.{fl[1]}")

print("\n=== ПОИСК ССЫЛОК НА ФОРМУЛЫ ===")
found_formulas = re.findall(r'формул[аыеойамих]*\s*\(?\s*(\d+)\.(\d+)\s*\)?', model.body_text, re.I)
print(f"  Найдено ссылок на формулы в тексте: {len(found_formulas)}")
for ff in found_formulas[:5]:
    print(f"    Формула ({ff[0]}.{ff[1]})")