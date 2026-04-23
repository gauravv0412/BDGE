# Frontend Read-Only Shell (Step 15)

## Route

- Page route: `/`
- Backend API dependency: `POST /api/v1/analyze` only

## Purpose

This shell is a read-only inspection surface for Wisdomize output quality. It allows a user to submit a dilemma and view the full response in organized sections for quick product review and screenshot capture.

Step 16 presentation refinement keeps the same behavior and contract while improving visual scanability:

- Verdict sentence is the primary visual anchor.
- Classification/alignment/confidence are shown as quick-scan summary metrics.
- Verse/teaching, counterfactuals, missing facts, and share layer have clearer visual contrast for screenshot use.

## Included in Scope

- Single textarea input for dilemma
- Client-side submit flow to the public API boundary (`fetch` to `POST /api/v1/analyze`)
- Loading, success, and error states
- Request ID display when returned by API response headers
- Structured read-only rendering of:
  - verdict
  - score/classification/confidence
  - internal driver
  - core reading + gita analysis
  - verse match or closest teaching
  - if-you-continue
  - counterfactuals
  - higher path
  - ethical dimensions
  - missing facts
  - share layer

## Intentionally Out of Scope

- Authentication/accounts
- Saved history or persistence
- Sharing backend
- Polling/feed
- Editing workflows
- Admin/editor interfaces
- Any direct call to engine internals from frontend

## Client Rendering Note (Step 17)

The page route (`/`) now serves a shell scaffold and renders analyze results directly in-browser from the `/api/v1/analyze` JSON response. The shell does not use server postback rendering for response cards.
