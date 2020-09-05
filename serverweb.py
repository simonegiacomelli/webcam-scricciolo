import base64
import json
import sys
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from time import sleep
from typing import Callable
from urllib.parse import urlparse, parse_qs

from dispatch import Dispatch
from webcam import Metadata, WebApi, RefreshableCache


class RequestHandler(SimpleHTTPRequestHandler):
    auth_file = Path('.auth.txt')  # username:password see RFC 7617
    query_index = 4
    path_index = 2

    def __init__(self, *args, refreshable_metadata: RefreshableCache[Metadata]
                 , api_dispatch: Dispatch
                 , image_directory=None, directory=None, **kwargs):
        self.api_dispatch = api_dispatch
        self.refreshable_metadata = refreshable_metadata
        self.image_directory = image_directory
        self.new_web_api = partial(WebApi, self.refreshable_metadata, image_directory=image_directory, response=self)
        super(RequestHandler, self).__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        params, rpath = self.decode_request()
        if rpath.startswith('/api/'):
            api_name = rpath[5:]
            if not self.authorized():
                self.send_string('not authorized', code=401)
                return
            instance = self.new_web_api()
            result = self.api_dispatch.dispatch(instance, api_name, params)
            if result is not None:
                self.send_json(result)
            # self.send_error(404, 'api not found')
        else:
            super(RequestHandler, self).do_GET()

    def decode_request(self):
        p = urlparse(self.path)
        query_str = p[self.query_index]
        rpath = p[self.path_index]
        di = parse_qs(query_str)
        params = {k: v[0] for k, v in di.items()}
        return params, rpath

    def authorized(self):
        if not self.auth_file.exists():
            return True
        auth_raw = self.headers.get('Authorization', '').split(' ')
        if len(auth_raw) != 2 or auth_raw[0] != 'Basic':
            return False
        auth_decoded = base64.b64decode(auth_raw[1]).decode('utf-8')
        return auth_decoded == self.auth_file.read_text()

    def send_json(self, obj):
        self.send_string(json.dumps(obj, indent=2))

    def send_string(self, message, code=200):
        self.protocol_version = "HTTP/1.1"
        self.send_response(code)
        self.send_header("Content-Length", str(len(message)))
        self.send_header("WWW-Authenticate", "Basic")
        self.end_headers()
        self.wfile.write(bytes(message, "utf8"))

    def serve_file(self, directory, filename):
        self.directory = directory
        self.path = '/' + filename
        super(RequestHandler, self).do_GET()


def wait_file_changes(file):
    self_file = Path(file)
    initial_st_mtime = self_file.stat().st_mtime
    try:
        while self_file.stat().st_mtime == initial_st_mtime:
            sleep(0.5)
    except KeyboardInterrupt as ex:
        return False

    print('File changed! Exiting...')
    return True


def main():
    port = 8090
    print('Starting server web v1.1 on port %d...' % port)
    args = sys.argv[1:]
    image_directory = './test_files/flat_files' if len(args) == 0 else args[0]

    refreshable_metadata = RefreshableCache(lambda: Metadata.from_folder(image_directory))
    api_dispatch = Dispatch().register(WebApi, 'API_')
    httpd = HTTPServer(('', port), partial(RequestHandler
                                           , refreshable_metadata=refreshable_metadata
                                           , api_dispatch=api_dispatch
                                           , image_directory=image_directory
                                           , directory='./wwwroot'))
    httpd.timeout = 10

    print('serving...')
    Thread(target=httpd.serve_forever).start()
    changed = wait_file_changes(__file__)
    httpd.shutdown()
    sys.exit(4 if changed else 0)


if __name__ == '__main__':
    main()
