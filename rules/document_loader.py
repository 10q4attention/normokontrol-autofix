import os
import zipfile
from docx import Document


def safe_load_document(doc_path: str):
    if not os.path.exists(doc_path):
        return None, f"Файл не найден: {doc_path}"
    ext = os.path.splitext(doc_path)[1].lower()
    if ext not in ('.docx', '.doc'):
        return None, f"Неподдерживаемый формат: {ext}"
    if ext == '.docx':
        try:
            if not zipfile.is_zipfile(doc_path):
                return None, "Файл повреждён или не является DOCX"
        except Exception as e:
            return None, f"Ошибка чтения архива: {e}"
    try:
        return Document(doc_path), None
    except KeyError as e:
        if 'NULL' in str(e):
            return None, "Файл содержит битые ссылки (word/NULL). Сохраните заново в MS Word."
        return None, f"Ошибка структуры: {e}"
    except Exception as e:
        return None, f"Не удалось открыть документ: {e}"