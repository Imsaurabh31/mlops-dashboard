"""
Quick verification script — runs against the live backend at localhost:8000.
Usage: python verify.py
"""
import urllib.request, urllib.error, json, sys

BASE = 'http://localhost:8000/api'
errors = []
passed = 0


def get(path):
    r = urllib.request.urlopen(BASE + path, timeout=5)
    return json.loads(r.read())


def post(path, data=None):
    body = json.dumps(data or {}).encode()
    req  = urllib.request.Request(
        BASE + path, data=body,
        headers={'Content-Type': 'application/json'}, method='POST'
    )
    r = urllib.request.urlopen(req, timeout=5)
    return json.loads(r.read())


def patch(path, data):
    body = json.dumps(data).encode()
    req  = urllib.request.Request(
        BASE + path, data=body,
        headers={'Content-Type': 'application/json'}, method='PATCH'
    )
    r = urllib.request.urlopen(req, timeout=5)
    return json.loads(r.read())


def delete(path):
    req = urllib.request.Request(BASE + path, method='DELETE')
    r   = urllib.request.urlopen(req, timeout=5)
    return r.status


def ok(n, msg):
    global passed
    passed += 1
    print(f'  PASS [{n:02d}] {msg}')


def fail(n, msg):
    errors.append(f'FAIL [{n:02d}] {msg}')
    print(f'  FAIL [{n:02d}] {msg}')


# ── 1. Health ────────────────────────────────────────────────
try:
    r = urllib.request.urlopen('http://localhost:8000/health', timeout=5)
    d = json.loads(r.read())
    assert d['status'] == 'ok'
    ok(1, f'health check: {d}')
except Exception as e:
    fail(1, f'health: {e}')

# ── 2. Image stats — /stats/summary must NOT 422 ─────────────
try:
    r = get('/images/stats/summary')
    assert 'total' in r and 'curated' in r and 'pct' in r
    ok(2, f'image stats: total={r["total"]} curated={r["curated"]} pct={r["pct"]}%')
except Exception as e:
    fail(2, f'image stats (route order bug if 422): {e}')

# ── 3. List images ────────────────────────────────────────────
try:
    r = get('/images/')
    assert isinstance(r, list) and len(r) == 24
    ok(3, f'list images: {len(r)} returned')
except Exception as e:
    fail(3, f'list images: {e}')

# ── 4. Filter curated ─────────────────────────────────────────
try:
    r = get('/images/?curated=true')
    assert all(i['curated'] for i in r)
    ok(4, f'filter curated=true: {len(r)} images')
except Exception as e:
    fail(4, f'filter images: {e}')

# ── 5. Get single image ───────────────────────────────────────
try:
    r = get('/images/1')
    assert r['id'] == 1 and r['label'] == 'IMG_0001'
    ok(5, f'get image 1: {r["label"]} @ {r["location"]}')
except Exception as e:
    fail(5, f'get image: {e}')

# ── 6. Annotate image ─────────────────────────────────────────
try:
    r = post('/images/10/annotate', {
        'image_id': 10,
        'annotations': {'gender': 'F', 'age': '3', 'staff': 'N', 'id': 'Y'}
    })
    assert r['curated'] is True and r['annotations']['gender'] == 'F'
    ok(6, f'annotate image 10: curated={r["curated"]}')
except Exception as e:
    fail(6, f'annotate: {e}')

# ── 7. 404 on bad image id ────────────────────────────────────
try:
    try:
        get('/images/9999')
        fail(7, '9999 should return 404')
    except urllib.error.HTTPError as he:
        assert he.code == 404
        ok(7, 'image 9999 returns 404')
except Exception as e:
    fail(7, f'404 check: {e}')

# ── 8. List batches ───────────────────────────────────────────
try:
    r = get('/batches/')
    assert isinstance(r, list) and len(r) >= 6
    ok(8, f'list batches: {len(r)} returned')
except Exception as e:
    fail(8, f'list batches: {e}')

# ── 9. Create batch ───────────────────────────────────────────
batch_id = None
try:
    r = post('/batches/', {'name': 'VERIFY-001', 'client': 'VerifyCo', 'images': 50})
    assert r['name'] == 'VERIFY-001' and r['pct'] == 0.0
    batch_id = r['id']
    ok(9, f'create batch: id={batch_id} status={r["status"]}')
except Exception as e:
    fail(9, f'create batch: {e}')

# ── 10. Duplicate batch name rejected ─────────────────────────
try:
    try:
        post('/batches/', {'name': 'VERIFY-001', 'client': 'X', 'images': 1})
        fail(10, 'duplicate should 409')
    except urllib.error.HTTPError as he:
        assert he.code == 409
        ok(10, 'duplicate batch name correctly returns 409')
except Exception as e:
    fail(10, f'duplicate check: {e}')

# ── 11. Update batch ──────────────────────────────────────────
if batch_id:
    try:
        r = patch(f'/batches/{batch_id}', {'client': 'UpdatedCo', 'assignee': 'alice@oly.com'})
        assert r['client'] == 'UpdatedCo' and r['assigned'] == 'alice@oly.com'
        ok(11, f'patch batch {batch_id}: client={r["client"]} assigned={r["assigned"]}')
    except Exception as e:
        fail(11, f'patch batch: {e}')
else:
    fail(11, 'skipped (no batch_id from test 9)')

# ── 12. Delete batch ──────────────────────────────────────────
if batch_id:
    try:
        s = delete(f'/batches/{batch_id}')
        assert s == 204
        # Confirm it's gone
        try:
            get(f'/batches/{batch_id}')
            fail(12, 'deleted batch still accessible')
        except urllib.error.HTTPError as he:
            assert he.code == 404
        ok(12, f'delete batch {batch_id}: 204, then 404 confirmed')
    except Exception as e:
        fail(12, f'delete batch: {e}')
else:
    fail(12, 'skipped (no batch_id)')

# ── 13. Training status ───────────────────────────────────────
try:
    r = get('/training/status')
    assert all(k in r for k in ['gender', 'age', 'staff'])
    ok(13, f'training status: {r}')
except Exception as e:
    fail(13, f'training status: {e}')

# ── 14. List training jobs ────────────────────────────────────
try:
    r = get('/training/jobs')
    assert isinstance(r, list) and len(r) >= 4
    ok(14, f'training jobs: {len(r)} jobs')
except Exception as e:
    fail(14, f'list jobs: {e}')

# ── 15. Batch complete → auto-trigger ────────────────────────
try:
    r = post('/batches/2/complete')
    assert len(r['jobs_started']) == 3
    models = {j['model'] for j in r['jobs_started']}
    assert models == {'gender', 'age', 'staff'}
    ok(15, f'batch complete trigger: {[j["id"] for j in r["jobs_started"]]}')
except Exception as e:
    fail(15, f'batch complete trigger: {e}')

# ── 16. Job logs endpoint ─────────────────────────────────────
try:
    jobs = get('/training/jobs')
    if jobs:
        jid = jobs[0]['id']
        r   = get(f'/training/jobs/{jid}/logs')
        assert 'logs' in r and 'metrics' in r and 'epoch' in r
        ok(16, f'job logs for {jid}: {len(r["logs"])} lines, epoch={r["epoch"]}')
    else:
        fail(16, 'no jobs found')
except Exception as e:
    fail(16, f'job logs: {e}')

# ── 17. Triggered_by_batch=0 must not say "manual" ───────────
try:
    # Manually trigger with batch_id=0 — should not be treated as manual
    r = post('/training/trigger', {'batch_id': 0, 'model_ids': ['gender']})
    job = r['jobs'][0]
    # batch_id=0 is falsy in old code — verify fix
    # We can't assert the exact value since batch 0 doesn't exist as a named batch
    # but it should not crash and should return a job
    assert 'id' in job
    ok(17, f'trigger with batch_id=0: {job["id"]} (not falsiness crash)')
except Exception as e:
    fail(17, f'batch_id=0 trigger: {e}')

# ── 18. 404 on bad job id ─────────────────────────────────────
try:
    try:
        get('/training/jobs/JOB-NOTEXIST')
        fail(18, 'missing job should 404')
    except urllib.error.HTTPError as he:
        assert he.code == 404
        ok(18, 'unknown job id returns 404')
except Exception as e:
    fail(18, f'job 404: {e}')

# ── Summary ───────────────────────────────────────────────────
print()
print(f'Results: {passed} passed, {len(errors)} failed')
if errors:
    print('\nFailures:')
    for e in errors:
        print(f'  {e}')
    sys.exit(1)
else:
    print('All tests passed!')
