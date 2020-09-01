import json
import sys
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from webcam import Metadata


class RequestHandler(SimpleHTTPRequestHandler):
    _metadata: Metadata = None
    query_index = 4
    path_index = 2

    def __init__(self, *args, image_directory=None, directory=None, **kwargs):
        self.image_directory = image_directory
        super(RequestHandler, self).__init__(*args, directory=directory, **kwargs)

    @property
    def metadata(self) -> Metadata:
        if RequestHandler._metadata is None:
            self.metadata_refresh()
        return RequestHandler._metadata

    def metadata_refresh(self):
        RequestHandler._metadata = Metadata.from_folder(self.image_directory)

    def summary(self):
        self.send_json(self.metadata.summary)

    def group_summary(self, filename):
        self.send_json(self.metadata.group_summary(filename))

    def serve_file(self, directory, filename):
        self.directory = directory
        self.path = '/' + filename
        print(['serving to', self.image_directory, self.path])
        super(RequestHandler, self).do_GET()

    def do_GET(self):
        print([self.path, self.directory])
        p = urlparse(self.path)
        query_str = p[self.query_index]
        rpath = p[self.path_index]
        di = parse_qs(query_str)
        print(di)
        params = {k: v[0] for k, v in di.items()}

        if rpath.startswith('/api/'):
            if rpath == '/api/image':
                self.serve_file(self.image_directory, params['filename'])
            elif rpath == '/api/summary':
                self.summary()
            elif rpath == '/api/group_summary':
                self.group_summary(params['filename'])
            elif rpath == '/api/metadata_refresh':
                self.metadata_refresh()
                self.send_json({'result': 'ok'})

        else:
            super(RequestHandler, self).do_GET()

    def send_json(self, obj):
        self.send_string(json.dumps(obj, indent=2))

    def send_string(self, message):
        self.protocol_version = "HTTP/1.1"
        self.send_response(200)
        self.send_header("Content-Length", str(len(message)))
        self.end_headers()
        self.wfile.write(bytes(message, "utf8"))


def main():
    print('starting server web...')
    args = sys.argv[1:]
    if len(args) > 0:
        image_directory = args[0]
    else:
        image_directory = './test_files/flat_files'

    server = ('', 8000)

    httpd = HTTPServer(server, partial(RequestHandler
                                       , image_directory=image_directory
                                       , directory='./wwwroot'))
    print('serving...')
    httpd.serve_forever()


if __name__ == '__main__':
    main()
