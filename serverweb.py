import base64
import os
import json
import sys
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import List, Dict, Callable, Any
from urllib.parse import urlparse, parse_qs

from webcam import Metadata, File


class Cached:
    def __init__(self, provider: Callable[[], Any]):
        self.provider = provider
        self.value = provider()

    def __call__(self, *args, **kwargs):
        return self.value

    def refresh(self):
        self.value = self.provider()


class WebApi:
    pass


class RequestHandler(SimpleHTTPRequestHandler):
    metadata: Metadata = None
    auth_file = Path('.auth.txt')  # username:password see RFC 7617
    query_index = 4
    path_index = 2
    api: Dict[str, Callable] = None

    def __init__(self, *args, image_directory=None, directory=None, **kwargs):
        self.image_directory = image_directory
        self.init_class_once()
        super(RequestHandler, self).__init__(*args, directory=directory, **kwargs)

    def init_class_once(self):
        if RequestHandler.api is not None:
            return
        RequestHandler.api = {d: getattr(RequestHandler, d) for d in dir(RequestHandler) if d.startswith('API_')}
        self.metadata_refresh()

    def metadata_refresh(self):
        print('------========= refreshing metadata')
        RequestHandler.metadata = Metadata.from_folder(self.image_directory)

    def API_metadata_refresh(self):
        self.metadata_refresh()
        self.send_json({'result': 'ok'})

    def API_summary(self):
        self.send_json(self.metadata.summary)

    def API_group_summary(self, filename):
        self.send_json(self.metadata.group_summary(filename))

    def API_delete_group(self, filename):
        delete_list: List[File] = self.metadata.files[filename].group.files
        [os.remove(self.image_directory + '/' + f.name) for f in delete_list]
        self.send_json({'result': 'ok'})

    def API_image(self, filename):
        self.directory = self.image_directory
        self.path = '/' + filename
        super(RequestHandler, self).do_GET()

    def do_GET(self):
        params, rpath = self.decode_request()
        if rpath.startswith('/api/'):
            if not self.authorized():
                self.send_string('not authorized', code=401)
                return
            api_method = self.api.get('API_' + rpath[5:], None)
            if api_method is not None:
                api_method(self, **params)
            else:
                self.send_error(404, 'api not found')
        else:
            super(RequestHandler, self).do_GET()

    def decode_request(self):
        p = urlparse(self.path)
        query_str = p[self.query_index]
        rpath = p[self.path_index]
        di = parse_qs(query_str)
        params = {k: v[0] for k, v in di.items()}
        return params, rpath

    def send_json(self, obj):
        self.send_string(json.dumps(obj, indent=2))

    def send_string(self, message, code=200):
        self.protocol_version = "HTTP/1.1"
        self.send_response(code)
        self.send_header("Content-Length", str(len(message)))
        self.send_header("WWW-Authenticate", "Basic")
        self.end_headers()
        self.wfile.write(bytes(message, "utf8"))

    def authorized(self):
        if not self.auth_file.exists():
            return True
        auth_raw = self.headers.get('Authorization', '').split(' ')
        if len(auth_raw) != 2 or auth_raw[0] != 'Basic':
            return False
        auth_decoded = base64.b64decode(auth_raw[1]).decode('utf-8')
        return auth_decoded == self.auth_file.read_text()


def main():
    port = 8090
    print('starting server web on port %d...' % port)
    args = sys.argv[1:]
    image_directory = './test_files/flat_files' if len(args) == 0 else args[0]

    httpd = HTTPServer(('', port), partial(RequestHandler
                                           , image_directory=image_directory
                                           , directory='./wwwroot'))
    print('serving...')
    httpd.serve_forever()


if __name__ == '__main__':
    main()
