#!/run/current-system/sw/bin/python3
import argparse,json,secrets,time,html,os
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
S=Path(os.environ.get('LILYDROP_STATE', str(Path.home()/'.local/state/lilydrop/shares.json')))
CHUNK=1024*1024
def human_size(n):
 for unit in ('B','KB','MB','GB','TB'):
  if n < 1024 or unit == 'TB': return f'{n:.1f} {unit}' if unit != 'B' else f'{n} B'
  n /= 1024
def state(): return json.loads(S.read_text() or '{}') if S.exists() else {}
def save(x):
 S.parent.mkdir(parents=True,exist_ok=True); t=S.with_suffix('.tmp'); t.write_text(json.dumps(x)); t.replace(S)
def main():
 p=argparse.ArgumentParser(); q=p.add_subparsers(dest='c',required=True); a=q.add_parser('publish'); a.add_argument('file'); a.add_argument('--days',type=int,default=7); a.add_argument('--slug',help='short public alias, for example vexian2026'); a.add_argument('--base-url',default='https://files.navylily.tv'); b=q.add_parser('revoke'); b.add_argument('token'); q.add_parser('serve'); x=p.parse_args()
 if x.c=='publish':
   d=state(); t=secrets.token_urlsafe(32); record={'file':str(Path(x.file).resolve()),'expires':time.time()+x.days*86400};
   if x.slug:
    if not x.slug.replace('-', '').replace('_', '').isalnum(): p.error('--slug must contain only letters, numbers, hyphens, or underscores')
    if any(v.get('slug') == x.slug for v in d.values()): p.error(f'slug already exists: {x.slug}')
    record['slug']=x.slug
   d[t]=record; save(d); print(f'{x.base_url.rstrip("/")}/{"d/" + x.slug if x.slug else "s/" + t}')
 elif x.c=='revoke': d=state(); d.pop(x.token,None); save(d)
 else:
  class H(BaseHTTPRequestHandler):
   def do_GET(self):
    from urllib.parse import urlparse, unquote
    request_path=urlparse(self.path).path
    if request_path in ('/pictogrep-studio/web/pictogrep.css', '/pictogrep-studio/web/style.css'):
     css=Path(__file__).resolve().parents[1]/request_path.lstrip('/')
     if not css.is_file(): self.send_error(404); return
     data=css.read_bytes(); self.send_response(200); self.send_header('Content-Type','text/css; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','public, max-age=3600'); self.end_headers(); self.wfile.write(data); return
    if request_path == '/lilydrop-folder-chrome-isometric.png':
     image=Path(__file__).resolve().parents[1]/'threejs/assets/sophiedrop-folder-chrome-isometric.png'
     if not image.is_file(): self.send_error(404); return
     data=image.read_bytes(); self.send_response(200); self.send_header('Content-Type','image/png'); self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','public, max-age=3600'); self.end_headers(); self.wfile.write(data); return
    z=[unquote(p) for p in request_path.split('/') if p]; d=state(); v=None
    if len(z)>=2 and z[0] == 's': v=d.get(z[1])
    elif len(z)>=2 and z[0] == 'd':
     v=next((share for share in d.values() if share.get('slug') == z[1]), None)
    f=Path(v['file']) if v and v['expires']>time.time() else None
    if not f or (len(z)>=3 and z[2]!=f.name) or not f.is_file(): self.send_error(404); return
    if len(z)==2:
     expires=time.strftime('%Y-%m-%d %H:%M UTC',time.gmtime(v['expires'])); name=html.escape(f.name); size=f.stat().st_size; size_label=human_size(size)
     href=html.escape(f'{urlparse(self.path).path}/{name}', quote=True)
     body=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SophieDrop · {name}</title><link rel="stylesheet" href="/pictogrep-studio/web/pictogrep.css"><link rel="stylesheet" href="/pictogrep-studio/web/style.css"><style>.drop-card{{max-width:680px;margin:0 auto;text-align:left}}.drop-meta{{display:grid;grid-template-columns:repeat(2,1fr);gap:1px;margin:32px 0;background:var(--line)}}.drop-meta div{{padding:16px;background:var(--bg)}}.drop-meta small{{display:block;color:var(--fg-muted);font-size:12px;margin-bottom:5px}}.drop-meta strong{{font-size:15px;overflow-wrap:anywhere}}.drop-actions{{display:flex;gap:10px;flex-wrap:wrap}}.drop-actions a.primary{{display:inline-flex;align-items:center;min-height:var(--control-height);padding:0 var(--space-3);border:1px solid var(--fg);background:var(--fg);color:var(--on-fg);text-decoration:none}}.drop-actions a.primary:hover{{background:var(--fg-hover)}}.drop-actions button{{color:var(--fg);background:var(--bg)}}.drop-note{{margin-top:24px;color:var(--fg-muted);font-size:13px;line-height:1.5}}@media(max-width:560px){{.drop-meta{{grid-template-columns:1fr}}}}</style></head><body class="full-width studio"><header class="app-header"><span class="wordmark">sophiedrop <small>asset delivery</small></span></header><main id="main" class="main-content"><section class="welcome drop-card"><p class="eyebrow">CLIENT DELIVERY</p><h1>Download assets</h1><p>Everything prepared for your project.</p><div class="drop-meta"><div><small>Archive</small><strong>{name}</strong></div><div><small>Size</small><strong>{size_label}</strong></div><div><small>Access</small><strong>Private share link</strong></div><div><small>Available until</small><strong>{expires}</strong></div></div><div class="drop-actions"><a class="primary" href="{href}">Download assets <span aria-hidden="true">↗</span></a><button id="copy" type="button">Copy agent command</button></div><p class="drop-note">The archive contains the original-quality files. Downloads can resume if interrupted. This share closes automatically at the time shown above.</p><p id="status" role="status"></p></section></main><script>document.querySelector('#copy').onclick=async()=>{{await navigator.clipboard.writeText(`curl -fL -C - '${{location.origin}}{href}' -o '{name}'`);document.querySelector('#status').textContent='Agent command copied.'}}</script></body></html>'''.encode()
     body=body.replace(b'</title>', b'</title><link rel="icon" href="/lilydrop-folder-chrome-isometric.png">', 1)
     body=body.replace(b'<section class="welcome drop-card">', b'<section class="welcome drop-card"><img src="/lilydrop-folder-chrome-isometric.png" alt="" style="display:block;width:min(320px,70vw);margin:0 auto 24px">')
     body=body.replace(b'SophieDrop', b'lilydrop').replace(b'sophiedrop-folder-chrome-isometric.png', b'lilydrop-folder-chrome-isometric.png')
     body=body.replace(b'</style>', b'.drop-card{padding:clamp(20px,5vw,48px);border:1px solid var(--line);border-radius:var(--radius-lg);background:var(--bg);box-shadow:var(--shadow-overlay)}.drop-meta{gap:12px;margin:24px 0}.drop-meta div{border:1px solid var(--line);border-radius:var(--radius-md);padding:16px 18px}.drop-meta small{letter-spacing:.04em;text-transform:uppercase}.agent-command{margin:16px 0;overflow:auto;padding:12px 14px;border:1px solid var(--line);border-radius:var(--radius-md);background:var(--bg-sunken);font-size:12px;line-height:1.5}.agent-command code{white-space:pre-wrap;overflow-wrap:anywhere}.drop-actions{margin-top:4px}</style>', 1)
     body=body.replace(b'</style>', b'body{background:#fff;color:#171717}.app-header{border-bottom:0;justify-content:center}.wordmark{color:#171717}.drop-card{width:min(100%,560px);margin:0 auto;padding:28px 24px;border:0;box-shadow:none;background:#fff;text-align:center!important;align-items:center}.drop-card>img{order:-2;width:min(150px,42vw)!important;margin:18px auto 24px!important}.drop-card h1{font-size:0;margin:0}.drop-card h1:after{content:"lilydrop";font-size:28px}.drop-card>p:not(.eyebrow):not(.drop-note):not(#status){display:none}.drop-meta{width:100%;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:22px 0}.drop-meta div{min-height:88px;display:flex;flex-direction:column;justify-content:center;text-align:left;border:1px solid #d8d8d5;border-radius:12px;background:#fafaf8}.drop-meta small{color:#6b6b67}.drop-meta strong{color:#171717}.drop-actions{order:-1;width:100%;display:grid;grid-template-columns:1fr 1fr;gap:8px}.drop-actions a.primary,.drop-actions button{justify-content:center;min-height:44px;border-radius:8px}.agent-command{display:none}.drop-note{width:100%;margin:22px 0 0!important;padding-top:18px;border-top:1px solid #e4e4e0;color:#6b6b67;text-align:left;font-size:13px}.drop-note:before{display:block;margin-bottom:8px;color:#171717;font-size:15px;content:"More info"}@media(max-width:420px){.drop-card{padding:20px 16px}.drop-meta{gap:8px}.drop-meta div{padding:12px;min-height:80px}.drop-meta strong{font-size:13px}}</style>', 1)
     body=body.replace(b'Download assets', b'Download', 1).replace(b'Copy agent command', b'Copy for agent', 1)
     command=f"curl -fL -C - '{urlparse(self.path).scheme or 'https'}://{self.headers.get('Host','files.navylily.tv')}{urlparse(self.path).path}/{f.name}' -o '{f.name}'"
     body=body.replace(b'<div class="drop-actions">', b'<p class="agent-command"><code>'+html.escape(command).encode()+b'</code></p><div class="drop-actions">')
     body=body.replace(b'.drop-card{', b'.drop-card{text-align:left!important;display:flex;flex-direction:column;}.drop-card>img{order:-2}')
     body=body.replace(b'.drop-actions{', b'.drop-actions{order:-1;')
     body=body.replace(b'width:min(320px,70vw)', b'width:min(180px,42vw)')
     self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','private, no-store'); self.end_headers();
     if self.command != 'HEAD': self.wfile.write(body)
     return
    size=f.stat().st_size; start=0; end=size-1; status=200; r=self.headers.get('Range','')
    if r.startswith('bytes='):
     try: a,b=(r[6:].split('-',1)+[''])[:2]; start=int(a or 0); end=int(b or end); end=min(end,size-1)
     except ValueError: self.send_error(416); return
     if start>=size or start>end: self.send_error(416); return
     status=206
    self.send_response(status); self.send_header('Content-Length',str(end-start+1)); self.send_header('Accept-Ranges','bytes'); self.send_header('Content-Disposition',f'attachment; filename="{html.escape(f.name,quote=True)}"'); self.send_header('Cache-Control','private, no-store')
    if status==206: self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
    self.end_headers()
    if self.command=='HEAD': return
    with f.open('rb') as src:
     src.seek(start); left=end-start+1
     while left:
      block=src.read(min(CHUNK,left))
      if not block: break
      self.wfile.write(block); left-=len(block)
   def do_HEAD(self): self.do_GET()
   def log_message(self,*a): pass
  ThreadingHTTPServer(('127.0.0.1',8787),H).serve_forever()
main()
