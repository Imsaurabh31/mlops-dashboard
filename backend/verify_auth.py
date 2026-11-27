"""Stage 4 Step 1 — Auth verification."""
import urllib.request, urllib.error, json, sys

BASE   = 'http://localhost:8000/api'
errors = []
passed = 0


def post(p, d):
    b   = json.dumps(d).encode()
    req = urllib.request.Request(BASE + p, data=b,
          headers={'Content-Type': 'application/json'}, method='POST')
    r = urllib.request.urlopen(req, timeout=5)
    return json.loads(r.read())


def get_auth(p, token):
    req = urllib.request.Request(BASE + p,
          headers={'Authorization': f'Bearer {token}'})
    r = urllib.request.urlopen(req, timeout=5)
    return json.loads(r.read())


def ok(n, msg):
    global passed; passed += 1; print(f'  PASS [{n:02d}] {msg}')


def fail(n, msg):
    errors.append(msg); print(f'  FAIL [{n:02d}] {msg}')


# 1. Admin login
try:
    r = post('/auth/login', {'email': 'admin@oly.com', 'password': 'admin123'})
    admin_token = r['access_token']
    assert r['user']['role'] == 'admin'
    ok(1, f'Admin login: {r["user"]["name"]} ({r["user"]["role"]})')
except Exception as e:
    fail(1, f'admin login: {e}')
    admin_token = None

# 2. Get /me
try:
    me = get_auth('/auth/me', admin_token)
    assert me['role'] == 'admin'
    ok(2, f'/me: {me["name"]}')
except Exception as e:
    fail(2, f'/me: {e}')

# 3. Permissions
try:
    p = get_auth('/auth/permissions', admin_token)
    assert 'admin' in p['permissions']
    ok(3, f'Admin permissions: {p["permissions"]}')
except Exception as e:
    fail(3, f'permissions: {e}')

# 4. Curator login
try:
    r = post('/auth/login', {'email': 'alice@oly.com', 'password': 'curator123'})
    curator_token = r['access_token']
    assert r['user']['role'] == 'curator'
    ok(4, f'Curator login: {r["user"]["name"]}')
except Exception as e:
    fail(4, f'curator login: {e}')
    curator_token = None

# 5. Curator permissions — no admin access
try:
    p = get_auth('/auth/permissions', curator_token)
    assert 'admin' not in p['permissions']
    assert 'curation' in p['permissions']
    ok(5, f'Curator permissions (no admin): {p["permissions"]}')
except Exception as e:
    fail(5, f'curator permissions: {e}')

# 6. Viewer login
try:
    r = post('/auth/login', {'email': 'viewer@oly.com', 'password': 'viewer123'})
    viewer_token = r['access_token']
    assert r['user']['role'] == 'viewer'
    ok(6, f'Viewer login: {r["user"]["name"]}')
except Exception as e:
    fail(6, f'viewer login: {e}')
    viewer_token = None

# 7. Wrong password → 401
try:
    try:
        post('/auth/login', {'email': 'admin@oly.com', 'password': 'wrongpass'})
        fail(7, 'should return 401')
    except urllib.error.HTTPError as he:
        assert he.code == 401
        ok(7, 'Wrong password returns 401')
except Exception as e:
    fail(7, f'wrong password: {e}')

# 8. Unknown email → 401
try:
    try:
        post('/auth/login', {'email': 'nobody@oly.com', 'password': 'test'})
        fail(8, 'should return 401')
    except urllib.error.HTTPError as he:
        assert he.code == 401
        ok(8, 'Unknown email returns 401')
except Exception as e:
    fail(8, f'unknown email: {e}')

# 9. No token → 401
try:
    try:
        req = urllib.request.Request(BASE + '/auth/me')
        urllib.request.urlopen(req, timeout=5)
        fail(9, 'should return 401 without token')
    except urllib.error.HTTPError as he:
        assert he.code == 401
        ok(9, 'No token returns 401')
except Exception as e:
    fail(9, f'no token: {e}')

# 10. List users — admin only
try:
    users = get_auth('/auth/users', admin_token)
    assert len(users) >= 4
    ok(10, f'Admin can list {len(users)} users')
except Exception as e:
    fail(10, f'list users: {e}')

# 11. Curator cannot list users → 403
try:
    try:
        get_auth('/auth/users', curator_token)
        fail(11, 'curator should not access /auth/users')
    except urllib.error.HTTPError as he:
        assert he.code == 403
        ok(11, 'Curator cannot list users (403)')
except Exception as e:
    fail(11, f'curator access guard: {e}')

# 12. Create user (admin) — use unique email each run
import time as _time
unique_email = f'test_{int(_time.time())}@oly.com'
try:
    b   = json.dumps({'name': 'Test User', 'email': unique_email, 'password': 'test1234', 'role': 'viewer'}).encode()
    req = urllib.request.Request(
        BASE + '/auth/users', data=b,
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {admin_token}'},
        method='POST',
    )
    r  = urllib.request.urlopen(req, timeout=5)
    nu = json.loads(r.read())
    assert nu['email'] == unique_email
    ok(12, f'Admin created user: {nu["name"]} ({nu["role"]})')
except Exception as e:
    fail(12, f'create user: {e}')

# Summary
print()
print(f'Auth results: {passed} passed, {len(errors)} failed')
if errors:
    for e in errors: print(f'  {e}')
    sys.exit(1)
else:
    print('All auth tests passed!')
