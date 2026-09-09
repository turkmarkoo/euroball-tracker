import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {dateValid,deduplicate,filterTransfers,counts,safeURL} from './data-core.mjs';
const record={id:'a',player:'Ivan Karačić',to:'Krka',from:'?',pos:'Coach',league:'ABA League',date:'2026-09-06',status:'signed'};
import {clubName,norm} from './data-core.mjs';
import {clubGroups,clubSearchNames,isClub} from './club-identities.mjs';
test('all reviewed club aliases resolve consistently and idempotently',()=>{
 for(const group of clubGroups)for(const name of group){assert.equal(clubName(name),group[0]);assert.equal(clubName(clubName(name)),group[0])}
 assert.equal(clubName(' BEŞİKTAŞ '),'Beşiktaş');assert.equal(clubName('Aris Betsson'),'Aris Thessaloniki');
});
test('sponsor searches and old team URLs find the complete combined archive',()=>{
 const rows=deduplicate(['Aris','Aris Betsson','Aris Thessaloniki'].map((to,i)=>({...record,id:String(i),player:'Player '+i,to})));
 for(const name of ['Aris','Aris Betsson','Aris Thessaloniki'])assert.equal(filterTransfers(rows,{team:name}).length,3);
 assert.equal(filterTransfers(rows,{q:'Aris Betsson'}).length,3);
 assert.ok(norm(clubSearchNames('Beşiktaş')).includes('besiktas'));
});
test('similar names, youth teams, and unrelated cities remain separate',()=>{
 for(const [a,b] of [['AEK','AEK Larnaca'],['Aris','Aris Leeuwarden'],['Apollo Amsterdam','Apollon Patras'],['Krka','Krka youth'],['Ilirija','Lliria'],['Spartak Subotica','Spartak Pleven'],['London Lions','Landau Lions'],['Charlotte Hornets','Charlotte Hornets (G League)']])assert.notEqual(clubName(a),clubName(b));
 assert.equal(isClub('NBA (Draft)'),false);assert.equal(isClub('Italian Serie A2'),false);assert.equal(isClub('Krka youth'),true);
});
test('duplicate aliases merge only the same dated event and preserve source IDs',()=>{
 const rows=deduplicate([{...record,to:'Aris',id:'aris-a'},{...record,to:'Aris Betsson',id:'aris-b'},{...record,to:'Aris Thessaloniki',id:'aris-c',date:'2026-09-05'}]);
 assert.equal(rows.length,2);assert.deepEqual(rows[0].alias_ids,['aris-b']);
});
test('Aris and Besiktas aliases share the same sourced crest',()=>{
 const media=JSON.parse(fs.readFileSync(new URL('./media.json',import.meta.url)));
 for(const group of [['Aris','Aris Betsson','Aris Thessaloniki'],['Besiktas','Beşiktaş']]){
  const urls=group.map(name=>media.clubs[norm(clubName(name))]?.url);assert.ok(safeURL(urls[0]));assert.equal(new Set(urls).size,1);
 }
 for(const entry of [...Object.values(media.clubs),...Object.values(media.players)]){assert.ok(safeURL(entry.url));assert.ok(safeURL(entry.source));assert.ok(entry.provider)}
});
test('accent search and whitespace work for incomplete records and coaches',()=>{const list=deduplicate([record]);assert.equal(filterTransfers(list,{q:'  karacic  ',pos:'coach'}).length,1)});
test('empty results reset every count',()=>assert.deepEqual(counts(filterTransfers(deduplicate([record]),{q:'absent'})),{all:0,signed:0,rumor:0,left:0,extended:0}));
test('same event merges sources, separate dated moves and rumors survive',()=>{const rows=deduplicate([record,{...record,id:'b',source_url:'https://example.com/confirmed',verified_at:'2026-09-08'},{...record,id:'c',date:'2026-09-05',status:'rumor'},{...record,id:'d',date:'2026-09-04'}]);assert.equal(rows.length,3);assert.equal(rows[0].id,'b');assert.ok(rows[0].alias_ids.includes('a'))});
test('invalid dates and unsafe URLs are rejected without crashing',()=>{for(const d of ['2026-13-01','2026-02-30','bad',null])assert.equal(dateValid(d),false);assert.equal(safeURL('javascript:alert(1)'), '');assert.equal(deduplicate([{...record,date:'bad'},{...record,status:'?'}]).length,0)});
test('database has unique public IDs and complete review provenance',()=>{const db=JSON.parse(fs.readFileSync(new URL('./transfers_all.json',import.meta.url))).items;const rows=deduplicate(db);assert.equal(new Set(rows.map(t=>t.id)).size,rows.length);assert.equal(rows.some(t=>t._visited),false);const updates=JSON.parse(fs.readFileSync(new URL('./data-review.json',import.meta.url))).items;assert.equal(updates.length,38);for(const t of updates){assert.ok(dateValid(t.date));assert.ok(safeURL(t.source_url));assert.equal(t.verified_at,'2026-09-08')}assert.equal(rows.find(t=>t.id==='sc-81293d3a').history[0].status,'rumor')});

import {isNewTransfer} from './data-core.mjs';
test('new badges use insertion time, expire after 24 hours and reject invalid or future times',()=>{
 const now=Date.parse('2026-09-09T12:00:00Z');
 assert.equal(isNewTransfer({date:'2020-01-01',added_at:'2026-09-09T10:00:00Z'},now),true);
 for(const added_at of [undefined,'bad','2026-09-10T00:00:00Z','2026-09-08T12:00:00Z'])assert.equal(isNewTransfer({added_at},now),false);
 assert.equal(isNewTransfer({verified_at:'2026-09-09'},now),false);
});
