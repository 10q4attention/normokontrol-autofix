"""Воркер для обработки одного студента."""

from datetime import datetime
from file_manager import StudentFolder
from rules.document_loader import safe_load_document
from document_model import DocumentModel
from loader import RuleLoader


def process_one(student_folder_path: str) -> dict:
    folder = StudentFolder(student_folder_path)
    metadata = folder.get_metadata()

    report = {
        'student_name': folder.student_name,
        'folder_path': folder.path,
        'metadata': metadata,
        'rules_results': {},
        'overall_status': 'pass',
        'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'structure_html': ''
    }

    if not metadata.get('exists'):
        report['overall_status'] = 'error'
        report['error_message'] = 'Файл DOC/DOCX не найден в папке студента'
        return report

    doc, load_error = safe_load_document(metadata['file_path'])
    if load_error:
        report['overall_status'] = 'error'
        report['error_message'] = load_error
        return report

    try:
        model = DocumentModel(metadata['file_path'], metadata, doc)
        report['structure_html'] = model.render_structure_html()
    except Exception as e:
        import traceback
        report['overall_status'] = 'error'
        report['error_message'] = f"Ошибка модели: {str(e)}\n{traceback.format_exc()}"
        return report    

    rules_loader = RuleLoader()
    for rule in rules_loader.get_rules():
        try:
            result = rule.check(model)
            report['rules_results'][rule.rule_id] = {
                'name': rule.name,
                'description': rule.description,
                'status': result.status,
                'summary': result.summary,
                'details': result.details,
                'received': result.received,
                'expected': result.expected,
                'metadata': result.metadata,
                'html_row': rule.render_html_row(result),
                'html_full': rule.render_html_full(result)
            }
            if result.status in ('fail', 'error'):
                report['overall_status'] = 'fail'
        except Exception as e:
            report['rules_results'][rule.rule_id] = {
                'name': rule.name,
                'description': rule.description,
                'status': 'error',
                'summary': f'Ошибка: {e}',
                'details': [str(e)],
                'received': '', 'expected': '', 'metadata': {},
                'html_row': f'<div class="rule-row status-error"><span class="rule-name">{rule.name}</span><span class="rule-summary">Ошибка</span></div>',
                'html_full': f'<div class="full-rule-block status-error"><h3>{rule.name}</h3><p>Ошибка: {e}</p></div>'
            }
            report['overall_status'] = 'fail'

    return report