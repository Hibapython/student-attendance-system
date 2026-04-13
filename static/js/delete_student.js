(function () {
  "use strict";

  /* ── URL constants injected by Flask via window.APP_URLS in the template ── */
  var URLs = window.APP_URLS || {
    search:    "/delete_student/search",
    confirm:   "/delete_student/confirm_delete",
    dashboard: "/dashboard"
  };

  /* ── Student list injected by Flask via window.STUDENTS_DATA ── */
  var allStudents = [];
  try {
    allStudents = Array.isArray(window.STUDENTS_DATA) ? window.STUDENTS_DATA : [];
  } catch (e) {
    allStudents = [];
  }

  /* ── DOM refs ── */
  var comboFilter   = document.getElementById("comboFilter");
  var comboList     = document.getElementById("comboList");
  var queryInput    = document.getElementById("queryInput");
  var btnSearch     = document.getElementById("btnSearch");
  var btnCancel     = document.getElementById("btnCancel");
  var btnDelete     = document.getElementById("btnDelete");
  var msgError      = document.getElementById("msgError");
  var msgInfo       = document.getElementById("msgInfo");
  var detailSection = document.getElementById("detailSection");
  var detailGrid    = document.getElementById("detailGrid");
  var confirmBlock  = document.getElementById("confirmBlock");

  /* ── Safety check: abort if any critical element is missing ── */
  if (!comboFilter || !comboList || !queryInput || !btnSearch ||
      !btnCancel || !btnDelete || !msgError || !msgInfo ||
      !detailSection || !detailGrid || !confirmBlock) {
    console.error("Delete Student: one or more required DOM elements not found.");
    return;
  }

  /* ── State ── */
  var selectedPk     = null;
  var selectedRollNo = null;

  /* ────────────────────────────────────────────────────────── */
  /*  HELPERS                                                    */
  /* ────────────────────────────────────────────────────────── */

  function hide(el) { el.classList.add("is-hidden"); }
  function show(el) { el.classList.remove("is-hidden"); }

  function clearMessages() {
    hide(msgError); msgError.textContent = "";
    hide(msgInfo);  msgInfo.textContent  = "";
  }

  function showError(text) {
    clearMessages();
    msgError.textContent = text;
    show(msgError);
  }

  function showInfo(text) {
    clearMessages();
    msgInfo.textContent = text;
    show(msgInfo);
  }

  function humanize(key) {
    return (key || "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }

  /* ── POST JSON helper ── */
  function postJSON(url, payload, onSuccess, onError) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Accept", "application/json");
    xhr.onreadystatechange = function () {
      if (xhr.readyState !== 4) return;
      var data = {};
      try { data = JSON.parse(xhr.responseText); } catch (e) { /* empty */ }
      if (xhr.status >= 200 && xhr.status < 300 && data.success) {
        onSuccess(data);
      } else {
        onError(data.error || ("Server error: " + xhr.status));
      }
    };
    xhr.onerror = function () { onError("Network error. Please check your connection."); };
    xhr.send(JSON.stringify(payload));
  }

  /* ────────────────────────────────────────────────────────── */
  /*  COMBO (dropdown list)                                      */
  /* ────────────────────────────────────────────────────────── */

  function filterStudents(term) {
    if (!term) return allStudents.slice();
    var t = term.toLowerCase();
    return allStudents.filter(function (s) {
      return (
        String(s.full_name  || "").toLowerCase().indexOf(t) !== -1 ||
        String(s.roll_no    || "").toLowerCase().indexOf(t) !== -1 ||
        String(s.biodata_pk || "").toLowerCase().indexOf(t) !== -1
      );
    });
  }

  function closeCombo() {
    comboList.classList.remove("is-open");
    comboList.innerHTML = "";
  }

  function openCombo() {
    var term    = comboFilter.value.trim();
    var results = filterStudents(term);

    comboList.innerHTML = "";

    if (allStudents.length === 0) {
      var empty = document.createElement("div");
      empty.className   = "combo-empty";
      empty.textContent = "No students in the database.";
      comboList.appendChild(empty);
    } else if (results.length === 0) {
      var noMatch = document.createElement("div");
      noMatch.className   = "combo-empty";
      noMatch.textContent = "No matches found.";
      comboList.appendChild(noMatch);
    } else {
      results.forEach(function (s) {
        var item = document.createElement("div");
        item.className = "combo-item";
        item.setAttribute("role", "option");
        item.tabIndex  = 0;
        item.textContent = s.label ||
          (String(s.full_name) + " | Roll No: " + String(s.roll_no) + " | ID: " + String(s.biodata_pk));

        function pick() {
          closeCombo();
          comboFilter.value = "";
          loadStudent({ biodata_pk: s.biodata_pk });
        }

        item.addEventListener("click", pick);
        item.addEventListener("keydown", function (ev) {
          if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            pick();
          }
        });
        comboList.appendChild(item);
      });
    }

    comboList.classList.add("is-open");
  }

  comboFilter.addEventListener("focus", openCombo);
  comboFilter.addEventListener("input", openCombo);

  document.addEventListener("click", function (ev) {
    if (ev.target !== comboFilter && !comboList.contains(ev.target)) {
      closeCombo();
    }
  });

  /* ────────────────────────────────────────────────────────── */
  /*  LOAD STUDENT (search API call)                             */
  /* ────────────────────────────────────────────────────────── */

  function clearDetail() {
    selectedPk     = null;
    selectedRollNo = null;
    hide(detailSection);
    hide(confirmBlock);
    detailGrid.innerHTML = "";
    clearMessages();
  }

  function renderDetail(student) {
    detailGrid.innerHTML = "";

    var preferred = ["id", "student_id", "roll_no", "full_name", "dob",
                     "class_sec", "exam_reg", "primary_phone", "alt_phone"];
    var allKeys   = Object.keys(student).sort();
    var ordered   = preferred.filter(function (k) { return allKeys.indexOf(k) !== -1; })
      .concat(allKeys.filter(function (k) { return preferred.indexOf(k) === -1; }));

    ordered.forEach(function (k) {
      var val = student[k];
      if (val === null || val === undefined || val === "") return;
      var dt = document.createElement("dt");
      dt.textContent = humanize(k);
      var dd = document.createElement("dd");
      dd.textContent = String(val);
      detailGrid.appendChild(dt);
      detailGrid.appendChild(dd);
    });

    show(detailSection);
    show(confirmBlock);
  }

  function loadStudent(payload) {
    clearMessages();
    hide(confirmBlock);
    detailGrid.innerHTML = "";
    hide(detailSection);

    showInfo("Searching…");

    postJSON(
      URLs.search,
      payload,
      function (data) {
        clearMessages();
        selectedPk     = data.biodata_pk;
        selectedRollNo = data.roll_no;
        renderDetail(data.student || {});
      },
      function (err) {
        showError(err);
      }
    );
  }

  /* ────────────────────────────────────────────────────────── */
  /*  SEARCH BUTTON                                              */
  /* ────────────────────────────────────────────────────────── */

  btnSearch.addEventListener("click", function () {
    var q = queryInput.value.trim();
    if (!q) {
      showError("Enter a roll number or student ID.");
      return;
    }
    loadStudent({ query: q });
  });

  queryInput.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter") {
      ev.preventDefault();
      btnSearch.click();
    }
  });

  /* ────────────────────────────────────────────────────────── */
  /*  CANCEL BUTTON                                              */
  /* ────────────────────────────────────────────────────────── */

  btnCancel.addEventListener("click", function () {
    clearDetail();
    comboFilter.value = "";
    queryInput.value  = "";
  });

  /* ────────────────────────────────────────────────────────── */
  /*  DELETE BUTTON                                              */
  /* ────────────────────────────────────────────────────────── */

  btnDelete.addEventListener("click", function () {
    if (selectedPk == null || selectedRollNo == null) {
      showError("No student selected.");
      return;
    }

    var confirmed = window.confirm(
      "This will permanently remove this student and ALL related attendance, " +
      "marks, and result records.\n\nThis cannot be undone. Continue?"
    );
    if (!confirmed) return;

    btnDelete.disabled = true;
    btnSearch.disabled = true;
    showInfo("Deleting, please wait…");

    postJSON(
      URLs.confirm,
      { biodata_pk: selectedPk, roll_no: selectedRollNo },
      function (data) {
        showInfo((data.message || "Student deleted successfully.") + " Redirecting to dashboard…");
        setTimeout(function () {
          window.location.href = URLs.dashboard;
        }, 1400);
      },
      function (err) {
        btnDelete.disabled = false;
        btnSearch.disabled = false;
        showError(err);
      }
    );
  });

})();
