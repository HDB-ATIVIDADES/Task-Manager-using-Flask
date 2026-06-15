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


import time
USER = f'u{int(time.time()) % 100000}'

print('=== Gerando trafego normal ===')

# 1. Registro
csrf = get_csrf('/register')
r = request('POST', '/register', {
    'csrf_token': csrf,
    'username': USER,
    'password': 'pass123',
    'confirm_password': 'pass123',
})
assert r.status == 200
assert 'Account Created' in r.read().decode()

# 2. Login
csrf = get_csrf('/login')
r = request('POST', '/login', {
    'csrf_token': csrf,
    'username': USER,
    'password': 'pass123',
})
assert r.status == 200
assert 'Welcome' in r.read().decode()

# 3. Criar 3 tarefas
for i in range(1, 4):
    csrf = get_csrf('/add_task')
    r = request('POST', '/add_task', {
        'csrf_token': csrf,
        'task_name': f'Tarefa normal {i}',
    })
    assert r.status == 200

print('Trafego normal gerado com sucesso')

# 4. Logout antes de simular brute-force
r = request('GET', '/logout')
assert r.status in (200, 302)

# 5. Simular brute-force: 10 tentativas de login com senha errada
print('=== Simulando ataque de forca bruta ===')
for i in range(10):
    csrf = get_csrf('/login')
    r = request('POST', '/login', {
        'csrf_token': csrf,
        'username': 'alice',
        'password': f'wrong{i}',
    })
    assert r.status == 200

print('10 tentativas de login invalidas geradas')

# 6. Login bem-sucedido (para mostrar contraste)
csrf = get_csrf('/login')
r = request('POST', '/login', {
    'csrf_token': csrf,
    'username': USER,
    'password': 'pass123',
})
assert r.status == 200
assert 'Welcome' in r.read().decode()

# 7. Logout
r = request('GET', '/logout')
assert r.status in (200, 302)

print('=== Trafego gerado com sucesso ===')
print('Verifique os logs no Loki ou no Grafana em http://localhost:3000')
