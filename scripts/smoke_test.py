import sys
import urllib.request
import urllib.parse
import http.cookiejar

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


# 1. Access login page
r = request('GET', '/login')
assert r.status == 200, f'GET /login returned {r.status}'

# 2. Register
r = request('POST', '/register', {
    'username': 'reviewer',
    'password': 'pass123',
    'confirm_password': 'pass123',
})
assert r.status == 200, f'POST /register returned {r.status}'
body = r.read().decode()
assert 'Login' in body, 'Register failed — no redirect to login'

# 3. Login
r = request('POST', '/login', {
    'username': 'reviewer',
    'password': 'pass123',
})
assert r.status == 200, f'POST /login returned {r.status}'
body = r.read().decode()
assert 'Add Task' in body or 'logout' in body.lower(), 'Login failed'

# 4. Add task
r = request('POST', '/add_task', {
    'task_name': 'Review smoke test task',
})
assert r.status in (200, 302), f'POST /add_task returned {r.status}'

# 5. Dashboard
r = request('GET', '/all_tasks')
assert r.status == 200, f'GET / returned {r.status}'
body = r.read().decode()
assert 'Review smoke test task' in body, 'Task not found on dashboard'

# 6. Logout
r = request('GET', '/logout')
assert r.status in (200, 302), f'GET /logout returned {r.status}'

print('All smoke tests passed')
