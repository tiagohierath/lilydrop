# lilydrop

Create a seven-day share with `./lilydrop.py publish assets.tar.gz`. Revoke it with `./lilydrop.py revoke TOKEN`. Run `./lilydrop.py serve` behind an HTTPS reverse proxy on port `8787`.

On the existing Navylily host, install `auth/deploy/lilydrop.service`, add `files.navylily.tv` to the Cloudflare tunnel and DNS, then start the service. Public links use `https://files.navylily.tv/s/TOKEN`.

The client page should show the project name, archive size, file count, and exact expiry time. Provide one **Download assets** button and one **Copy agent command** button. Show clear `expired` and `revoked` states.

Downloads should stream in chunks and support HTTP range requests so interrupted downloads can resume. Disable directory browsing, suppress URL logs, and send private no-cache headers. lilydrop does not terminate TLS.
