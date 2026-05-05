// GitHub Pages check-in page logic (static UI + hosted API call).
(function () {
  const els = {
    shiftDetails: () => document.getElementById("shift-details"),
    volunteerSelect: () => document.getElementById("volunteer-select"),
    confirmBtn: () => document.getElementById("confirm-btn"),
    result: () => document.getElementById("result"),
  };

  function getTokenFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get("token") || "";
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function renderShift(shift) {
    const d = els.shiftDetails();
    if (!shift) {
      d.innerHTML =
        '<p style="color: var(--danger-color);">Shift not found in exported data.</p>';
      return;
    }

    d.innerHTML = `
      <p><strong>Shift:</strong> ${escapeHtml(shift.shift_name || shift.id || "Unknown")}</p>
      <p><strong>Date:</strong> ${escapeHtml(shift.shift_date || "N/A")}</p>
      <p><strong>Location:</strong> ${escapeHtml(shift.location || "N/A")}</p>
      <p><strong>Status:</strong> ${escapeHtml(shift.status || "N/A")}</p>
    `;
  }

  function populateVolunteers(volunteers, selectedId) {
    const sel = els.volunteerSelect();
    const opts = [];
    opts.push('<option value="">Select volunteer...</option>');
    for (const v of volunteers || []) {
      const id = v.id || "";
      const name = v.name || id || "Unknown";
      const selected = selectedId && String(selectedId) === String(id) ? " selected" : "";
      opts.push(`<option value="${escapeHtml(id)}"${selected}>${escapeHtml(name)}</option>`);
    }
    sel.innerHTML = opts.join("");
  }

  async function submitCheckin(payload, volunteerId) {
    const cfg = window.VMS_CONFIG || {};
    const apiUrl = (cfg.checkinApiUrl || "").trim();
    if (!apiUrl) {
      throw new Error("Check-in API not configured.");
    }

    const body = {
      token: getTokenFromUrl(),
      shift_id: payload.shift_id,
      volunteer_id: volunteerId,
      source: "github_pages",
    };

    const res = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const text = await res.text();
    if (!res.ok) {
      throw new Error("HTTP " + res.status + ": " + text);
    }
    return text ? JSON.parse(text) : { ok: true };
  }

  async function init() {
    const token = getTokenFromUrl();
    const parsed = window.VMS_DATA.parseToken(token);
    if (!parsed.ok) {
      els.shiftDetails().innerHTML =
        '<p style="color: var(--danger-color);">Invalid token.</p>';
      els.confirmBtn().disabled = true;
      return;
    }

    const payload = parsed.payload || {};

    let volunteers = [];
    let shifts = [];
    try {
      [volunteers, shifts] = await Promise.all([
        window.VMS_DATA.loadVolunteers(),
        window.VMS_DATA.loadShifts(),
      ]);
    } catch (e) {
      els.shiftDetails().innerHTML =
        '<p style="color: var(--danger-color);">Unable to load shift data. Please try again.</p>';
      els.confirmBtn().disabled = true;
      return;
    }

    const shift = (shifts || []).find((s) => String(s.id) === String(payload.shift_id));
    renderShift(shift);

    populateVolunteers(volunteers, payload.user_id);

    els.confirmBtn().addEventListener("click", async () => {
      els.result().textContent = "";
      const volunteerId = els.volunteerSelect().value || payload.user_id || "";
      if (!volunteerId) {
        els.result().innerHTML =
          '<p style="color: var(--danger-color);">Please select a volunteer.</p>';
        return;
      }
      try {
        els.confirmBtn().disabled = true;
        const resp = await submitCheckin(payload, volunteerId);
        els.result().innerHTML =
          '<p style="color: var(--secondary-color); font-weight: 600;">You\'re checked in!</p>';
      } catch (e) {
        els.result().innerHTML =
          '<p style="color: var(--danger-color);">Check-in failed. Please try again.</p>';
      } finally {
        els.confirmBtn().disabled = false;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", init);
})();

