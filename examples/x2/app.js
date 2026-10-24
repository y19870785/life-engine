'use strict';
const token = location.hash.slice(1);
history.replaceState(null, '', '/');
let csrf = '', state = null, busy = false;
const pending = new Map();
const $ = id => document.getElementById(id);
const message = text => { $('message').textContent = text; };
const requestId = () => crypto.randomUUID().replaceAll('-', '');
async function call(path, body) {
  const headers = {Authorization: `Bearer ${token}`};
  const options = {method: body === undefined ? 'GET' : 'POST', headers};
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'; headers['X-X2-CSRF'] = csrf;
    options.body = JSON.stringify(body);
  }
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok) throw new Error(`${result.code} · 阶段 ${result.stage}`);
  return result;
}
function render(value) {
  state = value;
  $('identity').textContent = `${value.version} · fixture ${value.fixture} · 阶段 ${value.phase} · ${value.sessions}/7 故事`;
  $('reopen').textContent = `py -3.12 -I -S -B -X utf8 tools/experience_x2.py start --fixture ${value.fixture} --offline`;
  $('turns').replaceChildren();
  for (const turn of value.turns) {
    const p = document.createElement('p'); p.textContent = `你：${turn.user}\n回放：${turn.model}`; $('turns').append(p);
  }
  $('candidate').textContent = value.candidate ? JSON.stringify(value.candidate, null, 2) : '尚无候选';
  $('recalls').replaceChildren();
  for (const recall of value.recalls) {
    const pre = document.createElement('pre'); pre.textContent = JSON.stringify(recall, null, 2); $('recalls').append(pre);
  }
  $('turn').disabled = value.phase !== 'roleplay';
  $('finish').disabled = !['roleplay', 'interrupted'].includes(value.phase) || !value.turns.length;
  $('accept').disabled = value.phase !== 'candidate';
  $('end').disabled = !['candidate', 'accepted'].includes(value.phase);
  $('new').disabled = !['empty', 'ended'].includes(value.phase);
  message(`${value.diagnostic} · 反馈 ${value.feedback_count} 条。未接受候选不可召回；没有命中也可能是词面不匹配。`);
}
async function action(name, data = {}, idempotent = false) {
  if (busy) return;
  busy = true;
  try {
    let body = data;
    if (idempotent) {
      if (!pending.has(name)) pending.set(name, {...data, request: requestId()});
      body = pending.get(name);
    }
    render(await call(`/api/${name}`, body));
    pending.delete(name);
  } catch (error) { message(`${error.message}。操作结果不确定时请保留 fixture，停止并重开；不要更换身份重试。`); }
  finally { busy = false; }
}
$('new').addEventListener('click', () => action('new'));
$('turn').addEventListener('click', () => action('turn', {text: $('input').value}, true));
$('finish').addEventListener('click', () => action('finish', {}, true));
$('accept').addEventListener('click', () => action('accept', {revision: state.revision}, true));
$('end').addEventListener('click', () => action('end'));
$('search').addEventListener('click', async () => { try { render(await call('/api/query', {query: $('query').value})); } catch(e) { message(e.message); } });
$('feedback').addEventListener('click', () => action('feedback', {rating: $('rating').value, reason: $('reason').value}));
$('export').addEventListener('click', async () => { try { $('exported').textContent = JSON.stringify(await call('/api/export'), null, 2); } catch(e) { message(e.message); } });
$('stop').addEventListener('click', async () => { try { await call('/api/stop', {}); message('服务已停止。数据保留；请在终端重开同一 fixture，使用新地址。'); } catch(e) { message(e.message); } });
call('/api/bootstrap').then(result => { csrf = result.csrf; render(result.state); }).catch(e => message(`${e.message}。请从终端复制含 # 口令的完整地址；刷新后需要重新粘贴该地址。`));
