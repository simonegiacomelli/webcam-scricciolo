import os
import json
import sys
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import List, Dict, Callable
from urllib.parse import urlparse, parse_qs

from webcam import Metadata, File


class RequestHandler(SimpleHTTPRequestHandler):
    metadata: Metadata = None
    query_index = 4
    path_index = 2
    api: Dict[str, Callable] = None

    def __init__(self, *args, image_directory=None, directory=None, **kwargs):
        self.image_directory = image_directory
        self.init_class_once()
        super(RequestHandler, self).__init__(*args, directory=directory, **kwargs)

    def init_class_once(self):
        if self.api is not None:
            return
        self.api = {d: getattr(RequestHandler, d) for d in dir(RequestHandler) if d.startswith('API_')}
        self.metadata_refresh()

    def metadata_refresh(self):
        self.metadata = Metadata.from_folder(self.image_directory)

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
        print(['serving to', self.image_directory, self.path])
        super(RequestHandler, self).do_GET()

    def do_GET(self):
        print('--------API', self.api)
        params, rpath = self.decode_request()
        if rpath.startswith('/api/'):
            m = self.api.get('API_' + rpath[5:], None)
            if m is not None:
                m(self, **params)
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

    def send_string(self, message):
        self.protocol_version = "HTTP/1.1"
        self.send_response(200)
        self.send_header("Content-Length", str(len(message)))
        self.end_headers()
        self.wfile.write(bytes(message, "utf8"))


def main():
    port = 8090
    print('starting server web on port %d...' % port)
    args = sys.argv[1:]
    image_directory = './test_files/flat_files' if len(sys.argv) == 0 else args[0]

    httpd = HTTPServer(('', port), partial(RequestHandler
                                           , image_directory=image_directory
                                           , directory='./wwwroot'))
    print('serving...')
    httpd.serve_forever()


if __name__ == '__main__':
    main()
