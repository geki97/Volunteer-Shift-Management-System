// GitHub Pages home page logic (volunteers + shifts from static exports).
(function () {
  function el(id) {
    return document.getElementById(id);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function setActiveTab(tabName) {
    document.querySelectorAll(".tab-button").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach((t) => t.classList.remove("active"));

    const btn = document.querySelector(`.tab-button[data-tab="${tabName}"]`);
    const pane = el(tabName + "-tab");
    if (btn) btn.classList.add("active");
    if (pane) pane.classList.add("active");
  }

  function updateQuickCheckInLink() {
    const token = (el("token-input") && el("token-input").value) ? el("token-input").value.trim() : "";
    const a = el("open-checkin-link");
    if (!a) return;
    a.href = token ? "./check-in.html?token=" + encodeURIComponent(token) : "./check-in.html";
  }

  function renderVolunteers(volunteers) {
    const list = el("volunteers-list");
    if (!list) return;
    if (!volunteers || !volunteers.length) {
      list.innerHTML = "<p>No volunteers found.</p>";
      return;
    }

    list.innerHTML = volunteers
      .map((v) => {
        const availability = Array.isArray(v.availability) ? v.availability.join(", ") : (v.availability || "Not specified");
        const skills = Array.isArray(v.skills) ? v.skills.join(", ") : (v.skills || "Not specified");
        const status = v.status || "Unknown";
        const inactive = status !== "Active" ? " inactive" : "";
        return `
          <div class="card">
            <h4>${escapeHtml(v.name || v.id || "Unknown")}</h4>
            <p><strong>Email:</strong> ${escapeHtml(v.email || "N/A")}</p>
            <p><strong>Phone:</strong> ${escapeHtml(v.phone || "N/A")}</p>
            <p><strong>Status:</strong> <span class="status-badge${inactive}">${escapeHtml(status)}</span></p>
            <p><strong>Skills:</strong> ${escapeHtml(skills)}</p>
            <p><strong>Availability:</strong> ${escapeHtml(availability)}</p>
          </div>
        `;
      })
      .join("");
  }

  function renderShifts(shifts) {
    const list = el("shifts-list");
    if (!list) return;
    if (!shifts || !shifts.length) {
      list.innerHTML = "<p>No shifts found.</p>";
      return;
    }

    list.innerHTML = shifts
      .map((s) => {
        const assigned = Array.isArray(s.assigned_volunteers) ? s.assigned_volunteers : [];
        return `
          <div class="card">
            <h4>${escapeHtml(s.shift_name || s.id || "Unknown Shift")}</h4>
            <p><strong>Date:</strong> ${escapeHtml(s.shift_date || "N/A")}</p>
            <p><strong>Location:</strong> ${escapeHtml(s.location || "N/A")}</p>
            <p><strong>Status:</strong> ${escapeHtml(s.status || "N/A")}</p>
            <p><strong>Volunteers Assigned:</strong> ${assigned.length}</p>
            ${s.special_instructions ? `<p><strong>Instructions:</strong> ${escapeHtml(s.special_instructions)}</p>` : ""}
            ${assigned.length ? `<p><strong>Team:</strong> ${escapeHtml(assigned.join(", "))}</p>` : ""}
          </div>
        `;
      })
      .join("");
  }

  async function loadVolunteers() {
    const list = el("volunteers-list");
    if (list) list.innerHTML = '<div class="spinner"></div> Loading...';
    try {
      const volunteers = await window.VMS_DATA.loadVolunteers();
      renderVolunteers(volunteers);
    } catch (e) {
      if (list) {
        list.innerHTML =
          '<p style="color: red;">Unable to load volunteers. Please try again.</p>';
      }
    }
  }

  async function loadShifts() {
    const list = el("shifts-list");
    if (list) list.innerHTML = '<div class="spinner"></div> Loading...';
    try {
      const shifts = await window.VMS_DATA.loadShifts();
      renderShifts(shifts);
    } catch (e) {
      if (list) {
        list.innerHTML =
          '<p style="color: red;">Unable to load shifts. Please try again.</p>';
      }
    }
  }

  function wireTabs() {
    document.querySelectorAll(".tab-button").forEach((button) => {
      button.addEventListener("click", function () {
        const tab = this.dataset.tab;
        setActiveTab(tab);
        if (tab === "volunteers") loadVolunteers();
        if (tab === "shifts") loadShifts();
        if (tab === "checkin") updateQuickCheckInLink();
      });
    });
  }

  function init() {
    wireTabs();
    const tokenInput = el("token-input");
    if (tokenInput) tokenInput.addEventListener("input", updateQuickCheckInLink);
    updateQuickCheckInLink();
    loadVolunteers();
  }

  document.addEventListener("DOMContentLoaded", init);
})();

