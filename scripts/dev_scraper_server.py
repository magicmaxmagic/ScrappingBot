#!/usr/bin/env python3
import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
import threading

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(ROOT, '..'))


def run_cmd(cmd, cwd=None, timeout=600):
    try:
        res = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True, timeout=timeout)
        return {
            'cmd': ' '.join(cmd),
            'code': res.returncode,
            'stdout': res.stdout[-4000:],
            'stderr': res.stderr[-4000:]
        }
    except subprocess.TimeoutExpired:
        return {
            'cmd': ' '.join(cmd),
            'code': -1,
            'stdout': '',
            'stderr': 'timeout'
        }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, data):
        body = json.dumps(data).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith('/health'):
            return self._send(200, {'ok': True})
        if self.path.startswith('/run'):
            return self._run()
        if self.path.startswith('/last'):
            last_path = os.path.join(ROOT, 'data', 'last_run.json')
            if os.path.exists(last_path):
                try:
                    with open(last_path, 'r') as f:
                        data = json.load(f)
                    return self._send(200, data)
                except Exception as e:
                    return self._send(500, {'ok': False, 'error': str(e)})
            return self._send(404, {'ok': False, 'error': 'no_last_run'})
        self._send(404, {'error': 'not_found'})

    def do_POST(self):
        if self.path.startswith('/run'):
            return self._run()
        self._send(404, {'error': 'not_found'})

    def _run(self):
        # Get request parameters for XHR scraper
        query_params = {}
        if hasattr(self, 'headers') and 'content-length' in self.headers:
            try:
                content_length = int(self.headers['content-length'])
                if content_length > 0:
                    post_data = self.rfile.read(content_length).decode('utf-8')
                    query_params = json.loads(post_data)
            except:
                pass
                
        # Extract CLI args for scrapers
        where = query_params.get('where', 'montreal/lachine')
        what = query_params.get('what', 'condo')
        when = query_params.get('when', '')
        scraper_type = query_params.get('scraper', 'auto')
        
        # Kick off a background thread to do the heavy work to avoid proxy timeouts
        def job(sources_override: str | None):
            steps = []
            env = os.environ.copy()
            if sources_override:
                env['SOURCES_FILE'] = sources_override
            
            # Choose scraper based on request
            if 'realtor' in what.lower() or 'realtor' in where.lower() or scraper_type == 'realtor':
                # Use clean production scraper
                clean_cmd = [
                    'python3', 'scraper/spiders/clean_scraper.py',
                    '--where', where,
                    '--what', what,
                    '--when', when,
                    '--source', 'realtor'
                ]
                if query_params.get('debug', False):
                    clean_cmd.append('--debug')
                    
                xhr_success = False
                try:
                    res1 = subprocess.run(clean_cmd, cwd=ROOT, capture_output=True, text=True, timeout=600)
                    steps.append({'cmd': ' '.join(clean_cmd), 'code': res1.returncode, 'stdout': res1.stdout[-4000:], 'stderr': res1.stderr[-4000:]})
                    xhr_success = (res1.returncode == 0)
                except subprocess.TimeoutExpired:
                    steps.append({'cmd': ' '.join(clean_cmd), 'code': -1, 'stdout': '', 'stderr': 'timeout'})
                    
                # Map realtor data with ETL if successful
                if xhr_success:
                    steps.append(run_cmd(['python3', 'etl/map_realtor.py', '--input', 'logs/preview_realtor.json', '--output', 'data/listings.json']))
            else:
                # Use generic Scrapy spider
                env['MAKE_CRAWL_EXTRA'] = "-s ROBOTSTXT_OBEY=false"
                try:
                    res1 = subprocess.run(['make', 'crawl'], cwd=ROOT, capture_output=True, text=True, timeout=600, env=env)
                    steps.append({'cmd': 'make crawl', 'code': res1.returncode, 'stdout': res1.stdout[-4000:], 'stderr': res1.stderr[-4000:]})
                except subprocess.TimeoutExpired:
                    steps.append({'cmd': 'make crawl', 'code': -1, 'stdout': '', 'stderr': 'timeout'})
                steps.append(run_cmd(['make', 'etl']))
            upload_sql = os.path.join(ROOT, 'data', 'upload.sql')
            if os.path.exists(upload_sql):
                # Clear existing listings to avoid mixing old local file:// rows with fresh live data
                steps.append(run_cmd(['npx', 'wrangler', 'd1', 'execute', 'estate-db', '--local', '--command', 'DELETE FROM listings;'], cwd=os.path.join(ROOT, 'workers')))
                steps.append(run_cmd(['npx', 'wrangler', 'd1', 'execute', 'estate-db', '--local', '--file', '../data/upload.sql'], cwd=os.path.join(ROOT, 'workers')))
                # Best-effort: clear KV cache so UI sees fresh results immediately
                try:
                    import urllib.request
                    req = urllib.request.Request('http://127.0.0.1:8787/api/admin/cache/clear', method='POST')
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        steps.append({'cmd': 'POST /api/admin/cache/clear', 'code': resp.status, 'stdout': resp.read().decode('utf-8')[-4000:], 'stderr': ''})
                except Exception as e:
                    steps.append({'cmd': 'POST /api/admin/cache/clear', 'code': 0, 'stdout': '', 'stderr': str(e)})
            # Write a last result file for the UI to read
            last_path = os.path.join(ROOT, 'data', 'last_run.json')
            try:
                report_path = os.path.join(ROOT, 'data', 'report.json')
                report = None
                if os.path.exists(report_path):
                    with open(report_path, 'r') as f:
                        report = json.load(f)
                # Small preview from listings.json if present
                preview = None
                items_path = os.path.join(ROOT, 'data', 'listings.json')
                if os.path.exists(items_path):
                    try:
                        with open(items_path, 'r') as f:
                            items = json.load(f)
                        if isinstance(items, list):
                            preview = items[:10]
                    except Exception:
                        preview = None
                ok = all(s['code'] == 0 for s in steps[:2])
                with open(last_path, 'w') as f:
                    json.dump({'ok': ok, 'steps': steps, 'report': report, 'preview': preview}, f)
            except Exception as e:
                with open(last_path, 'w') as f:
                    json.dump({'ok': False, 'error': str(e), 'steps': steps}, f)

        # Parse optional sources override from query string (?sources=/path/to.yml)
        src_override = None
        try:
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            src_override = qs.get('sources', [None])[0]
        except Exception:
            src_override = None

        # If POST body contains sources YAML/content, write to a temp file and use it
        if self.command == 'POST':
            try:
                length = int(self.headers.get('Content-Length') or 0)
                body = self.rfile.read(length) if length > 0 else b''
                if body:
                    payload = json.loads(body.decode('utf-8'))
                    content = payload.get('sources_yaml') or payload.get('sources_content') or payload.get('sources')
                    if isinstance(content, str) and content.strip():
                        from pathlib import Path
                        tmp_dir = Path(ROOT) / 'data' / 'tmp'
                        tmp_dir.mkdir(parents=True, exist_ok=True)
                        tmp_path = tmp_dir / 'sources_generated.yml'
                        tmp_path.write_text(content, encoding='utf-8')
                        src_override = str(tmp_path)
            except Exception:
                pass
        threading.Thread(target=job, args=(src_override,), daemon=True).start()
        self._send(202, {'ok': True, 'status': 'started', 'sources': src_override or 'default'})


def main():
    host = '127.0.0.1'
    port = int(os.environ.get('SCRAPER_SERVER_PORT', '8000'))
    try:
        httpd = HTTPServer((host, port), Handler)
    except OSError as e:
        # Port already in use: check if it's our server; if yes, exit quietly, else explain
        if getattr(e, 'errno', None) in (48, 98):
            try:
                with urllib.request.urlopen(f"http://{host}:{port}/health", timeout=2) as r:
                    if r.status == 200:
                        print(f"Scraper dev server already running at http://{host}:{port}")
                        return
            except Exception:
                pass
            print(f"ERROR: Port {port} in use. Stop existing process (make scraper-dev-stop) or set SCRAPER_SERVER_PORT to another port.")
            return
        else:
            raise
    print(f"Scraper dev server listening on http://{host}:{port}")
    httpd.serve_forever()


if __name__ == '__main__':
    main()
