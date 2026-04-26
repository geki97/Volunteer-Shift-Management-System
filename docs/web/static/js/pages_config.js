// GitHub Pages runtime config (safe to commit; do not put secrets here).
// - checkinApiUrl: Hosted endpoint that records attendance. Recommended: Supabase Edge Function.
// - dataBasePath: Where the static site reads exported JSON from.
window.VMS_CONFIG = {
  checkinApiUrl: "", // e.g. "https://<project>.functions.supabase.co/checkin"
  dataBasePath: "./appflowy_exports",
};

