import http.server
import socketserver
import json
import os
from urllib.parse import unquote

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
        if path.startswith('/api/posts'):
            self.handle_api_posts()
            return
        return super().do_GET()

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


if __name__ == '__main__':
    os.chdir(ROOT)
    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        print(f"Serving on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('Stopping server')
            httpd.server_close()
