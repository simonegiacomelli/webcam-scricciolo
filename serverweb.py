import base64
import json
import os
import sys
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import List, Dict, Callable, Union
from urllib.parse import urlparse, parse_qs

from webcam import Metadata, File, WebApi, RefreshableCache


class MethodNotRegistered(Exception):
    pass


class Dispatch:
    def __init__(self, ):
        self.registered = {}
        self.prefix: str = None

    def register(self, clazz, prefix):
        self.registered = {d[len(prefix):]: getattr(clazz, d) for d in dir(clazz) if d.startswith(prefix)}
        self.prefix = prefix
        return self

    def dispatch(self, instance, method_name, params: Dict = {}):
        if method_name not in self.registered.keys():
            raise MethodNotRegistered(method_name)
        m = getattr(instance, self.prefix + method_name)
        return m(**params)


class RequestHandler(SimpleHTTPRequestHandler):
    auth_file = Path('.auth.txt')  # username:password see RFC 7617
    query_index = 4
    path_index = 2
    api: Dict[str, Callable] = None

    def __init__(self, *args, refreshable_metadata: RefreshableCache[Metadata]
                 , api_dispatch: Dispatch
                 , image_directory=None, directory=None, **kwargs):
        self.api_dispatch = api_dispatch
        self.refreshable_metadata = refreshable_metadata
        self.image_directory = image_directory
        self.init_class_once()
        super(RequestHandler, self).__init__(*args, directory=directory, **kwargs)

    def init_class_once(self):
        if RequestHandler.api is not None:
            return
        RequestHandler.api = {d: getattr(RequestHandler, d) for d in dir(RequestHandler) if d.startswith('API_')}

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
            api_name = rpath[5:]
            if not self.authorized():
                self.send_string('not authorized', code=401)
                return
            if api_name in {'days', 'summary', 'group_summary', 'metadata_refresh'}:
                instance = WebApi(self.refreshable_metadata)
                result = self.api_dispatch.dispatch(instance, api_name, params)
                if result is not None:
                    self.send_json(result)
            else:
                api_method = self.api.get('API_' + api_name, None)
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

    refreshable_metadata = RefreshableCache(lambda: Metadata.from_folder(image_directory))
    api_dispatch = Dispatch().register(WebApi, 'API_')
    httpd = HTTPServer(('', port), partial(RequestHandler
                                           , refreshable_metadata=refreshable_metadata
                                           , api_dispatch=api_dispatch
                                           , image_directory=image_directory
                                           , directory='./wwwroot'))
    print('serving...')
    httpd.serve_forever()


if __name__ == '__main__':
    main()
