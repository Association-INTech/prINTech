# Security Operations

## Historical Django/JWT Secret

The current code reads `DJANGO_SECRET_KEY` from the environment. If an old hard-coded key has been pushed or shared, treat it as compromised.

1. Generate a new secret:
   `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
2. Set the new value in production as `DJANGO_SECRET_KEY`.
3. Deploy and restart all Django workers.
4. Invalidate outstanding refresh tokens:
   `DJANGO_SETTINGS_MODULE=back.settings.prod ./manage.py flushexpiredtokens`
   Changing `DJANGO_SECRET_KEY` invalidates existing JWT signatures; users must log in again.
5. Purge Git history only with coordinated team approval because it rewrites commit IDs and requires force-push.

Recommended purge command after approval:

```sh
git filter-repo --path backend/back/settings/base.py --path backend/back/settings/prod.py --replace-text replacements.txt
```

The `replacements.txt` file must contain the exact leaked secret mapped to a redaction token, and must not be committed.

## Production Reverse Proxy

Use `deploy/nginx-printech.conf` as a baseline for:

- upload body limits before Django receives multipart data;
- rate limits for auth/API endpoints;
- security headers and CSP;
- admin IP allowlisting.

## Slicer Runtime

`rpi/slice.sh` refuses checksum mismatches and applies size/time/memory limits. For production, run it inside a rootless container or equivalent OS sandbox with network disabled and per-job temporary storage.
