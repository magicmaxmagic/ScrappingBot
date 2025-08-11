#!/usr/bin/env python3
import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
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
        # Kick off a background thread to do the heavy work to avoid proxy timeouts
        def job(sources_override: str | None):
            steps = []
            env = os.environ.copy()
            if sources_override:
                env['SOURCES_FILE'] = sources_override
            # Dev ergonomics: ignore robots to allow test during dev
            env['MAKE_CRAWL_EXTRA'] = "-s ROBOTSTXT_OBEY=false"
            # run crawl with optional SOURCES_FILE env
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
                ok = all(s['code'] == 0 for s in steps[:2])
                with open(last_path, 'w') as f:
                    json.dump({'ok': ok, 'steps': steps, 'report': report}, f)
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
        threading.Thread(target=job, args=(src_override,), daemon=True).start()
        self._send(202, {'ok': True, 'status': 'started', 'sources': src_override or 'default'})


def main():
    host = '127.0.0.1'
    port = int(os.environ.get('SCRAPER_SERVER_PORT', '8000'))
    httpd = HTTPServer((host, port), Handler)
    print(f"Scraper dev server listening on http://{host}:{port}")
    httpd.serve_forever()


if __name__ == '__main__':
    main()
