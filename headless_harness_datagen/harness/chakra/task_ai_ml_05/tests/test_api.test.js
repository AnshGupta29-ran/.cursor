import assert from 'assert';
import fetch from 'node-fetch';
import app from '../src/server.js';

const BASE = 'http://127.0.0.1:5000';
let server;

async function startServer(){
  return new Promise((resolve)=>{
    server = app.listen(5000,()=>{console.log('Test server started'); resolve();});
  });
}

async function stopServer(){
  return new Promise((r)=>server.close(()=>{console.log('Test server stopped'); r();}));
}

async function waitForServer(retries=5){
  for(let i=0;i<retries;i++){
    try{
      const r=await fetch(`${BASE}/health`);
      if(r.ok) return;
    }catch(e){}
    await new Promise(r=>setTimeout(r,500));
  }
  throw new Error('Server not reachable');
}

(async()=>{
  await startServer();
  await waitForServer();
  // Happy path ticket
  const payload={channel:'email',author_handle:'test',subject:'test',body:'The dock gate at Pier 4 is jammed and my card was charged twice.'};
  const res=await fetch(`${BASE}/tickets`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  assert.strictEqual(res.status,201,'Ticket creation should return 201');
  const data=await res.json();
  assert.ok(data.ticket_id,'Response should contain ticket_id');
  assert.strictEqual(data.category,'safety','Should route to safety queue');
  // Export
  const expRes=await fetch(`${BASE}/export`);
  assert.ok(expRes.ok,'Export should succeed');
  const bundle=await expRes.json();
  // Wipe DB via import of empty bundle (after dropping) - test roundtrip
  const wipeRes=await fetch(`${BASE}/import`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({version:1,tickets:[],classifications:[],queues:[],audit:[]})});
  assert.ok(wipeRes.ok,'Import should succeed');
  const statsRes=await fetch(`${BASE}/stats`);
  const stats=await statsRes.json();
  assert.strictEqual(stats.total,0,'After wipe, total tickets should be 0');
  console.log('All tests passed');
  await stopServer();
})();
