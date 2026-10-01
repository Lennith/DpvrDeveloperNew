const {test} = require('node:test');
const assert = require('node:assert/strict');
const {initialFileNavigation, auditTask, auditExitCode} = require('./audit_status.cjs');
const policy = 'page.goto: net::ERR_BLOCKED_BY_ADMINISTRATOR';
for (const [name, navigationError, laterError, expected] of [
  ['first navigation policy rejection', policy, null, 'BLOCKED'],
  ['first navigation missing file', 'net::ERR_FILE_NOT_FOUND', null, 'FAIL'],
  ['first navigation timeout', 'page.goto: Timeout 10000ms exceeded', null, 'FAIL'],
  ['CSS assertion', null, 'Offline CSS and search data', 'FAIL'],
  ['search timeout', null, 'locator.click: Timeout 10000ms exceeded', 'FAIL'],
  ['broken image assertion', null, 'Offline article image', 'FAIL'],
  ['later navigation policy rejection', null, policy, 'FAIL'],
  ['ordinary error with old marker', null, 'BLOCKED_BY_ENVIRONMENT: failure', 'FAIL'],
  ['complete workflow', null, null, 'PASS'],
]) test(name, async () => {
  let reachedAssertions = false;
  const result = await auditTask(name, async () => {
    await initialFileNavigation({goto: async () => {if (navigationError) throw Error(navigationError);}}, 'file:///index.html');
    reachedAssertions = true;
    if (laterError) throw Error(laterError);
  });
  assert.equal(result.status, expected);
  assert.equal(reachedAssertions, !navigationError);
  assert.equal(auditExitCode(0, [result]), {PASS: 0, FAIL: 1, BLOCKED: 2}[expected]);
});
test('failure takes precedence over blocked', () => {
  assert.equal(auditExitCode(0, [{status:'BLOCKED'}, {status:'FAIL'}]), 1);
  assert.equal(auditExitCode(1, [{status:'BLOCKED'}]), 1);
});
