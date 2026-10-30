const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const header = fs.readFileSync(path.join(__dirname, '../esp32_fan_manual/fan_page.hpp'), 'utf8');
const source = header.match(/<script>([\s\S]*?)<\/script>/)[1];
const flush = () => new Promise(resolve => setImmediate(resolve));

function createApp(ready = true, deferArm = false) {
  const elements = new Map();
  for (const name of ['fanStart', 'fanStop', 'fanMessage', 'fanDetail', 'stopAll']) {
    elements.set(name, {disabled: true, textContent: ''});
  }
  const app = {elements, calls: [], timers: [], events: {}, releaseArm: null};
  const board = {ready, armed: false, running: false, session: 0, reason: 'disarmed'};
  app.board = board;
  const context = vm.createContext({
    AbortSignal,
    document: {
      hidden: false,
      getElementById: name => elements.get(name),
      addEventListener: (name, handler) => {app.events[name] = handler;},
    },
    window: {addEventListener: (name, handler) => {app.events[name] = handler;}},
    setTimeout: (callback, delay) => {
      const timer = {callback, delay, cancelled: false};
      app.timers.push(timer);
      return timer;
    },
    clearTimeout: timer => {if (timer) timer.cancelled = true;},
    fetch: async (route, options = {}) => {
      const body = options.body ? JSON.parse(options.body) : {};
      app.calls.push({route, body});
      if (route.endsWith('/arm')) {
        board.session++;
        board.armed = true;
      } else if (route.endsWith('/run')) {
        board.running = board.armed && body.session === board.session;
      } else if (route.endsWith('/stop') && route.startsWith('/api/fan/')) {
        board.armed = board.running = false;
      }
      const snapshot = {...board};
      const response = {ok: true, json: async () => snapshot};
      if (deferArm && route.endsWith('/arm')) {
        return new Promise(resolve => {app.releaseArm = () => resolve(response);});
      }
      return response;
    },
  });
  vm.runInContext(source, context);
  app.count = suffix => app.calls.filter(call => call.route === suffix).length;
  app.timer = delay => app.timers.findLast(timer => timer.delay === delay && !timer.cancelled);
  return app;
}

async function main() {
  const app = createApp();
  await flush();
  assert.equal(app.elements.get('fanStart').disabled, false);
  assert.equal(app.count('/api/fan/run'), 0);
  await app.elements.get('fanStart').onclick();
  assert.equal(app.board.running, true);
  assert.equal(app.elements.get('fanStart').disabled, true);
  assert.deepEqual(app.calls.at(-1), {route: '/api/fan/run', body: {session: 1, sequence: 1}});
  app.timer(200).callback();
  await flush();
  assert.equal(app.calls.at(-1).body.sequence, 2);
  const oldHeartbeat = app.timer(200);
  app.elements.get('fanStop').onclick();
  await flush();
  assert.equal(app.board.running, false);
  assert.equal(app.count('/api/stop'), 0);
  const runCount = app.count('/api/fan/run');
  oldHeartbeat.callback();
  await flush();
  assert.equal(app.count('/api/fan/run'), runCount);
  await app.elements.get('fanStart').onclick();
  app.elements.get('stopAll').onclick();
  await flush();
  assert.equal(app.board.running, false);
  assert.equal(app.count('/api/stop'), 1);
  await app.elements.get('fanStart').onclick();
  app.events.blur();
  await flush();
  assert.equal(app.board.running, false);
  await app.elements.get('fanStart').onclick();
  app.board.armed = app.board.running = false;
  app.board.reason = 'run_timeout';
  const expiredHeartbeat = app.timer(200);
  app.timer(700).callback();
  await flush();
  assert.equal(app.elements.get('fanStart').disabled, false);
  const expiredCount = app.count('/api/fan/run');
  expiredHeartbeat.callback();
  await flush();
  assert.equal(app.count('/api/fan/run'), expiredCount);
  const disabled = createApp(false);
  await flush();
  assert.equal(disabled.elements.get('fanStart').disabled, true);
  assert.equal(disabled.count('/api/fan/run'), 0);
  const delayed = createApp(true, true);
  await flush();
  const pendingStart = delayed.elements.get('fanStart').onclick();
  await flush();
  delayed.elements.get('fanStop').onclick();
  await flush();
  delayed.releaseArm();
  await pendingStart;
  await flush();
  assert.equal(delayed.count('/api/fan/run'), 0);
  assert.equal(delayed.board.running, false);
  console.log('Fan page checks passed: no autostart, heartbeat, independent/all stop, stale replies, timeout and disabled configuration.');
}

main().catch(error => {console.error(error); process.exitCode = 1;});
