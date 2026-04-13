/**
 * Student Consolidated Report System – BGCGW
 * report.js  –  Edit toggle, live recalc, update submit
 */
(function () {
    'use strict';

    /* ── helpers ──────────────────────────────────────── */
    function $(id)      { return document.getElementById(id); }
    function all(sel)   { return document.querySelectorAll(sel); }

    const root = $('reportApp');
    if (!root) return;

    /* ── button references (top + bottom bar) ─────────── */
    const editBtns   = [].concat(
        Array.from(all('#editReportBtn,  #editReportBtn2')));
    const updateBtns = [].concat(
        Array.from(all('#updateReportBtn, #updateReportBtn2')));
    const updateMsg  = $('updateMsg');
    const updateErr  = $('updateErr');

    /* ── edit-mode toggle ─────────────────────────────── */
    function setEditMode(on) {
        root.classList.toggle('edit-mode', !!on);

        editBtns.forEach(function (b) {
            b.style.display = on ? 'none' : '';
        });
        updateBtns.forEach(function (b) {
            b.style.display = on ? '' : 'none';
        });

        /* Hide feedback when entering edit mode */
        if (on) {
            if (updateMsg) updateMsg.style.display = 'none';
            if (updateErr) updateErr.style.display = 'none';
        }
    }

    editBtns.forEach(function (btn) {
        btn.addEventListener('click', function () { setEditMode(true); });
    });

    /* ── live marks recalc ────────────────────────────── */
    all('#marksBody tr[data-subject-id]').forEach(function (tr) {
        var totalCell = tr.querySelector('.total-cell');
        function recalc() {
            if (!totalCell) return;
            var i = parseInt((tr.querySelector('.mark-internal') || {}).value || '0', 10) || 0;
            var e = parseInt((tr.querySelector('.mark-external') || {}).value || '0', 10) || 0;
            totalCell.textContent = String(i + e);
        }
        var iEl = tr.querySelector('.mark-internal');
        var eEl = tr.querySelector('.mark-external');
        if (iEl) iEl.addEventListener('input', recalc);
        if (eEl) eEl.addEventListener('input', recalc);
    });

    /* ── live photo preview ───────────────────────────── */
    var photoInput   = $('photoInput');
    var photoImg     = $('photoImg');
    var previewBox   = $('photoPreviewBox');

    if (photoInput) {
        photoInput.addEventListener('change', function () {
            var file = photoInput.files && photoInput.files[0];
            if (!file) return;
            var reader = new FileReader();
            reader.onload = function (e) {
                if (photoImg) {
                    photoImg.src = e.target.result;
                } else if (previewBox) {
                    /* First upload – create img element */
                    var img = document.createElement('img');
                    img.id = 'photoImg';
                    img.alt = 'Student Photo';
                    img.src = e.target.result;
                    previewBox.innerHTML = '';
                    previewBox.appendChild(img);
                }
            };
            reader.readAsDataURL(file);
        });
    }

    /* ── submit update ────────────────────────────────── */
    async function submitUpdate() {
        if (updateMsg) updateMsg.style.display = 'none';
        if (updateErr) updateErr.style.display = 'none';

        var studentBiodataId = ($('studentBiodataId') || {}).value || '';
        var originalRollNo   = ($('originalRollNo')   || {}).value || '';
        var targetSemesterId = ($('targetSemesterId') || {}).value || '';

        if (!studentBiodataId && !originalRollNo) {
            showError('Please search and load a valid student report first.');
            return;
        }

        /* Collect student fields */
        var studentFields = {};
        var sfRoot = $('studentFields');
        if (sfRoot) {
            sfRoot.querySelectorAll('input[name], select[name], textarea[name]').forEach(function (el) {
                studentFields[el.name] = el.value;
            });
        }

        /* Attendance */
        var attInput = $('attendance_percentage');
        var attendancePercentage = attInput ? attInput.value : '0';

        /* Marks */
        var marks = [];
        all('#marksBody tr[data-subject-id]').forEach(function (tr) {
            var subjectId = tr.getAttribute('data-subject-id') || '';
            var internal  = parseInt((tr.querySelector('.mark-internal') || {}).value || '0', 10) || 0;
            var external  = parseInt((tr.querySelector('.mark-external') || {}).value || '0', 10) || 0;
            if (subjectId) {
                marks.push({
                    subject_id:     subjectId,
                    internal_marks: internal,
                    external_marks: external
                });
            }
        });

        var payload = {
            student_biodata_id:   studentBiodataId,
            original_roll_no:     originalRollNo,
            target_semester_id:   targetSemesterId,
            student_fields:       studentFields,
            attendance_percentage: attendancePercentage,
            marks:                marks
        };

        var fd = new FormData();
        fd.append('payload', JSON.stringify(payload));

        if (photoInput && photoInput.files && photoInput.files[0]) {
            fd.append('photo', photoInput.files[0]);
        }

        /* Disable all update buttons */
        updateBtns.forEach(function (b) {
            b.disabled = true;
            b.textContent = '⏳ Updating…';
        });

        try {
            var resp = await fetch('/update_report', {
                method: 'POST',
                body:   fd
            });
            var data = await resp.json();
            if (!data.success) throw new Error(data.error || 'Update failed.');

            if (updateMsg) {
                updateMsg.textContent  = data.message || 'Report updated successfully.';
                updateMsg.style.display = 'block';
            }
            setEditMode(false);

            /* Reload after short delay so user sees the banner */
            setTimeout(function () {
                window.location.href = window.location.pathname + window.location.search;
            }, 1200);

        } catch (err) {
            showError(err.message || 'Update failed. Please try again.');
        } finally {
            updateBtns.forEach(function (b) {
                b.disabled    = false;
                b.textContent = '💾 Update Report';
            });
        }
    }

    function showError(msg) {
        if (updateErr) {
            updateErr.textContent  = msg;
            updateErr.style.display = 'block';
            updateErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            alert(msg);
        }
    }

    updateBtns.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            submitUpdate();
        });
    });

})();
