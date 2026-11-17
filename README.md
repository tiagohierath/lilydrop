# lilydrop

Just a tool i built to share files 

Show active links with `./lilydrop.py list`. Each entry includes the project,
delivery, URL, and expiry in UTC. Use `./lilydrop.py list --all` to include
expired and revoked links. Listing is read-only and does not extend expiry.

Publish a numbered delivery with `./lilydrop.py publish DELIVERY_FOLDER --project PROJECT --delivery 1 --allow-root PROJECT_ROOT`. Revoke it with `./lilydrop.py revoke TOKEN`. Run `./lilydrop.py serve` behind an HTTPS reverse proxy on port `8787`.

The local production ledger remains at `../navylily-tools/.state/lilydrop/shares.json`.
The CLI and server use this same default; do not move or replace the ledger during updates.
Existing tokens and archive paths remain valid until their original expiry.
Client links use `/PROJECT/NUMBER/TOKEN`; legacy `/s/TOKEN` links are supported.

The production user unit is `lilydrop.service`. Its `deploy/override.conf` drop-in
selects this checkout and explicitly pins the existing ledger. Run
`systemctl --user restart lilydrop.service` after updating.
Do not run preview servers on production port 8787; use `serve --port 8788`.

Run tests with `python3 -m unittest discover -s tests` from this directory.

On the existing Navylily host, install `auth/deploy/lilydrop.service`, add `files.navylily.tv` to the Cloudflare tunnel and DNS, then start the service. Public links use `https://files.navylily.tv/s/TOKEN`.

The client page should show the project name, archive size, file count, and exact expiry time. Provide one **Download assets** button and one **Copy agent command** button. Show clear `expired` and `revoked` states.

Downloads should stream in chunks and support HTTP range requests so interrupted downloads can resume. Disable directory browsing, suppress URL logs, and send private no-cache headers. lilydrop does not terminate TLS.
