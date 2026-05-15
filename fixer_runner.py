"""Запускает все фиксеры на одном .docx-файле."""

import shutil
import glob
import os
from datetime import datetime
from pathlib import Path
from docx import Document
from document_model import DocumentModel
from fixers.fixer_loader import FixerLoader

_loader = FixerLoader()


def fix_file(file_path: str) -> dict:
    """
    Создаёт резервную копию, запускает фиксеры, сохраняет исправленный файл.
    Возвращает словарь с результатами.
    """
    path = Path(file_path)
    if not path.exists():
        return {'status': 'error', 'error': f'Файл не найден: {file_path}'}

    # Резервная копия
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = path.with_name(f'{path.stem}_backup_{stamp}.docx')
    shutil.copy2(path, backup)

    try:
        doc = Document(str(path))
    except Exception as e:
        return {'status': 'error', 'error': f'Не удалось открыть файл: {e}', 'backup': str(backup)}

    metadata = {
        'exists': True,
        'file_path': str(path),
        'file_name': path.name,
        'folder_path': str(path.parent),
    }
    try:
        model = DocumentModel(str(path), metadata, doc)
    except Exception as e:
        return {'status': 'error', 'error': f'Ошибка модели: {e}', 'backup': str(backup)}

    results = []
    for fixer in _loader.get_fixers():
        try:
            res = fixer.fix(doc, model)
            results.append({
                'fixer_id': res.fixer_id,
                'name': res.name,
                'status': res.status,
                'changes': res.changes,
                'error': res.error,
            })
        except Exception as e:
            results.append({
                'fixer_id': fixer.fixer_id,
                'name': fixer.name,
                'status': 'error',
                'changes': [],
                'error': str(e),
            })

    doc.save(str(path))

    total_changes = sum(len(r['changes']) for r in results)
    return {
        'status': 'ok',
        'file_path': str(path),
        'backup_path': str(backup),
        'results': results,
        'total_changes': total_changes,
    }


def fix_student_folder(folder_path: str) -> dict:
    """
    Находит последний .docx в папке и запускает fix_file.
    Аналог worker.process_one, но для исправления.
    """
    docs = []
    for pat in ('*.docx', '*.doc'):
        docs.extend(glob.glob(os.path.join(folder_path, pat)))
    if not docs:
        return {
            'status': 'error',
            'error': 'Файл DOCX не найден',
            'folder_path': folder_path,
            'student_name': os.path.basename(folder_path),
        }

    docs.sort(key=os.path.getmtime, reverse=True)
    result = fix_file(docs[0])
    result['student_name'] = os.path.basename(folder_path)
    result['folder_path'] = folder_path
    return result
