# User management

Updated: 11 October 2026.

One public account buys, sells and rents. An approved agent uses that same login. Click the account avatar in the header, or open `/profile`, to manage your details.

## Profiles and permissions

| Account | Capabilities |
| --- | --- |
| User | Own profile, password/email settings, favourites/searches/enquiries, own listings, agent application |
| Agent | All user capabilities plus an approved public professional profile |
| Admin | Own profile/settings, read-only analytics and city CSV, account search/edit/suspend/reactivate, agent review, account activity, existing listing moderation |

Public registration always creates a user. Agent status is assigned by administrator review. Administrator accounts are provisioned separately; this release does not add an administrator creation or arbitrary role-change interface.

**My Profile** supports name, mobile, city, private biography and a photo. Indian mobile numbers accept ten digits beginning with 6–9, optionally prefixed with +91. Photo upload accepts JPEG/PNG/WebP up to 5 MB, strips metadata and uses the existing owner-scoped image volume. Uploading previews the photo; Save profile persists it. Another account cannot reuse your uploaded photo as its avatar. Name/photo appear publicly for an approved agent; account email and private biography are not published. Mobile appears in the directory only when the agent opts in.

## Analytics access

Only administrators can request [admin analytics](ADMIN-ANALYTICS.md); public users and agents do not gain access. Listing datasets scope inventory/enquiries, while account and agent charts cover the whole portal. CSV exports aggregate counts and prices without personal contact fields or enquiry messages. The dashboard changes no role-assignment or profile-edit permissions. Demo repricing also leaves account records, logins and uploaded images unchanged.

## Account Settings

Password changes require the current password and a different new password of at least ten characters. Other sessions are revoked; the requesting session remains signed in. Pending email verification is cancelled.

Email changes require the current password. The existing login email remains until verification succeeds. A random code is hashed in PostgreSQL, expires after 30 minutes, is bound to the signed-in account and is usable once. Resending replaces the previous code. Cancel is available; verification revokes other sessions. If the new address has been claimed meanwhile, verification returns a conflict without changing the account.

The built-in demo user and admin emails/passwords stay fixed for presentations. Register a separate account to demonstrate credential changes. Existing login passwords are preserved during migration.

### Local demo and real SMTP

Local Compose defaults to `ACCOUNT_EMAIL_MODE=demo`. A clearly labelled **Local demo only — no email sent** box displays the code, with a Use demo code button. This simulates verification and does not prove ownership of an actual mailbox. It is available only with demo accounts enabled and secure cookies disabled. Demo codes are not included in SMTP responses or account audit records.

For delivery, configure the ignored `.env` with provider credentials:

```dotenv
ACCOUNT_EMAIL_MODE=smtp
SMTP_HOST=your-provider-host
SMTP_PORT=587
SMTP_USER=your-provider-username
SMTP_PASSWORD=your-provider-secret
SMTP_FROM=no-reply@your-verified-domain.example
```

Port 587 uses STARTTLS; port 465 uses SMTP over TLS. Authentication is used when SMTP_USER is configured. Recreate only the API after changing configuration:

```powershell
docker compose up -d --no-deps --wait api
```

Azure Communication Services Email is the recommended delivery option for the Azure deployment. Configure a verified sender domain and SMTP credentials using [Microsoft's SMTP setup guide](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/email/send-email-smtp/send-email-smtp). No cloud email resources or credentials are provisioned here. Keep secrets out of Git and move them to managed secret storage for public deployment.

The Azure Compose overlay forces SMTP, secure cookies and disabled demo logins. An unconfigured/failing provider returns a useful error and leaves the login email unchanged. SMTP transport is covered with a mock; real provider delivery has not been tested. Initial-registration email verification, forgot-password, MFA and notification email are separate future work.

## Agent Profile

Enter agency/business name, professional biography, up to ten comma-separated service cities, experience, optional registration reference and optional public mobile consent. The service-city filter uses exact city membership. Applications start pending. Admin opens **Agent reviews**, reads the supplied details and approves or rejects with a reason. The applicant sees status and the review reason in Agent Profile.

Approved, active accounts appear in **Find an agent**. Cards include the professional biography, agency, service areas, supplied registration details, optional phone and owned listing count. View listings searches by stable account ID (`agent_id`), independently of display-name changes. The directory replaces the former fictional sample cards and can be empty until someone is approved.

Professional edits resubmit the profile as pending, hide it until another review and retain all normal user capabilities. Admin accounts cannot review their own application. Portal approval is a review of supplied content, not independent identity, qualification or registration certification. Customer ratings/reviews and independent credential checks are not implemented.

## Admin account controls

Open `/admin` as admin:

- **Accounts:** search name/email, filter role/status and paginate. Edit name, mobile, city and private biography; suspend/reactivate with a reason. Owners change email/password/photo through their own settings.
- **Agent reviews:** pending/approved/rejected/all applications, approve/reject with a reason.
- **Account activity:** paginated changes, actor/target account IDs, timestamp and reason; no password or verification-code values.

Suspension revokes every session, clears pending email verification, blocks login and hides the public agent card. Reactivation requires a fresh login; it does not revive old cookies. Existing listings and enquiries are retained. Archive listings separately if they should also disappear. Admins cannot suspend themselves or remove the last active administrator.

The API provides no audit-edit/delete route. Database administrators still control storage; the audit table is not a tamper-proof external ledger.

## Persistence and upgrade

`users` gains active, phone, city, bio and avatar_url with compatible defaults. New tables hold agent profiles, email-change verification and account activity. The startup migration is additive/idempotent and preserves original data. Back up PostgreSQL and uploaded images before updating; see [handoff](HANDOFF.md).

Source: `backend/app/accounts.py`, `models.py`, `migrations.py`, `frontend/src/profile.jsx`, `profile.css`, `account-admin.jsx`. Security regression coverage is in `backend/tests/test_accounts.py`; focused live checks are in `scripts/verify_accounts.py`.

```powershell
docker compose build api web
docker compose run --rm --no-deps -e DATABASE_URL=sqlite:////tmp/portal-tests.db api python -m pytest -q -p no:cacheprovider
docker compose up -d --no-deps --wait api web
python scripts/verify_accounts.py
```

The browser check creates its own account/photo/listing, archives the listing, rejects the test agent profile and suspends the test account. Test history remains intentionally; it never resets the database. See [verification](VERIFICATION.md) for outcomes and preserved-data evidence.

## Shared search experience

Users, approved agents and administrators retain the same public search interface. Filtered pins remain visible while drawing a boundary; hovering a property card highlights its matching pin with a thin cyan glow. Professional profile or account edits do not reset saved searches. Suspension blocks authenticated account access but preserves existing records and requires separate listing archival when needed.

## Account analytics

The admin Analytics tab reports role composition, active/suspended totals, new registrations and the agent application pipeline. These aggregate charts include all portal accounts, including labelled demo accounts, regardless of the selected listing dataset. They do not publish personal details. Accounts, Agent reviews and Account activity retain their existing controls. See [admin analytics](ADMIN-ANALYTICS.md).
