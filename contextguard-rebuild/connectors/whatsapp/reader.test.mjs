import test from 'node:test';
import assert from 'node:assert/strict';
import {Reader,validChat} from './reader.mjs';
import {seal,unseal} from './vault.mjs';
import {randomBytes} from 'node:crypto';
const chat='123@g.us',other='456@g.us';
const event=(id,text,remoteJid=chat)=>({key:{id,remoteJid,participant:'7@s.whatsapp.net'},message:{conversation:text},messageTimestamp:1800000000,pushName:'Fictional author'});
test('session encryption authenticates data and fails closed for tampering/wrong keys',()=>{
 const key=randomBytes(32),text='fictional session credential';const encrypted=seal(text,key);
 assert.equal(encrypted.includes(Buffer.from(text)),false);assert.equal(unseal(encrypted,key),text);
 assert.throws(()=>unseal(encrypted,randomBytes(32)));encrypted[encrypted.length-1]^=1;assert.throws(()=>unseal(encrypted,key));
});
test('retains only explicitly selected plain text with original identifiers',()=>{
 const r=new Reader();r.receive(event('1','unselected'));assert.equal(r.snapshot().length,0);
 r.select([chat]);r.receive(event('1','Selected text'));r.receive(event('2','Secret unselected',other));
 r.receive({key:{id:'media',remoteJid:chat},message:{imageMessage:{caption:'Private caption'}}});
 assert.equal(r.snapshot().length,1);assert.equal(r.snapshot()[0].external_identity,'7@s.whatsapp.net');
 assert.equal(r.snapshot()[0].message_id,'1');assert.equal(r.snapshot()[0].timestamp,'2027-01-15T08:00:00.000Z');
});
test('duplicate deliveries, edits/deletions and ack preserve newer revisions',()=>{
 const r=new Reader();r.select([chat]);r.receive(event('1','Old text'));r.receive(event('1','Old text'));assert.equal(r.snapshot().length,1);
 const snapshot=r.snapshot();r.update([{key:{id:'1',remoteJid:chat},update:{message:{conversation:'Edited text'}}}]);
 r.ack(snapshot);assert.equal(r.snapshot()[0].text,'Edited text');
 r.remove({keys:[{id:'1',remoteJid:chat}]});assert.equal(r.snapshot().length,0);
 r.receive(event('2','Delete all'));r.remove({all:true,jid:chat});assert.equal(r.snapshot().length,0);
});
test('deselecting removes text; bounds fail explicitly and empty selection resets',()=>{
 const r=new Reader();r.select([chat]);r.receive(event('1','text'));r.select([other]);assert.equal(r.snapshot().length,0);
 assert.throws(()=>r.select(['status@broadcast']));assert.equal(validChat('123@s.whatsapp.net'),true);
 r.select([chat]);r.receive(event('huge','x'.repeat(60001)));assert.throws(()=>r.snapshot(),/exceeded/);
 r.select([]);assert.deepEqual(r.snapshot(),[]);assert.equal(r.status().overflow,false);
});
