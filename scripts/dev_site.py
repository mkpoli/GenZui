"""Serve the built GenZui specimen with clean routes and no browser caching."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from sources import ROOT


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        target = Path(super().translate_path(path))
        if not target.suffix and target.with_suffix('.html').is_file():
            target = target.with_suffix('.html')
        return str(target)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=4173)
    parser.add_argument('--host', default='0.0.0.0')
    args = parser.parse_args()
    directory = ROOT/'build/site'
    if not (directory/'index.html').is_file():
        parser.error('Build the specimen site before starting the server.')
    server = ThreadingHTTPServer((args.host, args.port), partial(Handler, directory=str(directory)))
    print(f'GenZui site: http://localhost:{args.port}/', flush=True)
    print(f'Historical katakana: http://localhost:{args.port}/katakana', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
