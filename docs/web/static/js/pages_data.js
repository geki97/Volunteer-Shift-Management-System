// Data helpers for GitHub Pages (static JSON exports).
(function () {
  function config() {
    return (window.VMS_CONFIG || { dataBasePath: "./appflowy_exports" });
  }

  async function fetchJson(path) {
    const res = await fetch(path, { cache: "no-store" });
    if (!res.ok) {
      throw new Error("HTTP " + res.status + " for " + path);
    }
    return await res.json();
  }

  async function loadVolunteers() {
    const base = config().dataBasePath || "./appflowy_exports";
    return await fetchJson(base.replace(/\/$/, "") + "/volunteers.json");
  }

  async function loadShifts() {
    const base = config().dataBasePath || "./appflowy_exports";
    return await fetchJson(base.replace(/\/$/, "") + "/shifts.json");
  }

  function parseToken(token) {
    // Token format (from Python): base64( token_json + "." + signature_hex )
    if (!token) return { ok: false, error: "Missing token" };
    try {
      const b64 = String(token).replace(/-/g, "+").replace(/_/g, "/");
      const padded = b64 + "===".slice((b64.length + 3) % 4);
      const decoded = atob(padded);
      const parts = decoded.split(".");
      if (parts.length < 2) return { ok: false, error: "Invalid token format" };
      const signatureHex = parts.pop();
      const tokenJson = parts.join(".");
      const payload = JSON.parse(tokenJson);
      return { ok: true, payload, signatureHex };
    } catch (e) {
      return { ok: false, error: e && e.message ? e.message : String(e) };
    }
  }

  window.VMS_DATA = {
    loadVolunteers,
    loadShifts,
    parseToken,
  };
})();
