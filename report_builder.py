import os, json
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ProcessPoolExecutor, as_completed
from worker import process_one
from file_manager import FileManager


class ReportBuilder:
    def __init__(self, output_dir: str = 'reports'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def process_all(self, root_path: str, progress_callback=None) -> List[Dict[str, Any]]:
        fm = FileManager()
        folders = fm.scan_folders(root_path)
        if not folders:
            return []
        paths = [f.path for f in folders]
        reports = []
        done = 0
        with ProcessPoolExecutor() as ex:
            futures = {ex.submit(process_one, p): p for p in paths}
            for future in as_completed(futures):
                try:
                    reports.append(future.result())
                except Exception as e:
                    path = futures[future]
                    reports.append({
                        'student_name': os.path.basename(path),
                        'folder_path': path,
                        'metadata': {'exists': False},
                        'rules_results': {},
                        'overall_status': 'error',
                        'error_message': str(e),
                        'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                done += 1
                if progress_callback:
                    progress_callback(done, len(paths))
        reports.sort(key=lambda r: r['student_name'])
        for r in reports:
            self._save(r)
        return reports

    def _save(self, report):
        folder = report.get('folder_path', '')
        if not folder:
            return
        jp = os.path.join(folder, 'normocontrol_report.json')
        with open(jp, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        hp = os.path.join(folder, 'normocontrol_report.html')
        with open(hp, 'w', encoding='utf-8') as f:
            f.write(self._html(report))

    def _html(self, report):
        passed, failed = [], []
        for rd in report.get('rules_results', {}).values():
            (passed if rd.get('status') == 'pass' else failed).append(rd)
        ov = report.get('overall_status', 'error')
        st = 'Пройдено' if ov == 'pass' else 'Не пройдено' if ov == 'fail' else 'Ошибка'
        h = f'''<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><title>Нормоконтроль: {report.get('student_name','?')}</title>
<style>body{{font-family:'Times New Roman',serif;max-width:900px;margin:40px auto;padding:0 20px;color:#1a1a1a;background:#fcfcfc;}}
h1{{border-bottom:2px solid #2c3e50;padding-bottom:10px;}}h2{{color:#2c3e50;}}
.metadata-table{{width:100%;border-collapse:collapse;margin:20px 0;background:#fff;}}
.metadata-table td{{padding:8px 12px;border:1px solid #dee2e6;}}
.metadata-table td:first-child{{background:#f8f9fa;font-weight:600;width:30%;}}
.overall-status{{display:inline-block;padding:6px 16px;font-weight:600;font-size:1.1em;}}
.overall-pass{{color:#1a7a2e;}}.overall-fail{{color:#c0392b;}}.overall-error{{color:#7f8c8d;}}
.rule-block{{margin:16px 0;padding:16px;background:#fff;border-left:4px solid #bdc3c7;}}
.rule-block.status-pass{{border-left-color:#27ae60;}}.rule-block.status-fail{{border-left-color:#c0392b;}}.rule-block.status-error{{border-left-color:#95a5a6;}}
.rule-detail{{margin:8px 0;padding:8px 12px;background:#f8f9fa;}}.rule-details{{margin:8px 0;padding:8px 12px;background:#fdf2f2;}}
.rule-details ul{{margin:5px 0;padding-left:20px;}}.rule-details li{{margin:5px 0;}}
.passed-list{{display:flex;flex-wrap:wrap;gap:8px;}}.passed-item{{padding:4px 12px;background:#e8f5e9;color:#1a7a2e;font-size:.95em;}}
.timestamp{{color:#7f8c8d;font-size:.9em;}}</style></head><body>
<h1>Отчёт нормоконтроля</h1><h2>{report.get('student_name','?')}</h2>
<p class="timestamp">Дата проверки: {report.get('processed_at','?')}</p>
<div class="overall-status overall-{ov}">Общий статус: {st}</div>
<h3>Метаданные файла</h3><table class="metadata-table">'''
        meta = report.get('metadata', {})
        if meta.get('exists'):
            h += f"<tr><td>Имя файла</td><td>{meta.get('file_name','—')}</td></tr>"
            h += f"<tr><td>Дата изменения</td><td>{meta.get('file_modified','—')}</td></tr>"
            h += f"<tr><td>Размер</td><td>{meta.get('file_size',0)//1024} КБ</td></tr>"
            h += f"<tr><td>Автор</td><td>{meta.get('doc_author','—')}</td></tr>"
            h += f"<tr><td>Название</td><td>{meta.get('doc_title','—')}</td></tr>"
        else:
            h += "<tr><td colspan='2'>Файл не найден</td></tr>"
        h += '</table>'
        h += report.get('structure_html', '')
        if report.get('error_message'):
            h += f"<p><strong>Ошибка:</strong> {report['error_message']}</p>"
        if passed:
            h += '<h3>Пройденные проверки</h3><div class="passed-list">' + ''.join(f'<span class="passed-item">{p.get("name","?")}</span>' for p in passed) + '</div>'
        if failed:
            h += '<h3>Не пройденные проверки</h3>'
            for f in failed:
                h += f'<div class="rule-block status-{f.get("status","error")}"><h3>{f.get("name","?")}</h3><p>{f.get("description","")}</p>'
                if f.get('received'): h += f'<div class="rule-detail"><strong>Полученные данные:</strong> {f["received"]}</div>'
                if f.get('expected'): h += f'<div class="rule-detail"><strong>Ожидаемый результат:</strong> {f["expected"]}</div>'
                if f.get('details'): h += '<div class="rule-details"><strong>Нарушения:</strong><ul>' + ''.join(f'<li>{d}</li>' for d in f['details']) + '</ul></div>'
                h += '</div>'
        h += '</body></html>'
        return h