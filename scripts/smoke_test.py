import sys
import urllib.request
import urllib.parse
import http.cookiejar
import re

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5000'

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cj)
)


def request(method, path, data=None):
    url = BASE + path
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    if data:
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    return opener.open(req)


def get_csrf(path):
    r = request('GET', path)
    html = r.read().decode()
    match = re.search(r'name="csrf_token".*?value="([^"]+)"', html)
    assert match, f'csrf_token not found in {path}'
    return match.group(1)


# 1. Access login page
r = request('GET', '/login')
assert r.status == 200, f'GET /login returned {r.status}'

# 2. Register
csrf = get_csrf('/register')
r = request('POST', '/register', {
    'csrf_token': csrf,
    'username': 'reviewer',
    'password': 'pass123',
    'confirm_password': 'pass123',
})
assert r.status == 200, f'POST /register returned {r.status}'
body = r.read().decode()
assert 'Account Created' in body, 'Register failed'

# 3. Login
csrf = get_csrf('/login')
r = request('POST', '/login', {
    'csrf_token': csrf,
    'username': 'reviewer',
    'password': 'pass123',
})
assert r.status == 200, f'POST /login returned {r.status}'
body = r.read().decode()
assert 'Welcome' in body or 'logout' in body.lower(), 'Login failed'

# 4. Add task
csrf = get_csrf('/add_task')
r = request('POST', '/add_task', {
    'csrf_token': csrf,
    'task_name': 'Review smoke test task',
})
assert r.status == 200, f'POST /add_task returned {r.status}'

# 5. Dashboard
r = request('GET', '/all_tasks')
assert r.status == 200, f'GET /all_tasks returned {r.status}'
body = r.read().decode()
assert 'Review smoke test task' in body, 'Task not found on dashboard'

# 6. Logout
r = request('GET', '/logout')
assert r.status in (200, 302), f'GET /logout returned {r.status}'

print('All smoke tests passed')
