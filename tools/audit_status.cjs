/* Only a recognized policy rejection of the first file navigation is blocked. */
class InitialFileNavigationBlocked extends Error {}
async function initialFileNavigation(page, url) {
  try { await page.goto(url); }
  catch (error) {
    if (String(error.message).includes('net::ERR_BLOCKED_BY_ADMINISTRATOR')) {
      throw new InitialFileNavigationBlocked(error.message);
    }
    throw error;
  }
}
async function auditTask(name, run) {
  try { await run(); return {name, status: 'PASS'}; }
  catch (error) {
    return {name, status: error instanceof InitialFileNavigationBlocked ? 'BLOCKED' : 'FAIL', error: error.message};
  }
}
function auditExitCode(pageFailures, tasks) {
  return pageFailures || tasks.some(t => t.status === 'FAIL') ? 1 : tasks.some(t => t.status === 'BLOCKED') ? 2 : 0;
}
module.exports = {initialFileNavigation, auditTask, auditExitCode};
