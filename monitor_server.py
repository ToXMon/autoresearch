#!/usr/bin/env python3
"""
Monitor Server - Simple HTTP server for Akash deployment

Serves results and logs from /data directory on port 8080.
This allows Akash to have a globally exposed service (required for valid SDL).
"""

import os
import http.server
import socketserver
from urllib.parse import unquote
from pathlib import Path

# Configuration
PORT = int(os.environ.get("MONITOR_PORT", 8080))
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/data/output"))
LOG_DIR = Path(os.environ.get("LOG_DIR", "/data/logs"))


class MonitorHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for serving output files and logs."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DATA_DIR), **kwargs)
    
    def do_GET(self):
        """Handle GET requests with custom routing."""
        path = unquote(self.path)
        
        # Route / to output directory listing
        if path == '/' or path == '':
            self.send_response(302)
            self.send_header('Location', '/output/')
            self.end_headers()
            return
        
        # Route /output to output directory
        if path.startswith('/output'):
            rel_path = path[7:]  # Remove '/output'
            if rel_path.startswith('/'):
                rel_path = rel_path[1:]
            self.serve_from_directory(OUTPUT_DIR, rel_path)
            return
        
        # Route /logs to log directory
        if path.startswith('/logs'):
            rel_path = path[5:]  # Remove '/logs'
            if rel_path.startswith('/'):
                rel_path = rel_path[1:]
            self.serve_from_directory(LOG_DIR, rel_path)
            return
        
        # Route /health for health checks
        if path == '/health' or path == '/healthz':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            return
        
        # Default: try to serve from DATA_DIR
        super().do_GET()
    
    def serve_from_directory(self, directory: Path, rel_path: str):
        """Serve a file or directory listing from specified directory."""
        target = directory / rel_path if rel_path else directory
        
        if not target.exists():
            self.send_error(404, f"Not found: {rel_path}")
            return
        
        if target.is_dir():
            # Generate directory listing
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            listing = self.generate_directory_listing(target, rel_path)
            self.wfile.write(listing.encode('utf-8'))
        else:
            # Serve the file
            self.send_response(200)
            self.guess_and_send_type(str(target))
            self.end_headers()
            with open(target, 'rb') as f:
                self.wfile.write(f.read())
    
    def generate_directory_listing(self, directory: Path, rel_path: str) -> str:
        """Generate HTML directory listing."""
        parent = str(directory.parent.relative_to(DATA_DIR)) if directory != DATA_DIR else ''
        
        lines = [
            '<!DOCTYPE html>',
            '<html><head>',
            f'<title>Index of /{rel_path}</title>',
            '<style>',
            'body { font-family: monospace; margin: 20px; }',
            'h1 { border-bottom: 1px solid #ccc; }',
            'table { border-collapse: collapse; }',
            'td, th { padding: 5px 15px; text-align: left; }',
            'a { text-decoration: none; color: #0066cc; }',
            'a:hover { text-decoration: underline; }',
            '.size { color: #666; }',
            '.dir { font-weight: bold; }',
            '</style>',
            '</head><body>',
            f'<h1>Index of /{rel_path}</h1>',
            '<table>',
            '<tr><th>Name</th><th>Size</th><th>Modified</th></tr>',
        ]
        
        if rel_path:
            lines.append(f'<tr><td class="dir"><a href="../">../</a></td><td>-</td><td>-</td></tr>')
        
        try:
            items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            items = []
        
        for item in items:
            name = item.name
            mtime = item.stat().st_mtime
            from datetime import datetime
            modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            
            if item.is_dir():
                lines.append(f'<tr><td class="dir"><a href="{name}/">{name}/</a></td><td>-</td><td>{modified}</td></tr>')
            else:
                size = item.stat().st_size
                if size >= 1024 * 1024:
                    size_str = f'{size / (1024*1024):.1f} MB'
                elif size >= 1024:
                    size_str = f'{size / 1024:.1f} KB'
                else:
                    size_str = f'{size} B'
                lines.append(f'<tr><td><a href="{name}">{name}</a></td><td class="size">{size_str}</td><td>{modified}</td></tr>')
        
        lines.extend(['</table>', '</body></html>'])
        return '\n'.join(lines)
    
    def guess_and_send_type(self, path):
        """Guess and send content type based on file extension."""
        path_lower = path.lower()
        if path_lower.endswith('.tsv'):
            self.send_header('Content-Type', 'text/tab-separated-values')
        elif path_lower.endswith('.csv'):
            self.send_header('Content-Type', 'text/csv')
        elif path_lower.endswith('.json'):
            self.send_header('Content-Type', 'application/json')
        elif path_lower.endswith('.log') or path_lower.endswith('.txt'):
            self.send_header('Content-Type', 'text/plain')
        elif path_lower.endswith('.png'):
            self.send_header('Content-Type', 'image/png')
        elif path_lower.endswith('.jpg') or path_lower.endswith('.jpeg'):
            self.send_header('Content-Type', 'image/jpeg')
        elif path_lower.endswith('.html'):
            self.send_header('Content-Type', 'text/html')
        else:
            self.send_header('Content-Type', 'application/octet-stream')
    
    def log_message(self, format, *args):
        """Log HTTP requests to stdout."""
        print(f"[Monitor] {self.address_string()} - {format % args}")


def main():
    """Start the monitor server."""
    # Ensure directories exist
    for d in [DATA_DIR, OUTPUT_DIR, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    
    with socketserver.TCPServer(("", PORT), MonitorHandler) as httpd:
        print(f"[Monitor] Server starting on port {PORT}")
        print(f"[Monitor] Serving files from:")
        print(f"[Monitor]   - Output: {OUTPUT_DIR} -> /output/")
        print(f"[Monitor]   - Logs:   {LOG_DIR} -> /logs/")
        print(f"[Monitor] Health check: /health")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
