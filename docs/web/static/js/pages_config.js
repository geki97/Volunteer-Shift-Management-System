// GitHub Pages runtime config (safe to commit; do not put secrets here).
// - checkinApiUrl: Hosted endpoint that records attendance. Recommended: Supabase Edge Function.
// - dataBasePath: Where the static site reads exported JSON from.

// Detect base path for GitHub Pages deployment
function getBasePath() {
  const pathname = window.location.pathname;
  // Check if on GitHub Pages subdirectory (e.g., /Volunteer-Shift-Management-System/)
  if (pathname.includes("/Volunteer-Shift-Management-System/")) {
    return "/Volunteer-Shift-Management-System/appflowy_exports";
  }
  // Local development or root deployment
  return "./appflowy_exports";
}

window.VMS_CONFIG = {
  checkinApiUrl: "", // e.g. "https://<project>.functions.supabase.co/checkin"
  dataBasePath: getBasePath(),
};

