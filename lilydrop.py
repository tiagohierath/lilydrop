#!/run/current-system/sw/bin/python3
import argparse, html, json, os, secrets, shlex, tarfile, time, zipfile
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote, unquote, urlparse

S = Path(os.environ.get('LILYDROP_STATE', str(Path.home() / '.local/state/lilydrop/shares.json')))
CHUNK = 1024 * 1024

def human_size(n):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024 or unit == 'TB': return f'{n:.1f} {unit}' if unit != 'B' else f'{n} B'
        n /= 1024

def state(): return json.loads(S.read_text() or '{}') if S.exists() else {}
def save(value):
    S.parent.mkdir(parents=True, exist_ok=True); temp = S.with_suffix('.tmp'); temp.write_text(json.dumps(value)); temp.replace(S)
def file_count(filename):
    try:
        if tarfile.is_tarfile(filename): return len(tarfile.open(filename).getmembers())
        if zipfile.is_zipfile(filename): return len(zipfile.ZipFile(filename).infolist())
    except (OSError, tarfile.TarError, zipfile.BadZipFile): pass
    return None

CSS = '''
:root{color-scheme:dark;--bg:#0c0d0d;--panel:#151716;--line:#2b2e2c;--muted:#969c97;--text:#f2f4ee;--lime:#d9f76d}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 50% -10%,#242a25 0,#0c0d0d 48%);color:var(--text);font:15px/1.5 Inter,ui-sans-serif,system-ui,sans-serif;min-height:100vh}header{height:72px;display:flex;align-items:center;justify-content:space-between;max-width:1080px;margin:auto;padding:0 28px;border-bottom:1px solid #202320}.brand{color:var(--text);font-weight:700;letter-spacing:-.02em;text-decoration:none}.brand span{color:var(--muted);font-weight:400}.secure{color:var(--muted);font-size:11px;letter-spacing:.1em;text-transform:uppercase}main{max-width:680px;margin:auto;padding:52px 24px 60px}.hero{text-align:center}.orb{height:142px;width:142px;margin:0 auto 24px;display:grid;place-items:center;border:1px solid #303730;border-radius:50%;background:radial-gradient(circle,#28332b,#141815 68%);box-shadow:0 0 0 14px #111511,0 0 80px #455e3d55}.orb img{width:118px}.kicker{color:var(--lime);font-size:11px;font-weight:700;letter-spacing:.18em;margin:0 0 12px}.hero h1{font-size:clamp(30px,6vw,46px);letter-spacing:-.055em;line-height:1.05;margin:0}.lede{color:var(--muted);margin:14px 0 28px}.lede strong{color:var(--text);font-weight:500}.card{padding:18px;border:1px solid var(--line);border-radius:16px;background:linear-gradient(145deg,#191c1a,#121413);box-shadow:0 24px 60px #0006;text-align:left}.file-row{display:flex;align-items:center;gap:13px;padding:5px 3px 18px}.file-icon{display:grid;place-items:center;width:42px;height:48px;border:1px solid #64775b;border-radius:7px;color:var(--lime);font-size:10px;font-weight:800;background:#293427}.file-name{min-width:0;flex:1}.file-name strong{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.file-name span{display:block;color:var(--muted);font-size:12px;margin-top:3px}.ready{color:var(--lime);font-size:10px;font-weight:700;letter-spacing:.13em}.details{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:15px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.details div{display:flex;flex-direction:column;gap:4px}.details span,.command>span{color:var(--muted);font-size:10px;letter-spacing:.12em}.details strong{font-size:13px;font-weight:500}.actions{display:grid;grid-template-columns:1.3fr 1fr;gap:10px;margin-top:16px}.actions a,.actions button{min-height:46px;display:flex;align-items:center;justify-content:center;gap:9px;border-radius:9px;font:inherit;font-size:13px;font-weight:700;text-decoration:none;cursor:pointer}.download{color:#111!important;background:var(--lime);border:1px solid var(--lime)}.actions button{color:var(--text);background:#202421;border:1px solid #454b45}.command{margin-top:10px;padding:12px 38px 12px 13px;border-radius:8px;background:#0c0e0d;border:1px solid #252a26;position:relative}.command span{display:block;margin-bottom:6px}.command code{display:block;color:#c5cec4;font:11px/1.45 ui-monospace,SFMono-Regular,monospace;overflow-wrap:anywhere}.command button{position:absolute;right:10px;bottom:11px;color:var(--muted);background:none;border:0;font-size:18px;cursor:pointer}.fine-print{color:var(--muted);font-size:12px;text-align:center;margin:18px 0 0}#status{color:var(--lime);font-size:12px;min-height:18px;margin:10px 0 0}@media(max-width:540px){header{padding:0 18px}.secure{display:none}main{padding:34px 16px}.orb{height:116px;width:116px}.orb img{width:100px}.card{padding:15px}.details{grid-template-columns:1fr}.actions{grid-template-columns:1fr}.hero h1{font-size:34px}}
'''
CSS = CSS.replace('Inter,ui-sans-serif,system-ui,sans-serif', 'ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono",monospace')
CSS += '''
body{background:#111;color:#eee}header{height:56px;border-bottom:1px solid #292929}main{max-width:620px;padding:42px 20px}.hero{text-align:left}.orb{height:auto;width:auto;margin:0 0 24px;border:0;border-radius:0;background:none;box-shadow:none;display:block}.orb img{display:block;width:92px}.kicker{color:#999;margin-bottom:10px}.hero h1{font-size:28px;letter-spacing:-.04em}.lede{color:#999;margin:10px 0 28px}.card{padding:0;border:0;border-radius:0;background:none;box-shadow:none}.file-row{padding:16px 0;border-top:1px solid #444;border-bottom:1px solid #444}.details{display:flex;flex-wrap:wrap;gap:28px;padding:16px 0;border:0}.details div{min-width:150px}.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:4px}.actions a,.actions button{min-height:42px;padding:0 16px;border-radius:2px}.download{background:#eee;border-color:#eee}.actions button{background:none;border-color:#555}.command{margin-top:18px;padding:12px 0;border:0;border-top:1px solid #333;border-radius:0;background:none}.command code{color:#aaa}.fine-print{text-align:left;border-top:1px solid #333;padding-top:16px;margin-top:22px;color:#777}.secure{font-size:10px}@media(max-width:540px){main{padding:30px 16px}.orb img{width:76px}.actions{display:flex}.actions a,.actions button{flex:1;padding:0 10px}.details{gap:18px}.details div{min-width:130px}}
 :root{--lime:#eee}.orb img{filter:grayscale(1)}.file-icon{color:#eee;background:#222;border-color:#777}.download{background:#eee!important;border-color:#eee!important;color:#111!important}
'''

def main():
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest='command', required=True)
    publish = sub.add_parser('publish'); publish.add_argument('file'); publish.add_argument('--days', type=int, default=7); publish.add_argument('--slug'); publish.add_argument('--base-url', default='https://files.navylily.tv')
    revoke = sub.add_parser('revoke'); revoke.add_argument('token'); sub.add_parser('serve'); args = parser.parse_args()
    if args.command == 'publish':
        if args.days <= 0: parser.error('--days must be greater than zero')
        filename = Path(args.file).resolve()
        if not filename.is_file(): parser.error(f'file not found: {args.file}')
        shares = state(); token = secrets.token_urlsafe(32); record = {'file': str(filename), 'expires': time.time() + args.days * 86400, 'file_count': file_count(filename)}
        if args.slug:
            if not args.slug.replace('-', '').replace('_', '').isalnum(): parser.error('invalid slug')
            if any(item.get('slug') == args.slug for item in shares.values()): parser.error(f'slug already exists: {args.slug}')
            record['slug'] = args.slug
        shares[token] = record; save(shares); prefix = 'd/' + args.slug if args.slug else 's/' + token; print(f'{args.base_url.rstrip("/")}/{prefix}'); return
    if args.command == 'revoke':
        shares = state()
        if args.token in shares: shares[args.token]['revoked'] = True; save(shares)
        return

    class Handler(BaseHTTPRequestHandler):
        def state_page(self, title, message):
            body = f'<!doctype html><html><head><meta name="viewport" content="width=device-width"><style>{CSS}</style></head><body><main><p class="kicker">LILYDROP</p><h1>{html.escape(title)}</h1><p>{html.escape(message)}</p></main></body></html>'.encode(); self.send_response(410); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length', str(len(body))); self.send_header('Cache-Control','private, no-store'); self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            path = urlparse(self.path).path
            if path == '/lilydrop-folder-chrome-isometric.png':
                image = Path(__file__).parent / 'assets/sophiedrop-folder-chrome-isometric.png'; data = image.read_bytes(); self.send_response(200); self.send_header('Content-Type','image/png'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
            parts = [unquote(p) for p in path.split('/') if p]; shares = state(); share = shares.get(parts[1]) if len(parts) >= 2 and parts[0] == 's' else None
            if len(parts) >= 2 and parts[0] == 'd': share = next((x for x in shares.values() if x.get('slug') == parts[1]), None)
            if not share: self.state_page('Share unavailable','This link is no longer available.'); return
            if share.get('revoked'): self.state_page('Share revoked','This link has been revoked by the sender.'); return
            if share['expires'] <= time.time(): self.state_page('Share expired','This link expired and is no longer available.'); return
            filename = Path(share['file'])
            if not filename.is_file() or (len(parts) >= 3 and parts[2] != filename.name): self.send_error(404); return
            if len(parts) == 2: self.share_page(share, filename, path); return
            self.download(filename)
        def share_page(self, share, filename, path):
            name = html.escape(filename.name); project = html.escape(share.get('slug') or filename.stem); expires = time.strftime('%d %b %Y · %H:%M UTC', time.gmtime(share['expires'])); count = share.get('file_count'); count_label = f'{count} files' if count is not None else 'Archive'; href = f'{path}/{quote(filename.name)}'; command = f"curl -fL -C - {shlex.quote('http://' + self.headers.get('Host','localhost:8787') + href)} -o {shlex.quote(filename.name)}"
            body = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>lilydrop · {name}</title><style>{CSS}</style></head><body><header><a class="brand" href="/">lilydrop</a></header><main><section class="hero"><div class="orb"><img src="/lilydrop-folder-chrome-isometric.png" alt=""></div><p class="kicker">LILYDROP</p><h1>Download files</h1><div class="card"><div class="file-row"><div class="file-name"><strong>{name}</strong><span>{count_label} · {human_size(filename.stat().st_size)}</span></div></div><div class="details"><div><span>PROJECT</span><strong>{project}</strong></div><div><span>EXPIRES</span><strong>{expires}</strong></div></div><div class="actions"><a class="download" href="{href}">Download <span>↗</span></a><button id="copy" type="button">Copy command</button></div><div class="command"><span>MORE INFO</span><code>{html.escape(command)}</code><button id="copy-inline" type="button">⧉</button></div></div><p id="status" role="status"></p><p class="fine-print">Resume supported · expires {expires}</p></section></main><script>const command={json.dumps(command)};async function copy(){{await navigator.clipboard.writeText(command);document.querySelector('#status').textContent='Copied';document.querySelector('#copy').textContent='Copied';}}document.querySelector('#copy').onclick=copy;document.querySelector('#copy-inline').onclick=copy;</script></body></html>'''.encode(); self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','private, no-store'); self.end_headers(); self.wfile.write(body)
        def download(self, filename):
            size = filename.stat().st_size; start, end, status = 0, size - 1, 200; header = self.headers.get('Range','')
            if header.startswith('bytes='):
                try:
                    first, last = (header[6:].split('-',1) + [''])[:2]; start = max(size-int(last),0) if not first else int(first); end = min(int(last),size-1) if last else end; status = 206
                    if start >= size or start > end: raise ValueError
                except (ValueError, IndexError): self.send_error(416); return
            self.send_response(status); self.send_header('Content-Length',str(end-start+1)); self.send_header('Accept-Ranges','bytes'); self.send_header('Content-Disposition',f'attachment; filename="{filename.name.replace(chr(34),"")}"'); self.send_header('Cache-Control','private, no-store');
            if status == 206: self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
            self.end_headers()
            if self.command == 'HEAD': return
            with filename.open('rb') as source:
                source.seek(start); remaining = end-start+1
                while remaining:
                    block = source.read(min(CHUNK,remaining))
                    if not block: break
                    self.wfile.write(block); remaining -= len(block)
        def do_HEAD(self): self.do_GET()
        def log_message(self, *_args): pass
    ThreadingHTTPServer(('127.0.0.1',8787), Handler).serve_forever()

if __name__ == '__main__': main()
