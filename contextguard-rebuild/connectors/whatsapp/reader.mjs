// Independent read-only text buffer. No WhatsApp send/receipt/presence APIs.
export const validChat=id=>typeof id==='string'&&/^\d+(?:-\d+)?@(?:g\.us|s\.whatsapp\.net|lid)$/.test(id);
export class Reader {
  constructor(){this.selected=new Set();this.messages=new Map();this.chats=new Map();this.overflow=false;this.started=null;this.revision=0;}
  select(ids){
    if(!Array.isArray(ids)||ids.length>20||!ids.every(validChat))throw Error('Select up to 20 valid chats.');
    this.selected=new Set(ids);this.started=new Date().toISOString();
    for(const [id,m] of this.messages)if(!this.selected.has(m.chat))this.messages.delete(id);
    // Clearing selection is also an explicit way to clear a full buffer.
    if(!ids.length){this.messages.clear();this.overflow=false;}
    return this.status();
  }
  metadata(rows){for(const row of rows||[]){const id=row.id;if(validChat(id))this.chats.set(id,{id,name:String(row.subject||row.name||id).slice(0,150)});if(this.chats.size>=500)break;}}
  receive(row){
    const key=row.key||{},chat=key.remoteJid;
    if(!this.selected.has(chat)||!key.id)return;
    let body=row.message||{};
    body=body.ephemeralMessage?.message||body;
    const text=body.conversation||body.extendedTextMessage?.text;
    // Media, view-once messages, reactions and protocol messages are never extracted.
    if(typeof text!=='string'||!text.trim())return;
    const id=chat+':'+key.id;
    const time=Number(row.messageTimestamp);
    const message={id,chat,message_id:key.id,text,author:row.pushName||null,
      external_identity:key.fromMe?(this.accountId||null):(key.participant||chat),from_me:!!key.fromMe,
      timestamp:Number.isFinite(time)&&time>0?new Date(time*1000).toISOString():null,revision:++this.revision};
    this.messages.set(id,message);
    if(this.messages.size>300||[...this.messages.values()].reduce((n,m)=>n+m.text.length,0)>60000){this.messages.delete(id);this.overflow=true;}
  }
  update(rows){for(const {key,update} of rows||[]){const old=this.messages.get(key.remoteJid+':'+key.id);if(!old||!this.selected.has(key.remoteJid))continue;
    if(update?.message===null){this.messages.delete(old.id);continue;}
    if(update?.message)this.receive({key,message:update.message,pushName:old.author,messageTimestamp:old.timestamp?Date.parse(old.timestamp)/1000:undefined});
  }}
  remove(event){if(event.all){for(const [id,m] of this.messages)if(m.chat===event.jid)this.messages.delete(id);}else for(const k of event.keys||[])this.messages.delete(k.remoteJid+':'+k.id);}
  snapshot(){if(this.overflow)throw Error('Selected text exceeded the local buffer limit. Clear selection and collect a smaller batch, or import a chat export.');return [...this.messages.values()].map(m=>({...m}));}
  ack(items){for(const item of items||[]){const row=this.messages.get(item.id);if(row?.revision===item.revision)this.messages.delete(item.id);}}
  status(){return {selected:[...this.selected],chats:[...this.chats.values()],message_count:this.messages.size,overflow:this.overflow,collecting_since:this.started};}
  clear(){this.messages.clear();this.selected.clear();this.chats.clear();this.overflow=false;this.started=null;}
}
