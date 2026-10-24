"""真实 loopback HTTP 认证/Origin/CSRF/路径与正文测试。"""
import http.client
import json
from pathlib import Path
import threading
import unittest
import contextlib
import io
import socket
import struct
from test_x2_runtime import Controller, request
from x2_web import make_server


class Client:
    def __init__(self, url):
        from urllib.parse import urlsplit
        parsed = urlsplit(url)
        self.host = parsed.netloc
        self.origin = 'http://' + self.host
        self.port = parsed.port
        self.token = parsed.fragment
        self.csrf = ''

    def send(self, method, path, value=None, headers=None, raw=None):
        body = raw if raw is not None else (json.dumps(value).encode() if value is not None else None)
        h = {'Host': self.host, 'Authorization': 'Bearer '+self.token}
        if method == 'POST':
            h.update({'Origin': self.origin, 'X-X2-CSRF': self.csrf, 'Content-Type': 'application/json'})
        for key, item in (headers or {}).items():
            if item is None:
                h.pop(key, None)
            else:
                h[key] = item
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=6)
        try:
            connection.request(method, path, body=body, headers=h)
            response = connection.getresponse()
            data = response.read()
            result = json.loads(data) if 'application/json' in response.getheader('Content-Type', '') else data
            return response.status, result, dict(response.getheaders())
        finally:
            connection.close()

    def bootstrap(self):
        status, result, _ = self.send('GET', '/api/bootstrap')
        if status != 200:
            raise AssertionError(result)
        self.csrf = result['csrf']
        return result['state']


class WebTests(unittest.TestCase):
    def setUp(self):
        self.c = Controller()
        self.server = make_server(self.c)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .05})
        self.thread.start()
        self.addCleanup(self.c.close)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.thread.join, 5)
        self.addCleanup(self.server.shutdown)
        self.client = Client(self.server.launch_url)
        self.client.bootstrap()

    def test_actual_auth_host_origin_csrf_rejections(self):
        client = self.client
        for headers, expected in (({'Authorization': None}, 'AUTH_DENIED'),
            ({'Authorization': 'Bearer bad'}, 'AUTH_DENIED'), ({'Host': 'localhost:'+str(client.port)}, 'HOST_DENIED'),
            ({'Host': 'evil.example'}, 'HOST_DENIED'), ({'Origin': None}, 'ORIGIN_DENIED'),
            ({'Origin': 'null'}, 'ORIGIN_DENIED'), ({'Origin': 'https://evil.example'}, 'ORIGIN_DENIED'),
            ({'X-X2-CSRF': None}, 'CSRF_DENIED'), ({'X-X2-CSRF': 'bad'}, 'CSRF_DENIED')):
            with self.subTest(headers=headers):
                status, value, returned = client.send('POST', '/api/new', {}, headers)
                self.assertEqual(status, 403)
                self.assertEqual(value['code'], expected)
                self.assertNotIn('Access-Control-Allow-Origin', returned)
        for path in ('/api/bootstrap', '/api/export'):
            self.assertEqual(client.send('GET', path, headers={'Authorization': None})[0], 403)
        self.assertEqual(self.c.state['sessions'], [])

    def test_routes_limits_fields_and_static_policy(self):
        c = self.client
        for path in ('/../x2.json', '/%2e%2e/x2.json', '/app.js?file=x2.json', '/api/source/foreign'):
            self.assertEqual(c.send('GET', path)[0], 404)
        for payload in ({'root': 'production'}, {'world': 'foreign'}, {'source': 'other'}):
            self.assertEqual(c.send('POST', '/api/new', payload)[1]['code'], 'FIELDS_INVALID')
        self.assertEqual(c.send('POST', '/api/new', {}, {'Content-Type':'text/plain'})[0], 403)
        self.assertEqual(c.send('POST', '/api/new', raw=b'x'*8193)[1]['code'], 'BODY_LIMIT_DENIED')
        self.assertEqual(c.send('POST', '/api/new', raw=b'{"a":1,"a":2}')[1]['code'], 'JSON_INVALID')
        self.assertEqual(c.send('OPTIONS', '/api/new')[0], 405)
        for path in ('/', '/app.js', '/style.css'):
            status, body, headers = c.send('GET', path, headers={'Authorization':None})
            self.assertEqual(status, 200)
            self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
            self.assertNotIn(c.token.encode(), body)
        js = c.send('GET', '/app.js')[1]
        self.assertNotIn(b'innerHTML', js)
        self.assertNotIn(b'eval(', js)

    def test_html_is_data_and_export_has_no_raw_text(self):
        c = self.client
        self.assertEqual(c.send('POST', '/api/new', {})[0], 200)
        html = '<script>window.X2_INJECTED=1</script>蓝灯书店'
        result = c.send('POST', '/api/turn', request(text=html))[1]
        self.assertEqual(result['turns'][0]['user'], html)
        c.send('POST', '/api/finish', request())
        state = c.bootstrap()
        c.send('POST', '/api/accept', request(revision=state['revision']))
        found = c.send('POST', '/api/query', {'query':'蓝灯书店'})[1]
        self.assertEqual(len(found['recalls']), 1)
        c.send('POST', '/api/feedback', {'rating':'confusing','reason':'ui'})
        export = json.dumps(c.send('GET', '/api/export')[1])
        for secret in (html, c.token, c.csrf, str(self.c.root)):
            self.assertNotIn(secret, export)
        self.assertNotIn(html.encode(), c.send('GET', '/')[1])

    def test_distinct_service_token_cannot_read_other_fixture(self):
        other = make_server(self.c)
        self.addCleanup(other.server_close)
        thread = threading.Thread(target=other.serve_forever, kwargs={'poll_interval':.05})
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(other.shutdown)
        foreign = Client(other.launch_url)
        foreign.token = self.client.token
        self.assertEqual(foreign.send('GET', '/api/bootstrap')[0], 403)

    def test_accept_committed_then_actual_http_connection_reset(self):
        client = self.client
        client.send('POST', '/api/new', {})
        client.send('POST', '/api/turn', request(text='蓝灯书店地图'))
        client.send('POST', '/api/finish', request())
        state = client.bootstrap()
        committed, release = threading.Event(), threading.Event()
        def fault(stage):
            if stage == 'after_accept':
                committed.set()
                if not release.wait(5):
                    raise RuntimeError('test synchronization failed')
        self.c.fault = fault
        payload = request(revision=state['revision'])
        body = json.dumps(payload).encode()
        wire = ('POST /api/accept HTTP/1.0\r\nHost: '+client.host+'\r\nOrigin: '+client.origin+
                '\r\nAuthorization: Bearer '+client.token+'\r\nX-X2-CSRF: '+client.csrf+
                '\r\nContent-Type: application/json\r\nContent-Length: '+str(len(body))+'\r\n\r\n').encode()+body
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            sock = socket.create_connection(('127.0.0.1', client.port), timeout=5)
            sock.sendall(wire)
            try:
                self.assertTrue(committed.wait(5))
                # SO_LINGER=0 强制 RST；Windows 的 linger 为两个 unsigned short。
                linger = struct.pack('HH' if __import__('os').name == 'nt' else 'ii', 1, 0)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, linger)
            finally:
                sock.close()
                release.set()
            self.c.fault = lambda stage: None
            result = client.bootstrap()
            self.assertEqual(result['phase'], 'accepted')
            self.assertEqual(len(result['recalls']), 1)
            self.assertEqual(client.send('POST','/api/accept',payload)[0], 200)
            self.assertEqual(self.c.export()['accepted'], 1)
        self.assertNotIn('Traceback', errors.getvalue())
        self.assertNotIn(str(self.c.root), errors.getvalue())
