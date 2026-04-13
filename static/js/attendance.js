/**
 * Hour-Wise Attendance Register – BGCGW
 * Handles load, toggle, daily/monthly calculations, save.
 */
(function () {
    'use strict';

    // Cycle: P -> A -> L -> P
    const CYCLE = ['P', 'A', 'L'];

    let state = {
        students: [],
        // key: "roll|YYYY-MM-DD" -> { h1:'A'|'L'|'P', ... h6:... }
        attendance: {},
        month: 1,
        year: 2025,
        semesterNumber: 1,
        dates: []
    };

    const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];

    function pad2(n) { return String(n).padStart(2, '0'); }

    function formatDate(d) {
        return `${pad2(d.getDate())}-${pad2(d.getMonth() + 1)}-${d.getFullYear()}`;
    }

    function isoDate(d) {
        return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
    }

    function getDatesInMonth(month, year) {
        const dates = [];
        const last = new Date(year, month, 0).getDate();
        for (let d = 1; d <= last; d++) {
            dates.push(new Date(year, month - 1, d));
        }
        return dates;
    }

    function initYearSelect() {
        const sel = document.getElementById('yearSelect');
        const y = new Date().getFullYear();
        for (let i = y - 2; i <= y + 2; i++) {
            const opt = document.createElement('option');
            opt.value = i;
            opt.textContent = i;
            if (i === y) opt.selected = true;
            sel.appendChild(opt);
        }
    }

    function initMonthSelect() {
        const m = new Date().getMonth() + 1;
        document.getElementById('monthSelect').value = m;
    }

    function getAttKey(sid, dateStr) {
        return `${sid}|${dateStr}`;
    }

    function getHourKey(hour) {
        return `h${hour}`;
    }

    function getStatus(rollNumber, dateStr, hour) {
        const key = getAttKey(rollNumber, dateStr);
        const hk = getHourKey(hour);
        return (state.attendance[key] && state.attendance[key][hk]) || 'A';
    }

    function setStatus(rollNumber, dateStr, hour, code) {
        const key = getAttKey(rollNumber, dateStr);
        const hk = getHourKey(hour);
        if (!state.attendance[key]) state.attendance[key] = {};
        state.attendance[key][hk] = code;
    }

    function nextStatus(current) {
        const idx = CYCLE.indexOf(current);
        return CYCLE[(idx + 1) % CYCLE.length];
    }

    function dayTotals(rollNumber, dateStr) {
        let p = 0, a = 0, l = 0;
        for (let h = 1; h <= 6; h++) {
            const s = getStatus(rollNumber, dateStr, h);
            if (s === 'P') p++;
            else if (s === 'L') l++;
            else a++;
        }
        return { p, a, l };
    }

    function monthlyTotals(rollNumber) {
        let tp = 0, ta = 0, tl = 0;
        state.dates.forEach(d => {
            const ds = isoDate(d);
            const t = dayTotals(rollNumber, ds);
            tp += t.p;
            ta += t.a;
            tl += t.l;
        });
        return { tp, ta, tl };
    }

    function renderCell(rollNumber, dateStr, hour) {
        const cell = document.createElement('td');
        cell.className = 'hour-cell status-A';
        cell.dataset.roll = rollNumber;
        cell.dataset.date = dateStr;
        cell.dataset.hour = hour;
        cell.textContent = 'A';
        cell.addEventListener('click', () => {
            const cur = getStatus(rollNumber, dateStr, hour);
            const nxt = nextStatus(cur);
            setStatus(rollNumber, dateStr, hour, nxt);
            cell.textContent = nxt;
            cell.className = `hour-cell status-${nxt}`;
            updateDayTotal(rollNumber, dateStr);
            updateMonthlySummary();
        });
        return cell;
    }

    function updateDayTotal(rollNumber, dateStr) {
        const t = dayTotals(rollNumber, dateStr);
        const el = document.querySelector(
            `.day-total-cell[data-roll="${rollNumber}"][data-date="${dateStr}"]`
        );
        if (el) el.textContent = `${t.p}P / ${t.a}A / ${t.l}L`;
    }

    function updateMonthlySummary() {
        const tbody = document.getElementById('summaryBody');
        if (!tbody) return;
        const totalHours = state.dates.length * 6;
        state.students.forEach((s, idx) => {
            const roll = s.roll_number;
            const name = s.student_name || '-';
            const { tp, ta, tl } = monthlyTotals(roll);
            const pct = totalHours > 0 ? Math.round((tp / totalHours) * 100) : 0;
            const eligible = pct >= 75;
            const row = tbody.querySelector(`tr[data-summary-roll="${roll}"]`);
            if (row) {
                row.cells[0].textContent = (idx + 1);
                row.cells[3].textContent = tp;
                row.cells[4].textContent = ta;
                row.cells[5].textContent = tl;
                row.cells[6].textContent = pct + '%';
                const badge = row.cells[7].querySelector('.badge');
                badge.textContent = eligible ? 'Eligible' : 'Not Eligible';
                badge.className = 'badge ' + (eligible ? 'badge-eligible' : 'badge-not-eligible');
            }
        });
    }

    async function saveDateAttendance(dateStr, msgEl, btnEl) {
        const payload = {
            date: dateStr,
            month: monthNames[state.month - 1],
            year: state.year,
            semester_number: state.semesterNumber,
            records: state.students.map(s => {
                const roll = s.roll_number;
                const key = getAttKey(roll, dateStr);
                const rec = state.attendance[key] || {};
                return {
                    roll_number: roll,
                    student_name: s.student_name,
                    h1: rec.h1 || 'A',
                    h2: rec.h2 || 'A',
                    h3: rec.h3 || 'A',
                    h4: rec.h4 || 'A',
                    h5: rec.h5 || 'A',
                    h6: rec.h6 || 'A'
                };
            })
        };

        if (btnEl) {
            btnEl.disabled = true;
            btnEl.textContent = 'Saving…';
        }
        if (msgEl) msgEl.textContent = '';

        try {
            const resp = await fetch(getApiUrls().save, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error || 'Save failed');
            if (msgEl) msgEl.textContent = 'Attendance saved successfully';
        } catch (err) {
            const msg = err.message || 'Could not save attendance';
            if (msgEl) msgEl.textContent = msg;
            alert('Error: ' + msg);
        } finally {
            if (btnEl) {
                btnEl.disabled = false;
                btnEl.textContent = 'Save Attendance';
            }
        }
    }

    function buildGrid() {
        const wrapper = document.getElementById('attendanceGrid');
        wrapper.innerHTML = '';

        if (!state.students.length) {
            wrapper.innerHTML = '<p class="placeholder-text">No students found for this semester.</p>';
            return;
        }

        const frag = document.createDocumentFragment();
        state.dates.forEach(d => {
            const dateStr = isoDate(d);
            const block = document.createElement('div');
            block.className = 'date-block';

            const header = document.createElement('div');
            header.className = 'date-header-row';
            header.textContent = `Date: ${formatDate(d)}`;
            block.appendChild(header);

            const scroll = document.createElement('div');
            scroll.className = 'attendance-scroll';

            const table = document.createElement('table');
            table.className = 'attendance-table';
            table.innerHTML = `
                <thead>
                    <tr>
                        <th class="col-attendance-serial">Attendance ID</th>
                        <th class="col-roll-no">Roll Number</th>
                        <th class="col-student-name">Student Name</th>
                        <th>H1</th><th>H2</th><th>H3</th><th>H4</th><th>H5</th><th>H6</th>
                        <th>Day Total</th>
                    </tr>
                </thead>
                <tbody></tbody>
            `;

            const tbody = table.querySelector('tbody');
            state.students.forEach((s, idx) => {
                const rollNo = s.roll_number;
                const name = s.student_name || '-';
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="col-attendance-serial">${idx + 1}</td>
                    <td class="col-roll-no">${rollNo}</td>
                    <td class="col-student-name">${name}</td>
                `;
                for (let h = 1; h <= 6; h++) {
                    const cell = renderCell(rollNo, dateStr, h);
                    const st = getStatus(rollNo, dateStr, h);
                    cell.textContent = st;
                    cell.className = `hour-cell status-${st}`;
                    tr.appendChild(cell);
                }
                const t = dayTotals(rollNo, dateStr);
                const totCell = document.createElement('td');
                totCell.className = 'day-total-cell';
                totCell.dataset.roll = rollNo;
                totCell.dataset.date = dateStr;
                totCell.textContent = `${t.p}P / ${t.a}A / ${t.l}L`;
                tr.appendChild(totCell);
                tbody.appendChild(tr);
            });

            scroll.appendChild(table);
            block.appendChild(scroll);

            // Per-date save button row
            const saveRow = document.createElement('div');
            saveRow.className = 'date-save-row';
            const msg = document.createElement('div');
            msg.className = 'date-save-msg';
            msg.id = `msg-${dateStr}`;
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn-save';
            btn.textContent = 'Save Attendance';
            btn.addEventListener('click', () => saveDateAttendance(dateStr, msg, btn));
            saveRow.appendChild(msg);
            saveRow.appendChild(btn);
            block.appendChild(saveRow);

            frag.appendChild(block);
        });

        wrapper.appendChild(frag);
    }

    function buildSummary() {
        const wrap = document.getElementById('monthlySummary');
        const tbody = document.getElementById('summaryBody');
        if (!wrap || !tbody) return;

        wrap.style.display = 'block';
        tbody.innerHTML = '';
        const totalHours = state.dates.length * 6;

        state.students.forEach((s, idx) => {
            const rollNo = s.roll_number;
            const name = s.student_name || '-';
            const { tp, ta, tl } = monthlyTotals(rollNo);
            const pct = totalHours > 0 ? Math.round((tp / totalHours) * 100) : 0;
            const eligible = pct >= 75;
            const tr = document.createElement('tr');
            tr.dataset.summaryRoll = rollNo;
            tr.innerHTML = `
                <td>${idx + 1}</td>
                <td>${rollNo}</td>
                <td>${name}</td>
                <td>${tp}</td>
                <td>${ta}</td>
                <td>${tl}</td>
                <td>${pct}%</td>
                <td><span class="badge ${eligible ? 'badge-eligible' : 'badge-not-eligible'}">${eligible ? 'Eligible' : 'Not Eligible'}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }

    function getApiUrls() {
        const el = document.getElementById('attendanceApp') || document.querySelector('[data-api-load]');
        return {
            load: (el && el.dataset.apiLoad) || '/api/attendance/load',
            save: (el && el.dataset.apiSave) || '/api/attendance/save'
        };
    }

    async function loadAttendance() {
        const month = parseInt(document.getElementById('monthSelect').value, 10);
        const year = parseInt(document.getElementById('yearSelect').value, 10);
        const semesterNumber = parseInt(document.getElementById('semesterInput').value, 10) || 1;

        const loadBtn = document.getElementById('loadBtn');
        if (!loadBtn) return;
        loadBtn.disabled = true;
        loadBtn.textContent = 'Loading…';

        const urls = getApiUrls();
        try {
            const resp = await fetch(urls.load, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ month, year, semester_number: semesterNumber })
            });
            let data;
            try {
                data = await resp.json();
            } catch (_) {
                throw new Error(resp.status === 404 ? 'API route not found. Check Flask blueprint registration.' : 'Invalid server response (' + resp.status + ')');
            }

            if (!data.success) throw new Error(data.error || 'Failed to load');

            state.students = (data.students || []).map(s => ({
                roll_number: s.roll_number,
                student_name: s.student_name
            }));
            state.attendance = data.attendance || {};
            state.month = month;
            state.year = year;
            state.semesterNumber = semesterNumber;
            state.dates = getDatesInMonth(month, year);

            const banner = document.getElementById('errorBanner');
            if (banner) banner.style.display = 'none';
            buildGrid();
            buildSummary();
        } catch (err) {
            const msg = err.message || 'Could not load attendance';
            const banner = document.getElementById('errorBanner');
            if (banner) {
                banner.textContent = msg;
                banner.style.display = 'block';
            }
            alert('Error: ' + msg);
        } finally {
            const lb = document.getElementById('loadBtn');
            if (lb) { lb.disabled = false; lb.textContent = 'Load Attendance'; }
        }
    }

    function init() {
        const yearSel = document.getElementById('yearSelect');
        const monthSel = document.getElementById('monthSelect');
        const loadBtn = document.getElementById('loadBtn');
        if (!yearSel || !loadBtn) {
            console.error('Attendance: required elements (yearSelect, loadBtn) not found. Check template.');
            return;
        }
        initYearSelect();
        if (monthSel) initMonthSelect();
        loadBtn.addEventListener('click', loadAttendance);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
