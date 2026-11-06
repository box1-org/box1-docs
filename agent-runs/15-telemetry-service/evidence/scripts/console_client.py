"""Logs in to the asset-service console through the real OIDC authorization-code flow and calls its control API.
Local test helper for box1-docs#15 Phase 4. Credentials are read from a local file and never printed."""
import html
import http.cookiejar
import json
import re
import urllib.error
import urllib.parse
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LocalPolicy(http.cookiejar.DefaultCookiePolicy):
    """Local Keycloak marks its cookies Secure; send them over http to localhost only."""
    def return_ok_secure(self, cookie, request):
        return request.host.split(':')[0] in ('localhost', '127.0.0.1') or super().return_ok_secure(cookie, request)


class Console:
    def __init__(self, base):
        self.base = base.rstrip('/')
        self.jar = http.cookiejar.CookieJar(LocalPolicy())
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), NoRedirect)

    def _open(self, request):
        try:
            return self.opener.open(request, timeout=20)
        except urllib.error.HTTPError as error:
            return error

    def login(self, username, password):
        response = self._open(urllib.request.Request(self.base + '/console/'))
        assert response.status == 302, response.status
        auth_url = response.headers['Location']
        page = self._open(urllib.request.Request(auth_url)).read().decode()
        action = html.unescape(re.search(r'<form[^>]*id="kc-form-login"[^>]*action="([^"]+)"', page).group(1))
        body = urllib.parse.urlencode({'username': username, 'password': password, 'credentialId': ''}).encode()
        response = self._open(urllib.request.Request(action, data=body, method='POST'))
        if response.status != 302:
            raise AssertionError('Keycloak did not accept the login: %s' % response.status)
        callback = response.headers['Location']
        hops = 0
        while hops < 5:
            response = self._open(urllib.request.Request(callback))
            if response.status not in (301, 302, 303):
                break
            callback = urllib.parse.urljoin(callback, response.headers['Location'])
            hops += 1
        return response.status

    def call(self, path, method='GET', body=None, console_header=True, content_type='application/json'):
        headers = {'Accept': 'application/json', 'X-Requested-With': 'JavaScript'}
        data = None
        if method != 'GET':
            if console_header:
                headers['X-Box1-Console'] = '1'
            headers['Content-Type'] = content_type
            data = json.dumps(body if body is not None else {}).encode()
        response = self._open(urllib.request.Request(self.base + path, data=data, method=method, headers=headers))
        text = response.read().decode()
        try:
            return response.status, json.loads(text) if text else None
        except json.JSONDecodeError:
            return response.status, text

    def cookie_header(self):
        return '; '.join('%s=%s' % (c.name, c.value) for c in self.jar if 'localhost' in c.domain)
