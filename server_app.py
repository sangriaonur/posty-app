import http.server
import socketserver
import json
import os
import time
from urllib.parse import unquote, parse_qs
from datetime import datetime

PORT = 3001
ROOT = os.path.dirname(__file__)
POSTS_DIR = os.path.join(ROOT, 'posts')

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # allow fetch from browser
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_GET(self):
        path = unquote(self.path)
        if path == '/new':
            self.handle_new_get()
            return
        if path.startswith('/api/posts'):
            self.handle_api_posts()
            return
        return super().do_GET()

    def do_POST(self):
        path = unquote(self.path)
        if path == '/new':
            self.handle_new_post()
            return
        self.send_error(404)

    def handle_api_posts(self):
        items = []
        if os.path.isdir(POSTS_DIR):
            for fname in sorted(os.listdir(POSTS_DIR), reverse=True):
                if not fname.lower().endswith('.md'):
                    continue
                fpath = os.path.join(POSTS_DIR, fname)
                title = None; author = None; date = None
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        for _ in range(20):
                            line = f.readline()
                            if not line:
                                break
                            s = line.strip()
                            if not s:
                                continue
                            if s.startswith('#') and not title:
                                title = s.lstrip('#').strip()
                            if s.lower().startswith('**author:**') and not author:
                                author = s.split(':',1)[1].strip().strip('*').strip()
                            if s.lower().startswith('**date:**') and not date:
                                date = s.split(':',1)[1].strip().strip('*').strip()
                except Exception:
                    pass
                items.append({
                    'title': title or fname,
                    'author': author,
                    'date': date,
                    'filename': fname,
                    'url': '/posts/' + fname
                })
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(items).encode('utf-8'))

    def handle_new_get(self):
        html = '''<!doctype html>
<html><head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width,initial-scale=1" />
<title>New Post — Posty</title>
<style>
body{font-family:Arial,sans-serif;background:#0e0f12;color:#ddd;margin:0;padding:20px}
.container{max-width:600px;margin:40px auto}
h1{color:#e85ec6}
label{display:block;margin-top:16px;font-weight:600}
input,textarea{width:100%;box-sizing:border-box;padding:10px;margin-top:6px;background:#1a1b1f;border:1px solid #333;color:#ddd;border-radius:6px;font-family:Arial,sans-serif}
textarea{min-height:300px;resize:vertical}
button{margin-top:20px;padding:10px 20px;background:#e85ec6;border:none;color:#000;font-weight:700;border-radius:6px;cursor:pointer}
button:hover{background:#f0a5d8}
</style>
</head><body>
<div class="container">
<h1>New Post</h1>
<form method="POST">
<label for="title">Title</label>
<input type="text" id="title" name="title" required />

<label for="author">Author</label>
<input type="text" id="author" name="author" value="SaNGRia" />

<label for="content">Content (Markdown)</label>
<textarea id="content" name="content" required></textarea>

<button type="submit">Publish</button>
</form>
</div>
</body></html>'''
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def handle_new_post(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = parse_qs(body)
        title = data.get('title', [''])[0]
        author = data.get('author', [''])[0]
        content = data.get('content', [''])[0]
        
        if not title or not content:
            self.send_error(400, 'Title and content required')
            return
        
        if not os.path.isdir(POSTS_DIR):
            os.makedirs(POSTS_DIR)
        
        now = datetime.now().strftime('%Y-%m-%d')
        fname = f"{now}-{title.lower().replace(' ', '-')[:30]}.md"
        fpath = os.path.join(POSTS_DIR, fname)
        
        post_content = f"# {title}\n\n**Author:** {author}\n**Date:** {now}\n\n{content}"
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(post_content)
        
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()


if __name__ == '__main__':
    os.chdir(ROOT)
    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        print(f"Serving on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('Stopping server')
            httpd.server_close()
