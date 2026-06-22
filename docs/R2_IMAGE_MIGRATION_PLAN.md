# Plan: Move dept56-gallery images to Cloudflare R2 (images only)

**Status:** Not started — reference plan. **Written:** 2026-06-21.
**Scope:** Move *only* the image files off Firebase Cloud Storage to Cloudflare R2.
Firestore (data), Firebase Auth, and Firebase Hosting **stay on Firebase's free Spark tier** and are not touched.

---

## Why / when to do this

Today this is **not** a cost problem — a ~400-image gallery sits inside Firebase Storage's
free quota, so the bill is ~$0. The reason to migrate is **reliability + consolidation**:

- **Removes the failure mode we just hit.** Firebase requires the paid **Blaze** plan (an
  attached payment method) to use Cloud Storage *at all*. When the billing account
  (`My Billing Account` 01298F-73F87A-D58FBA) closed, every image 402/403'd even though usage
  was free. R2's free tier needs **no** payment method, so a closed card can't dark the gallery.
- **Consolidates with MSL-Tender**, which already runs R2 (and far more images).
- **Zero egress fees** on R2 (Firebase charges egress above 1 GB/day) — future-proof if traffic grows.

**Trigger to execute:** Google starts charging for Storage, another billing-account lapse,
or a deliberate "everything image-related on Cloudflare" cleanup.

After migration, dept56-gallery uses **no** Firebase Storage → it can drop off Blaze entirely
and run free, like every other rndpig project.

---

## Current state (snapshot)

| Thing | Value |
|---|---|
| Firebase project | `dept56-gallery` |
| Storage bucket | `gs://dept56-gallery.firebasestorage.app` |
| Object paths | `images/houses/{uuid}-{name}.jpg`, `images/accessories/{uuid}-{name}.jpg`, plus `uploads/{...}` |
| Image count | ~407 (235 houses + 172 accessories) + any `uploads/` — ~50 MB total, mostly `.jpg` |
| How URLs are stored | Each Firestore house/accessory doc has a `photoUrl` field = a **raw GCS URL**, e.g. `https://storage.googleapis.com/dept56-gallery.firebasestorage.app/images/houses/{file}.jpg` |
| How the app renders | `firestoreToHouse()` maps `photo_url: data.photoUrl`; the UI uses it directly as `<img src>` |
| Upload code | `src/lib/firebase-database.ts` — `ref` / `uploadBytes` / `getDownloadURL` / `deleteObject` from `firebase/storage` |

Because images are referenced by a **stored URL string**, the cutover is mostly a
find-and-replace of the URL host across Firestore docs — the app code barely changes for *reads*.

---

## Target architecture

- R2 bucket, e.g. `dept56-gallery-images`, on the Cloudflare account.
- **Public read via a custom domain** bound to the bucket, e.g. `dept56-images.rndpig.com`
  (recommended over the rate-limited `*.r2.dev` URL). dept56 is a **public** gallery, so
  public read is correct — **no Cloudflare Access** needed (unlike the MSL-Tender bucket, which
  has its own public-vs-Access decision).
- **Keep the same object keys** (`images/houses/{file}` …) so only the URL *host* changes.
  New image URLs: `https://dept56-images.rndpig.com/images/houses/{file}.jpg`.
- Uploads write to R2 through a tiny **Cloudflare Worker** (presigned PUT or proxy) so the R2
  secret stays server-side — never in the client bundle.

---

## Migration steps

### Phase 0 — Prep (no downtime, fully reversible)
1. Create R2 bucket `dept56-gallery-images` (Cloudflare → R2).
2. Bind custom domain `dept56-images.rndpig.com` to the bucket (public read). Verify a manual
   `GET https://dept56-images.rndpig.com/test.jpg` returns 200 after a test upload.
3. Create an R2 S3-API token (account id, access key id, secret) for the copy + uploads.
   Store it **outside git** (Cloudflare secret / local `.env`, gitignored).

### Phase 1 — Copy the files (no downtime, both sources live)
4. One-time copy GCS → R2, preserving keys. Easiest is **rclone** with two remotes
   (GCS source, R2 as an S3 provider):
   ```
   rclone copy gcs:dept56-gallery.firebasestorage.app/images r2:dept56-gallery-images/images --progress
   rclone copy gcs:dept56-gallery.firebasestorage.app/uploads r2:dept56-gallery-images/uploads --progress
   ```
   (GCS remote auths via the dept56-gallery service account or `gcloud auth`; R2 remote via the
   Phase-0 token + the R2 S3 endpoint.)
5. Verify object counts match (~407) and spot-check several R2 URLs return `200 image/jpeg`.

### Phase 2 — Repoint the data (the cutover)
6. Batch-rewrite Firestore `photoUrl` on every house + accessory: swap the host only —
   `https://storage.googleapis.com/dept56-gallery.firebasestorage.app/` →
   `https://dept56-images.rndpig.com/` (path/key unchanged). Node + `firebase-admin`, batched writes.
   Use ADC (`gcloud auth application-default login`) so no SA key sits on disk.
7. Hard-refresh the gallery → images now load from R2 (confirm the host in the Network tab).
   **This is the cutover** — the moment `photoUrl` points to R2, reads come from R2.

### Phase 3 — Repoint uploads (new images)
8. In `src/lib/firebase-database.ts`, replace the Firebase Storage upload/delete with R2:
   - Stand up a small **Worker** that (a) issues a presigned R2 PUT URL (preferred) or (b) proxies
     the upload, and handles delete. The "Manage" admin flow is the only writer, low frequency.
   - On upload, store the resulting `https://dept56-images.rndpig.com/images/{type}/{key}` as `photoUrl`.
   - Drop the `firebase/storage` import once nothing uses it.

### Phase 4 — Decommission Firebase Storage (the savings)
9. After a few days serving cleanly from R2:
   - Empty/delete the Firebase Storage bucket.
   - Remove `"storage"` from `firebase.json`; delete `storage.rules` if unused.
   - Confirm Storage was the only Blaze-billed service on dept56-gallery, then **unlink billing**
     (back to free Spark). The other rndpig projects already run this way.

---

## Rollback

Until Phase 4 the Firebase Storage files still exist, so cutover is reversible: re-run the
Phase-2 script with the host prefixes swapped back (`dept56-images.rndpig.com/` →
`storage.googleapis.com/dept56-gallery.firebasestorage.app/`). Keep GCS files until confident.

---

## Cost after migration

- **R2:** 10 GB storage free, **zero egress**, generous free ops. ~50 MB gallery = **$0**, with
  no payment-method-required failure mode.
- **Firebase:** Firestore + Auth + Hosting on Spark = **$0**, no billing account required.

## Effort

~Half a day: bucket + domain, the rclone copy, the Firestore rewrite script, the upload Worker, testing.

## Open decisions when executing

- Final custom-domain name (`dept56-images.rndpig.com` suggested).
- Upload mechanism: Worker presigned PUT (recommended) vs Worker proxy.
- Reuse the existing MSL-Tender Cloudflare/R2 account + tooling patterns.
