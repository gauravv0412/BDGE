# Google OAuth Setup

Wisdomize has a safe Google sign-in foundation in Step 36B. The UI and routes are present, and the app does not crash when credentials are missing.

## Environment Variables

Set these before enabling live Google OAuth:

```bash
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
```

No real credentials should be committed.

## Current Status

- Password signup uses email verification.
- Google-authenticated users are treated as verified when Google supplies a verified email.
- The live OAuth redirect/callback exchange is intentionally backlogged until production domains and callback URLs are final.

## Backlog

- Wire live Google authorization and callback routes.
- Add production SMTP credentials through environment variables.
- Add delete history, export history, account deletion, and a dedicated privacy policy page.
