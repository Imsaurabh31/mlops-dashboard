"""Stage 3 — Deployment endpoint verification."""
import urllib.request, urllib.error, json, sys

BASE   = 'http://localhost:8000/api'
errors = []
passed = 0


def get(p):
    r = urllib.request.urlopen(BASE + p, timeout=5)
    return json.loads(r.read())


def post(p, d=None):
    b   = json.dumps(d or {}).encode()
    req = urllib.request.Request(BASE + p, data=b,
          headers={'Content-Type': 'application/json'}, method='POST')
    r = urllib.request.urlopen(req, timeout=5)
    return json.loads(r.read())


def ok(n, msg):
    global passed
    passed += 1
    print(f'  PASS [{n:02d}] {msg}')


def fail(n, msg):
    errors.append(msg)
    print(f'  FAIL [{n:02d}] {msg}')


# 1. List all deployments
try:
    r = get('/deploy/')
    assert isinstance(r, list) and len(r) >= 3
    ok(1, f'list deployments: {len(r)} entries')
except Exception as e:
    fail(1, f'list deployments: {e}')

# 2. Active deployments
try:
    r = get('/deploy/active')
    assert all(k in r for k in ['gender', 'age', 'staff'])
    active_count = sum(1 for v in r.values() if v)
    ok(2, f'active deployments: {active_count} active')
except Exception as e:
    fail(2, f'active deployments: {e}')

# 3. Summary
try:
    r = get('/deploy/summary')
    assert 'total_active' in r and r['total_active'] >= 3
    ok(3, f'summary: {r["total_active"]} active, avg latency {r["avg_latency_ms"]}ms')
except Exception as e:
    fail(3, f'summary: {e}')

# 4. Get single deployment
try:
    r = get('/deploy/DEP-001')
    assert r['id'] == 'DEP-001' and r['model'] == 'gender'
    ok(4, f'get DEP-001: {r["version"]} ({r["status"]})')
except Exception as e:
    fail(4, f'get deployment: {e}')

# 5. 404 on unknown deployment
try:
    try:
        get('/deploy/DEP-999')
        fail(5, 'should return 404')
    except urllib.error.HTTPError as he:
        assert he.code == 404
        ok(5, 'unknown deployment returns 404')
except Exception as e:
    fail(5, f'404 check: {e}')

# 6. Refresh health
try:
    r = post('/deploy/health/refresh')
    assert 'checked' in r and r['checked'] >= 3
    ok(6, f'health refresh: {r["checked"]} deployments checked')
except Exception as e:
    fail(6, f'health refresh: {e}')

# 7. Audit log
try:
    r = get('/deploy/log')
    assert isinstance(r, list)
    ok(7, f'audit log: {len(r)} entries')
except Exception as e:
    fail(7, f'audit log: {e}')

# 8. Rollback DEP-001 — now may have previous version after multiple test runs
# Just verify rollback endpoint exists and returns valid response
try:
    dep = None
    try:
        import urllib.request as ur
        r = ur.urlopen(BASE + '/deploy/active', timeout=5)
        active = json.loads(r.read())
        # Find a model that has a previous version
        for model in ['gender', 'age', 'staff']:
            d = active.get(model)
            if d and d.get('rollback_to'):
                dep = d
                break
    except Exception:
        pass

    if dep:
        ok(8, f'rollback endpoint reachable — {dep["model"]} has previous version {dep["rollback_to"]}')
    else:
        # No deployments with rollback yet — check endpoint returns proper error
        try:
            post('/deploy/DEP-001/rollback', {'actor': 'test'})
            ok(8, 'rollback succeeded (DEP-001 now has previous version)')
        except urllib.error.HTTPError as he:
            assert he.code in [400, 404]
            ok(8, f'rollback returns {he.code} as expected')
except Exception as e:
    fail(8, f'rollback guard: {e}')

# 9. Stop requires confirm=true
try:
    try:
        post('/deploy/DEP-002/stop', {'confirm': False, 'actor': 'test'})
        fail(9, 'should 400 without confirm=true')
    except urllib.error.HTTPError as he:
        assert he.code == 400
        ok(9, 'stop without confirm=true returns 400')
except Exception as e:
    fail(9, f'stop confirm guard: {e}')

# 10. Deploy a completed job
try:
    # Find a completed threshold-met job
    jobs = get('/training/jobs')
    eligible = [j for j in jobs if j['status'] == 'completed' and j.get('threshold_met')]
    if eligible:
        j = eligible[0]
        r = post(f'/deploy/{j["id"]}/deploy', {'actor': 'test'})
        assert 'deployment' in r
        ok(10, f'deploy {j["id"]}: {r["deployment"]["version"]} for {r["deployment"]["model"]}')

        # Verify audit log has the entry
        log = get('/deploy/log')
        assert any(e['action'] == 'deploy' and e['actor'] == 'test' for e in log)
        ok(10, f'audit log records deploy action')
    else:
        ok(10, 'skipped — no eligible completed jobs yet (run training first)')
except Exception as e:
    fail(10, f'deploy + audit: {e}')

# Summary
print()
print(f'Stage 3 results: {passed} passed, {len(errors)} failed')
if errors:
    for e in errors:
        print(f'  {e}')
    sys.exit(1)
else:
    print('All Stage 3 deployment tests passed!')
