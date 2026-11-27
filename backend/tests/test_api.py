"""
OLY VISION MLOps API — Integration Test Suite
==============================================
Runs against a live server at http://localhost:8000

Usage:
    cd backend
    python tests/test_api.py              # run all suites
    python tests/test_api.py --suite core # run one suite (core | auth | deployment)

Suites:
    core        — images, batches, training pipeline (18 tests)
    auth        — authentication & RBAC (12 tests)
    deployment  — model auto-deployment (11 tests)
"""
from __future__ import annotations
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Optional

BASE = 'http://localhost:8000/api'

# ── Helpers ───────────────────────────────────────────────────
_errors: list[str] = []
_passed: int       = 0


def _ok(n: int, msg: str) -> None:
    global _passed
    _passed += 1
    print(f'  PASS [{n:02d}] {msg}')


def _fail(n: int, msg: str) -> None:
    _errors.append(msg)
    print(f'  FAIL [{n:02d}] {msg}')


def _get(path: str, token: Optional[str] = None) -> dict:
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(BASE + path, headers=headers)
    r   = urllib.request.urlopen(req, timeout=8)
    return json.loads(r.read())


def _post(path: str, data: Optional[dict] = None, token: Optional[str] = None) -> dict:
    body    = json.dumps(data or {}).encode()
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method='POST')
    r   = urllib.request.urlopen(req, timeout=8)
    return json.loads(r.read())


def _patch(path: str, data: dict, token: Optional[str] = None) -> dict:
    body    = json.dumps(data).encode()
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method='PATCH')
    r   = urllib.request.urlopen(req, timeout=8)
    return json.loads(r.read())


def _delete(path: str, token: Optional[str] = None) -> int:
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(BASE + path, headers=headers, method='DELETE')
    r   = urllib.request.urlopen(req, timeout=8)
    return r.status


def _expects_error(code: int, fn, *args, **kwargs) -> bool:
    try:
        fn(*args, **kwargs)
        return False
    except urllib.error.HTTPError as e:
        return e.code == code


# ── Suite: Core API ───────────────────────────────────────────
def run_core() -> None:
    print('\n── Core API (Stages 1 & 2) ──────────────────────────────')

    # 1. Health
    try:
        r = urllib.request.urlopen('http://localhost:8000/health', timeout=5)
        d = json.loads(r.read())
        assert d['status'] == 'ok'
        _ok(1, f'Health check: {d}')
    except Exception as e:
        _fail(1, f'Health: {e}')

    # 2. Image stats — route order regression check
    try:
        r = _get('/images/stats/summary')
        assert 'total' in r and 'curated' in r
        _ok(2, f'Image stats: total={r["total"]} curated={r["curated"]} pct={r["pct"]}%')
    except Exception as e:
        _fail(2, f'Image stats: {e}')

    # 3. List images
    try:
        r = _get('/images/')
        assert isinstance(r, list) and len(r) == 24
        _ok(3, f'List images: {len(r)} returned')
    except Exception as e:
        _fail(3, f'List images: {e}')

    # 4. Filter curated
    try:
        r = _get('/images/?curated=true')
        assert all(i['curated'] for i in r)
        _ok(4, f'Filter curated=true: {len(r)} images')
    except Exception as e:
        _fail(4, f'Filter images: {e}')

    # 5. Get single image
    try:
        r = _get('/images/1')
        assert r['id'] == 1 and r['label'] == 'IMG_0001'
        _ok(5, f'Get image 1: {r["label"]} @ {r["location"]}')
    except Exception as e:
        _fail(5, f'Get image: {e}')

    # 6. Annotate image
    try:
        r = _post('/images/10/annotate', {
            'image_id': 10,
            'annotations': {'gender': 'F', 'age': '3', 'staff': 'N', 'id': 'Y'},
        })
        assert r['curated'] is True
        _ok(6, f'Annotate image 10: curated={r["curated"]}')
    except Exception as e:
        _fail(6, f'Annotate: {e}')

    # 7. 404 on unknown image
    try:
        assert _expects_error(404, _get, '/images/9999')
        _ok(7, 'Unknown image returns 404')
    except Exception as e:
        _fail(7, f'Image 404: {e}')

    # 8. List batches
    try:
        r = _get('/batches/')
        assert isinstance(r, list) and len(r) >= 6
        _ok(8, f'List batches: {len(r)} returned')
    except Exception as e:
        _fail(8, f'List batches: {e}')

    # 9. Create batch
    batch_id = None
    try:
        r = _post('/batches/', {'name': 'TEST-001', 'client': 'TestCo', 'images': 50})
        assert r['name'] == 'TEST-001'
        batch_id = r['id']
        _ok(9, f'Create batch: id={batch_id} status={r["status"]}')
    except Exception as e:
        _fail(9, f'Create batch: {e}')

    # 10. Duplicate batch name rejected
    try:
        assert _expects_error(409, _post, '/batches/', {'name': 'TEST-001', 'client': 'X', 'images': 1})
        _ok(10, 'Duplicate batch name returns 409')
    except Exception as e:
        _fail(10, f'Duplicate check: {e}')

    # 11. Update batch
    if batch_id:
        try:
            r = _patch(f'/batches/{batch_id}', {'client': 'UpdatedCo', 'assignee': 'alice@oly.com'})
            assert r['client'] == 'UpdatedCo'
            _ok(11, f'Update batch {batch_id}: client={r["client"]}')
        except Exception as e:
            _fail(11, f'Update batch: {e}')

    # 12. Delete batch
    if batch_id:
        try:
            s = _delete(f'/batches/{batch_id}')
            assert s == 204
            assert _expects_error(404, _get, f'/batches/{batch_id}')
            _ok(12, f'Delete batch {batch_id}: 204, then 404 confirmed')
        except Exception as e:
            _fail(12, f'Delete batch: {e}')

    # 13. Training status
    try:
        r = _get('/training/status')
        assert all(k in r for k in ['gender', 'age', 'staff'])
        _ok(13, f'Training status: {r}')
    except Exception as e:
        _fail(13, f'Training status: {e}')

    # 14. List training jobs
    try:
        r = _get('/training/jobs')
        assert isinstance(r, list)
        _ok(14, f'Training jobs: {len(r)} jobs')
    except Exception as e:
        _fail(14, f'List jobs: {e}')

    # 15. Batch complete → auto-trigger
    try:
        r = _post('/batches/1/complete')
        assert len(r['jobs_started']) == 3
        models = {j['model'] for j in r['jobs_started']}
        assert models == {'gender', 'age', 'staff'}
        _ok(15, f'Batch complete trigger: {[j["id"] for j in r["jobs_started"]]}')
    except Exception as e:
        _fail(15, f'Batch complete: {e}')

    # 16. Job logs
    try:
        jobs = _get('/training/jobs')
        if jobs:
            jid = jobs[0]['id']
            r   = _get(f'/training/jobs/{jid}/logs')
            assert 'logs' in r and 'metrics' in r
            _ok(16, f'Job logs for {jid}: {len(r["logs"])} lines, epoch={r["epoch"]}')
        else:
            _fail(16, 'No jobs found')
    except Exception as e:
        _fail(16, f'Job logs: {e}')

    # 17. batch_id=0 not falsiness crash
    try:
        r = _post('/training/trigger', {'batch_id': 0, 'model_ids': ['gender']})
        assert 'jobs' in r
        _ok(17, f'Trigger with batch_id=0: {r["jobs"][0]["id"]}')
    except Exception as e:
        _fail(17, f'batch_id=0 trigger: {e}')

    # 18. 404 on unknown job
    try:
        assert _expects_error(404, _get, '/training/jobs/JOB-NOTEXIST')
        _ok(18, 'Unknown job returns 404')
    except Exception as e:
        _fail(18, f'Job 404: {e}')


# ── Suite: Authentication & RBAC ──────────────────────────────
def run_auth() -> None:
    print('\n── Authentication & RBAC (Stage 4) ─────────────────────')

    admin_token   = None
    curator_token = None
    viewer_token  = None

    # 1. Admin login
    try:
        r = _post('/auth/login', {'email': 'admin@oly.com', 'password': 'admin123'})
        admin_token = r['access_token']
        assert r['user']['role'] == 'admin'
        _ok(1, f'Admin login: {r["user"]["name"]} ({r["user"]["role"]})')
    except Exception as e:
        _fail(1, f'Admin login: {e}')

    # 2. /me
    try:
        me = _get('/auth/me', admin_token)
        assert me['role'] == 'admin'
        _ok(2, f'/me: {me["name"]}')
    except Exception as e:
        _fail(2, f'/me: {e}')

    # 3. Admin permissions
    try:
        p = _get('/auth/permissions', admin_token)
        assert 'admin' in p['permissions']
        _ok(3, f'Admin permissions: {p["permissions"]}')
    except Exception as e:
        _fail(3, f'Permissions: {e}')

    # 4. Curator login
    try:
        r = _post('/auth/login', {'email': 'alice@oly.com', 'password': 'curator123'})
        curator_token = r['access_token']
        assert r['user']['role'] == 'curator'
        _ok(4, f'Curator login: {r["user"]["name"]}')
    except Exception as e:
        _fail(4, f'Curator login: {e}')

    # 5. Curator permissions — no admin access
    try:
        p = _get('/auth/permissions', curator_token)
        assert 'admin' not in p['permissions'] and 'curation' in p['permissions']
        _ok(5, f'Curator permissions (no admin): {p["permissions"]}')
    except Exception as e:
        _fail(5, f'Curator permissions: {e}')

    # 6. Viewer login
    try:
        r = _post('/auth/login', {'email': 'viewer@oly.com', 'password': 'viewer123'})
        viewer_token = r['access_token']
        assert r['user']['role'] == 'viewer'
        _ok(6, f'Viewer login: {r["user"]["name"]}')
    except Exception as e:
        _fail(6, f'Viewer login: {e}')

    # 7. Wrong password → 401
    try:
        assert _expects_error(401, _post, '/auth/login', {'email': 'admin@oly.com', 'password': 'wrong'})
        _ok(7, 'Wrong password returns 401')
    except Exception as e:
        _fail(7, f'Wrong password: {e}')

    # 8. Unknown email → 401
    try:
        assert _expects_error(401, _post, '/auth/login', {'email': 'nobody@oly.com', 'password': 'x'})
        _ok(8, 'Unknown email returns 401')
    except Exception as e:
        _fail(8, f'Unknown email: {e}')

    # 9. No token → 401
    try:
        assert _expects_error(401, _get, '/auth/me')
        _ok(9, 'No token returns 401')
    except Exception as e:
        _fail(9, f'No token: {e}')

    # 10. List users — admin only
    try:
        users = _get('/auth/users', admin_token)
        assert len(users) >= 4
        _ok(10, f'Admin can list {len(users)} users')
    except Exception as e:
        _fail(10, f'List users: {e}')

    # 11. Curator cannot list users → 403
    try:
        assert _expects_error(403, _get, '/auth/users', curator_token)
        _ok(11, 'Curator cannot list users (403)')
    except Exception as e:
        _fail(11, f'Curator access guard: {e}')

    # 12. Create user — unique email to avoid conflicts
    try:
        email = f'test_{int(time.time())}@oly.com'
        body  = json.dumps({'name': 'Test User', 'email': email, 'password': 'test1234', 'role': 'viewer'}).encode()
        req   = urllib.request.Request(
            BASE + '/auth/users', data=body,
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {admin_token}'},
            method='POST',
        )
        r  = json.loads(urllib.request.urlopen(req, timeout=8).read())
        assert r['email'] == email
        _ok(12, f'Admin created user: {r["name"]} ({r["role"]})')
    except Exception as e:
        _fail(12, f'Create user: {e}')


# ── Suite: Deployment ─────────────────────────────────────────
def run_deployment() -> None:
    print('\n── Model Deployment (Stage 3) ───────────────────────────')

    # 1. List deployments
    try:
        r = _get('/deploy/')
        assert isinstance(r, list) and len(r) >= 3
        _ok(1, f'List deployments: {len(r)} entries')
    except Exception as e:
        _fail(1, f'List deployments: {e}')

    # 2. Active deployments
    try:
        r = _get('/deploy/active')
        assert all(k in r for k in ['gender', 'age', 'staff'])
        active = sum(1 for v in r.values() if v)
        _ok(2, f'Active deployments: {active} active')
    except Exception as e:
        _fail(2, f'Active deployments: {e}')

    # 3. Summary
    try:
        r = _get('/deploy/summary')
        assert 'total_active' in r and r['total_active'] >= 3
        _ok(3, f'Summary: {r["total_active"]} active, avg latency {r["avg_latency_ms"]}ms')
    except Exception as e:
        _fail(3, f'Summary: {e}')

    # 4. Get single deployment
    try:
        r = _get('/deploy/DEP-001')
        assert r['id'] == 'DEP-001'
        _ok(4, f'Get DEP-001: {r["version"]} ({r["status"]})')
    except Exception as e:
        _fail(4, f'Get deployment: {e}')

    # 5. 404 on unknown deployment
    try:
        assert _expects_error(404, _get, '/deploy/DEP-999')
        _ok(5, 'Unknown deployment returns 404')
    except Exception as e:
        _fail(5, f'Deployment 404: {e}')

    # 6. Health refresh
    try:
        r = _post('/deploy/health/refresh')
        assert r['checked'] >= 3
        _ok(6, f'Health refresh: {r["checked"]} deployments checked')
    except Exception as e:
        _fail(6, f'Health refresh: {e}')

    # 7. Audit log
    try:
        r = _get('/deploy/log')
        assert isinstance(r, list)
        _ok(7, f'Audit log: {len(r)} entries')
    except Exception as e:
        _fail(7, f'Audit log: {e}')

    # 8. Rollback — verify endpoint behaves correctly
    try:
        active = _get('/deploy/active')
        dep_with_prev = next(
            (v for v in active.values() if v and v.get('rollback_to')), None
        )
        if dep_with_prev:
            _ok(8, f'Rollback available: {dep_with_prev["model"]} has previous version')
        else:
            assert _expects_error(400, _post, '/deploy/DEP-001/rollback', {'actor': 'test'})
            _ok(8, 'Rollback with no previous version returns 400')
    except Exception as e:
        _fail(8, f'Rollback guard: {e}')

    # 9. Stop requires confirm=true
    try:
        assert _expects_error(400, _post, '/deploy/DEP-002/stop', {'confirm': False, 'actor': 'test'})
        _ok(9, 'Stop without confirm=true returns 400')
    except Exception as e:
        _fail(9, f'Stop confirm guard: {e}')

    # 10. Deploy a completed job
    try:
        jobs     = _get('/training/jobs')
        eligible = [j for j in jobs if j['status'] == 'completed' and j.get('threshold_met')]
        if eligible:
            j = eligible[0]
            r = _post(f'/deploy/{j["id"]}/deploy', {'actor': 'test'})
            assert 'deployment' in r
            _ok(10, f'Deploy {j["id"]}: {r["deployment"]["version"]} for {r["deployment"]["model"]}')
            log = _get('/deploy/log')
            assert any(e['action'] == 'deploy' and e['actor'] == 'test' for e in log)
            _ok(10, 'Audit log records deploy action')
        else:
            _ok(10, 'Skipped — no eligible completed jobs (run training first)')
    except Exception as e:
        _fail(10, f'Deploy + audit: {e}')

    # 11. Inference model status
    try:
        r = _get('/infer/status')
        staff_ok = r.get('staff', {}).get('exists', False)
        id_ok    = r.get('id', {}).get('exists', False)
        _ok(11, f'Inference models: staff={staff_ok} id={id_ok}')
    except Exception as e:
        _fail(11, f'Inference status: {e}')


# ── Main ──────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description='OLY VISION API Integration Tests')
    parser.add_argument('--suite', choices=['core', 'auth', 'deployment', 'all'], default='all')
    args = parser.parse_args()

    global _passed, _errors
    _passed = 0
    _errors = []

    suites = {
        'core':       run_core,
        'auth':       run_auth,
        'deployment': run_deployment,
    }

    if args.suite == 'all':
        for fn in suites.values():
            fn()
    else:
        suites[args.suite]()

    total = _passed + len(_errors)
    print(f'\n{"═"*55}')
    print(f'Results: {_passed}/{total} passed, {len(_errors)} failed')

    if _errors:
        print('\nFailures:')
        for e in _errors:
            print(f'  ✗ {e}')
        sys.exit(1)
    else:
        print('All tests passed! ✓')


if __name__ == '__main__':
    main()
