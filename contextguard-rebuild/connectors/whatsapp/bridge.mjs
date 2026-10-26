// Private stdio RPC; only the parent local API can reach this process.
import readline from 'node:readline';
import {readFile,writeFile,rename,rm} from 'node:fs/promises';
import {Reader} from './reader.mjs';
import {seal,unseal} from './vault.mjs';
const reader=new Reader();
let runtime,qrEncoder,socket,auth,key,file,qr=null,status='disconnected',generation=0,retries=0,retryTimer;
const silent={level:'silent',trace(){},debug(){},info(){},warn(){},error(){},fatal(){},child(){return this;}};
function send(value){process.stdout.write(JSON.stringify(value)+'\n');}
let writing=Promise.resolve();
function save(){
  writing=writing.then(async()=>{
    await writeFile(file+'.tmp',seal(JSON.stringify(auth,runtime.BufferJSON.replacer),key),{mode:0o600});await rename(file+'.tmp',file);
  });
  writing.catch(()=>{status='storage_error';qr=null;generation++;socket?.end(undefined);});
  return writing;
}
async function start(){
  clearTimeout(retryTimer);const current=++generation;qr=null;status='connecting';
  socket=runtime.default({auth:{creds:auth.creds,keys:{
    async get(type,ids){const data={};for(const id of ids){let item=auth.keys[type]?.[id];if(type==='app-state-sync-key'&&item)item=runtime.proto.Message.AppStateSyncKeyData.fromObject(item);data[id]=item;}return data;},
    async set(data){for(const [type,items]of Object.entries(data)){auth.keys[type]||={};for(const [id,value]of Object.entries(items)){if(value===null)delete auth.keys[type][id];else auth.keys[type][id]=value;}}await save();}
  }},logger:silent,syncFullHistory:false,shouldSyncHistoryMessage:()=>false,markOnlineOnConnect:false,
    shouldIgnoreJid:jid=>!reader.selected.has(jid),getMessage:async()=>undefined});
  socket.ev.on('creds.update',updates=>{if(current===generation){Object.assign(auth.creds,updates);save().catch(()=>{});}});
  socket.ev.on('connection.update',update=>{
    if(current!==generation)return;
    if(update.qr){qr=update.qr;status='awaiting_scan';}
    if(update.connection==='open'){qr=null;status='connected';retries=0;reader.accountId=socket.user?.id||null;}
    if(update.connection==='close'){
      qr=null;const code=update.lastDisconnect?.error?.output?.statusCode;
      if([401,403,411,440,500].includes(code)){reader.clear();status=code===401?'logged_out':'connection_rejected';return;}
      if(retries++<3){status='reconnecting';retryTimer=setTimeout(()=>start().catch(()=>{status='connection_failed';}),code===515?300:2000*retries);}
      else status='connection_failed';
    }
  });
  socket.ev.on('messages.upsert',({messages})=>{if(current===generation)for(const m of messages)reader.receive(m);});
  socket.ev.on('messages.update',rows=>{if(current===generation)reader.update(rows);});
  socket.ev.on('messages.delete',event=>{if(current===generation)reader.remove(event);});
  for(const event of ['chats.upsert','chats.update','groups.upsert','groups.update'])socket.ev.on(event,rows=>{if(current===generation)reader.metadata(rows);});
}
async function action(method,p){
  if(method==='initialize'){
    key=Buffer.from(p.key,'base64');file=p.file;
    try{runtime=await import('baileys');qrEncoder=(await import('qrcode')).default;}catch{throw Error('WhatsApp runtime missing. Run setup-whatsapp.bat.');}
    try{auth=JSON.parse(unseal(await readFile(file),key),runtime.BufferJSON.reviver);}
    catch(e){if(e.code!=='ENOENT')throw Error('Stored session could not be decrypted. Disconnect and pair again.');auth={creds:runtime.initAuthCreds(),keys:{}};}
    return {status:'ready'};
  }
  if(!runtime)throw Error('Initialize the WhatsApp runtime first.');
  if(method==='connect'){if(!['connected','connecting','awaiting_scan','reconnecting'].includes(status)){retries=0;await start();}return {status};}
  if(method==='status')return {status,...reader.status(),account_id:status==='connected'?socket.user?.id:null,qr_available:!!qr};
  if(method==='qr'){if(!qr)throw Error('No pairing QR available. Refresh connection status.');return {png:(await qrEncoder.toBuffer(qr,{type:'png',width:320,margin:2})).toString('base64')};}
  if(method==='chats'){if(status!=='connected')throw Error('Pair WhatsApp first.');reader.metadata(Object.values(await socket.groupFetchAllParticipating()));return reader.status();}
  if(method==='select'){if(status!=='connected')throw Error('Pair WhatsApp first.');return reader.select(p.ids);}
  if(method==='messages'){if(status!=='connected')throw Error('Pair WhatsApp first.');return {messages:reader.snapshot()};}
  if(method==='ack'){reader.ack(p.items);return {ok:true};}
  if(method==='disconnect'){
    generation++;clearTimeout(retryTimer);qr=null;status='disconnected';reader.clear();
    try{if(socket)await Promise.race([socket.logout(),new Promise(resolve=>setTimeout(resolve,2000))]);}catch{}
    socket?.end(undefined);socket=null;await writing.catch(()=>{});await rm(file,{force:true});await rm(file+'.tmp',{force:true});auth={creds:runtime.initAuthCreds(),keys:{}};writing=Promise.resolve();return {status};
  }
  throw Error('Unknown read-only operation.');
}
let queue=Promise.resolve();
readline.createInterface({input:process.stdin}).on('line',line=>{queue=queue.then(async()=>{
  let request;try{request=JSON.parse(line);const result=await action(request.method,request.payload||{});send({id:request.id,result});}
  catch(error){send({id:request?.id,error:['Select up to 20 valid chats.','Pair WhatsApp first.','WhatsApp runtime missing. Run setup-whatsapp.bat.','Stored session could not be decrypted. Disconnect and pair again.','No pairing QR available. Refresh connection status.'].includes(error.message)||error.message.startsWith('Selected text exceeded')?error.message:'WhatsApp operation failed. Refresh status or pair again; manual import remains available.'});}
});}).on('close',()=>{generation++;clearTimeout(retryTimer);socket?.end(undefined);writing.finally(()=>process.exit(0));});
process.on('uncaughtException',()=>{status='connection_failed';qr=null;generation++;socket?.end(undefined);});
process.on('unhandledRejection',()=>{status='connection_failed';qr=null;generation++;socket?.end(undefined);});
