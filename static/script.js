document.addEventListener('DOMContentLoaded', () => {
    const scanBtn = document.getElementById('scan-btn');
    const reloadBtn = document.getElementById('reload-rules-btn');
    const folderPathInput = document.getElementById('folder-path');
    const resultsTable = document.getElementById('results-table');
    const tableBody = document.getElementById('table-body');
    const loadingDiv = document.getElementById('loading');
    const statusMessage = document.getElementById('status-message');
    const statsBar = document.getElementById('stats-bar');
    const filtersDiv = document.querySelector('.filters');
    const filterStudent = document.getElementById('filter-student');
    const filterStatus = document.getElementById('filter-status');

    let allReports = [];

    scanBtn.addEventListener('click', scanFolder);
    reloadBtn.addEventListener('click', reloadRules);
    folderPathInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') scanFolder(); });
    filterStudent.addEventListener('change', applyFilters);
    filterStatus.addEventListener('change', applyFilters);

    async function scanFolder() {
        const folderPath = folderPathInput.value.trim();
        if (!folderPath) {
            showMessage('Укажите путь к папке с работами', 'error');
            return;
        }

        loadingDiv.style.display = 'block';
        loadingDiv.textContent = 'Выполняется проверка...';
        resultsTable.style.display = 'none';
        statsBar.style.display = 'none';
        filtersDiv.style.display = 'none';
        tableBody.innerHTML = '';
        statusMessage.innerHTML = '';
        allReports = [];

        try {
            // Запускаем сканирование и прогресс параллельно
            const scanPromise = fetch('/api/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder_path: folderPath })
            });

            const progressInterval = setInterval(async () => {
                try {
                    const resp = await fetch('/api/progress');
                    const prog = await resp.json();
                    if (prog.total > 0) {
                        loadingDiv.textContent = `Выполняется проверка... ${prog.completed}/${prog.total}`;
                    }
                } catch {}
            }, 300);

            const response = await scanPromise;
            clearInterval(progressInterval);

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Ошибка сканирования');
            }

            allReports = await response.json();
            populateStudentFilter();
            applyFilters();
            updateStats();
            filtersDiv.style.display = 'flex';
            showMessage(`Проверка завершена. Обработано студентов: ${allReports.length}`, 'success');

        } catch (error) {
            showMessage(error.message, 'error');
        } finally {
            loadingDiv.style.display = 'none';
        }
    }

    function populateStudentFilter() {
        filterStudent.innerHTML = '<option value="all">Все</option>';
        allReports.forEach((r, i) => {
            const opt = document.createElement('option');
            opt.value = i;
            opt.textContent = r.student_name;
            filterStudent.appendChild(opt);
        });
    }

    function applyFilters() {
        let filtered = allReports;
        if (filterStudent.value !== 'all') filtered = [allReports[parseInt(filterStudent.value)]];
        if (filterStatus.value !== 'all') filtered = filtered.filter(r => r.overall_status === filterStatus.value);
        renderTable(filtered);
        updateStats(filtered);
    }

    function updateStats(filtered = null) {
        const data = filtered || allReports;
        const total = data.length;
        const passed = data.filter(r => r.overall_status === 'pass').length;
        const failed = data.filter(r => r.overall_status === 'fail').length;
        const errors = data.filter(r => r.overall_status === 'error').length;
        statsBar.innerHTML = `<span>Всего: ${total}</span><span>Пройдено: ${passed}</span><span>Не пройдено: ${failed}</span><span>Ошибок: ${errors}</span>`;
        statsBar.style.display = 'block';
    }

    function renderTable(reports) {
        tableBody.innerHTML = '';
        if (reports.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:40px;">Нет данных для отображения</td></tr>';
            resultsTable.style.display = 'table';
            return;
        }
        reports.forEach((student) => {
            const row = document.createElement('tr');
            row.className = 'row-toggle';
            const nameCell = document.createElement('td');
            nameCell.textContent = student.student_name;
            row.appendChild(nameCell);
            const statusCell = document.createElement('td');
            const badge = document.createElement('span');
            badge.className = `badge badge-${student.overall_status}`;
            badge.textContent = student.overall_status === 'pass' ? 'Пройдено' : student.overall_status === 'fail' ? 'Не пройдено' : 'Ошибка';
            statusCell.appendChild(badge);
            row.appendChild(statusCell);
            const fileCell = document.createElement('td');
            fileCell.textContent = student.metadata && student.metadata.exists ? student.metadata.file_name || 'Файл найден' : '—';
            row.appendChild(fileCell);
            const reportCell = document.createElement('td');
            if (student.report_url) {
                const link = document.createElement('a');
                link.href = student.report_url;
                link.target = '_blank';
                link.className = 'report-link';
                link.textContent = 'Открыть отчёт';
                link.addEventListener('click', (e) => e.stopPropagation());
                reportCell.appendChild(link);
            } else {
                reportCell.textContent = '—';
            }
            row.appendChild(reportCell);
            row.addEventListener('click', () => toggleRulesRow(row, student));
            tableBody.appendChild(row);
        });
        resultsTable.style.display = 'table';
    }

    function toggleRulesRow(row, student) {
        const existing = row.nextElementSibling;
        if (existing && existing.classList.contains('rules-detail-row')) {
            existing.remove();
            return;
        }
        const detailRow = document.createElement('tr');
        detailRow.className = 'rules-detail-row';
        const detailCell = document.createElement('td');
        detailCell.colSpan = 4;
        const passedCount = student.rules.filter(r => r.status === 'pass').length;
        let html = '<div class="rules-container">';
        html += `<div class="rules-header">Правила проверки (${passedCount}/${student.rules.length} пройдено)</div>`;
        student.rules.forEach(rule => { html += rule.html_row; });
        if (student.error_message) {
            html += `<div class="rule-row status-error"><span class="rule-name">Ошибка</span><span class="rule-summary">${student.error_message}</span></div>`;
        }
        html += '</div>';
        detailCell.innerHTML = html;
        detailRow.appendChild(detailCell);
        row.parentNode.insertBefore(detailRow, row.nextSibling);
    }

    async function reloadRules() {
        try {
            const response = await fetch('/api/reload-rules', { method: 'POST' });
            const data = await response.json();
            showMessage(data.status === 'success' ? `Правила обновлены. Загружено: ${data.rules_count}` : data.message, data.status);
        } catch { showMessage('Ошибка обновления правил', 'error'); }
    }

    function showMessage(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = type === 'success' ? 'status-success' : 'status-error';
    }
});