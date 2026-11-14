# SophieDrop

Small expiring file-share server for client asset deliveries.

SophieDrop creates independent random links that expire after seven days by default. Each link can be revoked without affecting other shares.

## Run

```sh
python3 sophiedrop.py publish assets.tar.gz
python3 sophiedrop.py serve
python3 sophiedrop.py revoke TOKEN
```

Put the local HTTP server behind an HTTPS reverse proxy or tunnel. SophieDrop does not manage TLS.

The share page shows the archive name, human-readable size, expiry time, download action, and a copyable `curl` command. Downloads support streaming and resume requests.

State is stored in `~/.local/state/sophiedrop/shares.json`, or at the path in `SOPHIEDROP_STATE`.
