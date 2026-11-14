// Reload the page when a newer build has been deployed.
//
// A web app saved to the iPhone Home Screen has no refresh button, and iOS
// resumes it from memory instead of reloading it, so without this it keeps
// running whatever build it was first opened with.

const BUNDLE_RE = /<script[^>]+src="(\/assets\/[^"]+\.js)"/
const RELOADED_FOR_KEY = 'd56-reloaded-for'
const MIN_INTERVAL_MS = 60_000

/** The app's script path named in a copy of index.html, or null if none. */
export function bundleIn(html: string): string | null {
  return BUNDLE_RE.exec(html)?.[1] ?? null
}

type Deps = {
  current: string | null
  fetchHtml: () => Promise<string>
  reload: () => void
  isEditing: () => boolean
  storage: Pick<Storage, 'getItem' | 'setItem'>
}

/** Reload once if the live site names a different script than the one running. */
export async function checkForUpdate({ current, fetchHtml, reload, isEditing, storage }: Deps): Promise<boolean> {
  if (!current) return false // dev server: no built script to compare
  let live: string | null
  try { live = bundleIn(await fetchHtml()) } catch { return false } // offline: try again later
  if (!live || live === current) return false
  // Never reload twice for the same build (guards against a reload loop if a
  // stale copy of the page keeps coming back), and never under someone typing.
  if (storage.getItem(RELOADED_FOR_KEY) === live || isEditing()) return false
  storage.setItem(RELOADED_FOR_KEY, live)
  reload()
  return true
}

export function startUpdateChecks(): void {
  const current = document.querySelector('script[type="module"][src^="/assets/"]')?.getAttribute('src') ?? null
  if (!current) return
  let lastCheck = 0
  const run = () => {
    if (document.visibilityState !== 'visible' || Date.now() - lastCheck < MIN_INTERVAL_MS) return
    lastCheck = Date.now()
    void checkForUpdate({
      current,
      fetchHtml: () => fetch('/', { cache: 'no-store' }).then(r => (r.ok ? r.text() : Promise.reject(new Error(String(r.status))))),
      reload: () => window.location.reload(),
      isEditing: () => /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName ?? ''),
      storage: window.sessionStorage,
    })
  }
  document.addEventListener('visibilitychange', run)
  window.addEventListener('pageshow', run)
  run()
}
