"""固定路由的标准库 loopback HTTP；无 CORS、文件或模型代理。"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import hmac
import json
from pathlib import Path
import secrets
import socket
import sys
import threading
from socketserver import TCPServer

from x2_runtime import PACKAGE, X2Error
from x2_selection import RecallQueryError

MAX_BODY = 8192
STATIC = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'),
          '/style.css': ('style.css', 'text/css')}


def make_server(controller):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.0'

        def handle(self):
            try:
                super().handle()
            except (ConnectionError, OSError):
                # 客户端断连不能使已提交业务回滚，也不输出路径/请求/口令堆栈。
                print('HTTP_CONNECTION_CLOSED stage=transport', file=sys.stderr)

        def log_message(self, *args):
            pass

        def reply(self, status, value, content_type='application/json'):
            data = value if type(value) is bytes else json.dumps(value, ensure_ascii=False).encode('utf8')
            self.send_response(status)
            self.send_header('Content-Type', content_type + '; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'same-origin')
            self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
            self.end_headers()
            self.wfile.write(data)
            self.wfile.flush()
            # HTTP/1.0 每次关闭；先发 FIN，避免 Windows 丢弃带未读请求体的错误响应。
            try:
                self.connection.shutdown(socket.SHUT_WR)
            except OSError:
                pass

        def check(self, write=False):
            if self.headers.get_all('Host') != [server.expected_host]:
                raise X2Error('HOST_DENIED', 'http')
            if self.headers.get_all('Authorization') != ['Bearer ' + token]:
                raise X2Error('AUTH_DENIED', 'http')
            if write:
                if self.headers.get_all('Origin') != [server.origin]:
                    raise X2Error('ORIGIN_DENIED', 'http')
                value = self.headers.get('X-X2-CSRF', '')
                if not hmac.compare_digest(value, csrf) or len(self.headers.get_all('X-X2-CSRF', [])) != 1:
                    raise X2Error('CSRF_DENIED', 'http')

        def handle_error(self, error):
            self.reply(403 if error.code.endswith('DENIED') else 409,
                       dict(ok=False, code=error.code, stage=getattr(error, 'stage', 'query')))

        def do_GET(self):
            try:
                if self.headers.get_all('Host') != [server.expected_host]:
                    raise X2Error('HOST_DENIED', 'http')
                if self.path in STATIC:
                    name, mime = STATIC[self.path]
                    return self.reply(200, (PACKAGE / 'examples/x2' / name).read_bytes(), mime)
                if self.path == '/health':
                    return self.reply(200, dict(ok=True, mode='OFFLINE_REPLAY'))
                self.check()
                if self.path == '/api/bootstrap':
                    return self.reply(200, dict(csrf=csrf, state=controller.view()))
                if self.path == '/api/export':
                    return self.reply(200, controller.export())
                self.reply(404, dict(ok=False, code='ROUTE_UNKNOWN', stage='http'))
            except (X2Error, RecallQueryError) as error:
                self.handle_error(error)
            except Exception:
                self.reply(500, dict(ok=False, code='INTERNAL_FAILURE', stage='read'))

        def do_POST(self):
            try:
                lengths = self.headers.get_all('Content-Length', [])
                if len(lengths) != 1 or len(lengths[0]) > 6 or not lengths[0].isascii() or not lengths[0].isdigit() or not 0 < int(lengths[0]):
                    raise X2Error('BODY_LIMIT_DENIED', 'http')
                # 有界读取后认证；拒绝响应也不会因为未消费的小请求体被 Winsock RST 吞掉。
                raw = self.rfile.read(min(int(lengths[0]), MAX_BODY + 1))
                if int(lengths[0]) > MAX_BODY:
                    raise X2Error('BODY_LIMIT_DENIED', 'http')
                self.check(write=True)
                if (self.headers.get_all('Content-Type') != ['application/json']
                        or self.headers.get('Transfer-Encoding') is not None):
                    raise X2Error('CONTENT_TYPE_DENIED', 'http')
                if len(raw) != int(lengths[0]):
                    raise X2Error('BODY_INCOMPLETE', 'http')

                def unique(pairs):
                    result = {}
                    for key, value in pairs:
                        if key in result:
                            raise ValueError()
                        result[key] = value
                    return result

                try:
                    value = json.loads(raw.decode('utf8'), object_pairs_hook=unique)
                    if type(value) is not dict:
                        raise ValueError()
                except (ValueError, UnicodeError):
                    raise X2Error('JSON_INVALID', 'http') from None
                if self.path == '/api/query':
                    if set(value) != {'query'}:
                        raise X2Error('FIELDS_INVALID', 'http')
                    return self.reply(200, controller.view(value['query']))
                if self.path == '/api/stop':
                    if value:
                        raise X2Error('FIELDS_INVALID', 'http')
                    self.reply(200, dict(ok=True, code='STOPPING'))
                    threading.Thread(target=server.shutdown, daemon=True).start()
                    return
                routes = {('/api/' + k): k for k in ('new', 'turn', 'finish', 'accept', 'end', 'feedback')}
                if self.path not in routes:
                    return self.reply(404, dict(ok=False, code='ROUTE_UNKNOWN', stage='http'))
                self.reply(200, controller.mutate(routes[self.path], value))
            except (X2Error, RecallQueryError) as error:
                self.handle_error(error)
            except Exception:
                self.reply(500, dict(ok=False, code='INTERNAL_FAILURE', stage='mutation'))

        def do_OPTIONS(self):
            self.reply(405, dict(ok=False, code='METHOD_DENIED', stage='http'))

        do_PUT = do_DELETE = do_PATCH = do_OPTIONS

    class Server(HTTPServer):
        def server_bind(self):
            # 避免 HTTPServer 为日志名称调用 getfqdn/gethostbyaddr。
            TCPServer.server_bind(self)
            self.server_name = '127.0.0.1'
            self.server_port = self.server_address[1]

        def get_request(self):
            sock, address = super().get_request()
            sock.settimeout(3)
            return sock, address

    server = Server(('127.0.0.1', 0), Handler)
    server.expected_host = '127.0.0.1:' + str(server.server_port)
    server.origin = 'http://' + server.expected_host
    server.launch_url = server.origin + '/#' + token
    return server
