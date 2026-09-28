// A small real application exercised over CLI, browser HTTP and MCP stdio.
// Its contract is deliberately independent of the orchestration implementation.
import http from 'node:http';
import readline from 'node:readline';

const transport = process.argv[2];
const greeting = name => `Hello, ${name}!`;

if (transport === 'cli') {
  const name = process.argv[3];
  if (!name?.trim()) {
    process.stderr.write('A nonempty name is required.\n');
    process.exitCode = 2;
  } else {
    process.stdout.write(`${JSON.stringify({ message: greeting(name) })}\n`);
  }
} else if (transport === 'mcp') {
  process.stderr.write('AGENTIC_FIXTURE_MCP_READY\n');
  for await (const line of readline.createInterface({ input: process.stdin })) {
    let request;
    try { request = JSON.parse(line); } catch { continue; }
    if (!Object.hasOwn(request, 'id')) continue;
    let result;
    if (request.method === 'initialize') {
      result = { protocolVersion: request.params.protocolVersion, capabilities: { tools: {} }, serverInfo: { name: 'agentic-test-fixture', version: '1.0.0' } };
    } else if (request.method === 'tools/list') {
      result = { tools: [{ name: 'greet', description: 'Return the greeting for a name.', inputSchema: { type: 'object', properties: { name: { type: 'string' } }, required: ['name'], additionalProperties: false } }] };
    } else if (request.method === 'tools/call' && request.params.name === 'greet') {
      const name = request.params.arguments?.name;
      result = typeof name === 'string' && name.trim()
        ? { content: [{ type: 'text', text: greeting(name) }] }
        : { content: [{ type: 'text', text: 'A nonempty name is required.' }], isError: true };
    } else if (request.method === 'ping') {
      result = {};
    } else {
      process.stdout.write(`${JSON.stringify({ jsonrpc: '2.0', id: request.id, error: { code: -32601, message: 'Method not found' } })}\n`);
      continue;
    }
    process.stdout.write(`${JSON.stringify({ jsonrpc: '2.0', id: request.id, result })}\n`);
  }
} else if (transport === 'http') {
  const page = `<!doctype html><html lang="en"><meta charset="utf-8"><title>Agentic test fixture</title>
<style>body{font:18px system-ui;background:#f2f5fa;color:#142238;max-width:660px;margin:80px auto;padding:24px}main{background:white;border:1px solid #d9e1eb;border-radius:16px;padding:32px}label{display:block}input,button{font:inherit;padding:12px;margin:12px 0;border-radius:8px;border:1px solid #a6b5ca}button{background:#233f70;color:white}#result{min-height:32px;font-weight:600}</style>
<main><h1>Greeting service</h1><p>Enter a name. The greeting survives a page reload.</p>
<form><label for="name">Name</label><input id="name" required autocomplete="off"><button>Greet</button></form><p id="result" role="status"></p></main>
<script>
const result = document.querySelector('#result');
result.textContent = localStorage.getItem('agentic-greeting') || '';
document.querySelector('form').addEventListener('submit', async event => {
  event.preventDefault();
  const response = await fetch('/greet', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:document.querySelector('#name').value}) });
  const data = await response.json();
  result.textContent = data.message || data.error;
  if (response.ok) localStorage.setItem('agentic-greeting', data.message);
});
</script></html>`;
  const server = http.createServer(async (request, response) => {
    if (request.method === 'GET' && request.url === '/') {
      response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      response.end(page);
    } else if (request.method === 'GET' && request.url === '/health') {
      response.writeHead(200, { 'Content-Type': 'application/json' });
      response.end(JSON.stringify({ service: 'agentic-fixture', ready: true }));
    } else if (request.method === 'POST' && request.url === '/greet') {
      try {
        let body = '';
        for await (const chunk of request) {
          body += chunk;
          if (body.length > 4096) throw new Error('Request too large');
        }
        const { name } = JSON.parse(body);
        if (typeof name !== 'string' || !name.trim()) throw new Error('A nonempty name is required.');
        response.writeHead(200, { 'Content-Type': 'application/json' });
        response.end(JSON.stringify({ message: greeting(name) }));
      } catch (error) {
        response.writeHead(400, { 'Content-Type': 'application/json' });
        response.end(JSON.stringify({ error: error.message }));
      }
    } else {
      response.writeHead(404);
      response.end('Not found');
    }
  });
  server.listen(Number(process.argv[3] ?? 0), '127.0.0.1', () => {
    process.stdout.write(`${JSON.stringify({ ready: true, url: `http://127.0.0.1:${server.address().port}` })}\n`);
  });
  process.on('SIGTERM', () => server.close(() => process.exit(0)));
} else {
  process.stderr.write('Use cli, mcp, or http.\n');
  process.exitCode = 2;
}
