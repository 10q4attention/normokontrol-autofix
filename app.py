import os, threading
from flask import Flask, render_template, request, jsonify
from config import Config
from report_builder import ReportBuilder
from loader import RuleLoader
from fixer_runner import fix_file, fix_student_folder
from file_manager import FileManager

app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

rules_loader = RuleLoader()
progress_data = {'completed': 0, 'total': 0, 'running': False}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/scan', methods=['POST'])
def scan_folder():
    global progress_data
    data = request.json
    folder_path = data.get('folder_path', '')
    if not folder_path or not os.path.exists(folder_path):
        return jsonify({'error': 'Папка не существует'}), 400

    from file_manager import FileManager
    fm = FileManager()
    folders = fm.scan_folders(folder_path)
    progress_data = {'completed': 0, 'total': len(folders), 'running': True}

    builder = ReportBuilder()
    reports_container = []

    def run():
        def cb(completed, total):
            progress_data.update({'completed': completed, 'total': total})
        result = builder.process_all(folder_path, cb)
        reports_container.extend(result)
        progress_data['running'] = False

    thread = threading.Thread(target=run)
    thread.start()
    thread.join()

    response = []
    for report in reports_container:
        student = {
            'student_name': report['student_name'],
            'overall_status': report['overall_status'],
            'metadata': report['metadata'],
            'rules': [],
            'error_message': report.get('error_message', '')
        }
        for rd in report.get('rules_results', {}).values():
            student['rules'].append({
                'name': rd['name'],
                'status': rd['status'],
                'summary': rd['summary'],
                'html_row': rd['html_row']
            })
        rp = os.path.join(report['folder_path'], 'normocontrol_report.html')
        student['report_url'] = f'/view-report?path={rp}'
        response.append(student)
    return jsonify(response)


@app.route('/api/progress')
def get_progress():
    return jsonify(progress_data)


@app.route('/view-report')
def view_report():
    rp = request.args.get('path', '')
    if not os.path.exists(rp):
        return "Отчёт не найден", 404
    with open(rp, 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/api/fix', methods=['POST'])
def fix_folder():
    """
    Принимает folder_path или file_path.
    - file_path: исправляет конкретный .docx
    - folder_path: сканирует подпапки студентов и исправляет каждый
    """
    data = request.json or {}
    file_path = data.get('file_path', '').strip()
    folder_path = data.get('folder_path', '').strip()

    if file_path:
        if not os.path.exists(file_path):
            return jsonify({'error': 'Файл не найден'}), 400
        result = fix_file(file_path)
        return jsonify([result])

    if folder_path:
        if not os.path.exists(folder_path):
            return jsonify({'error': 'Папка не найдена'}), 400
        fm = FileManager()
        folders = fm.scan_folders(folder_path)
        # Если подпапок нет — пробуем сам folder_path как папку с одним docx
        if not folders:
            result = fix_student_folder(folder_path)
            return jsonify([result])
        results = []
        for sf in folders:
            results.append(fix_student_folder(sf.path))
        return jsonify(results)

    return jsonify({'error': 'Укажите file_path или folder_path'}), 400


@app.route('/api/reload-rules', methods=['POST'])
def reload_rules():
    try:
        rules_loader.reload()
        return jsonify({
            'status': 'success',
            'rules_count': len(rules_loader.get_rules()),
            'rules': [{'id': r.rule_id, 'name': r.name} for r in rules_loader.get_rules()]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    print(f"Загружено правил: {len(rules_loader.get_rules())}")
    for r in rules_loader.get_rules():
        print(f"  - {r.name}")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)