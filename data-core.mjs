import {canonicalClub,clubSearchNames} from './club-identities.mjs?v=20260908-identities1';
export const STATUS = {signed:'Signed',rumor:'Rumor',left:'Departure',extended:'Extension'};
export const norm = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[đĐ]/g,'d').replace(/[łŁ]/g,'l').replace(/ı/g,'i').toLowerCase().replace(/\s+/g,' ').trim();
const leagues = {'greek basket league':'GBL','israeli winner league':'Israeli BSL','turkish bsl':'BSL','pro a':'Betclic Elite','lega':'Lega Basket','greek a1':'GBL','vtb united league':'VTB','croatian hkl':'HKL','ht liga':'HKL','croatian htl':'HKL','nbia hungary':'Hungarian NB1'};
export const clubName = canonicalClub;
export const competitions = value => [...new Set(String(value || '').split('/').map(x=>leagues[norm(x)]||x.trim()).filter(x=>x&&x!=='?'))];
export const unknown = value => !value || ['?','unknown','null'].includes(norm(value));
export const safeURL = value => {try {const url = new URL(value);return ['http:','https:'].includes(url.protocol)?url.href:'';}catch{return '';}};
export function dateValid(value) {try{return /^\d{4}-\d{2}-\d{2}$/.test(value||'') && new Date(value+'T12:00:00Z').toISOString().slice(0,10)===value;}catch{return false}}
export function normalize(record) {
 const t={...record};
 t.player=String(t.player||'').trim(); t.from=clubName(t.from); t.to=clubName(t.to);
 t.pos=/^(coach|hc|head coach)$/i.test(t.pos||'')?'coach':String(t.pos||'?').toUpperCase();
 t.leagues=competitions(t.league); t.league=t.leagues.join(' / '); t.status=norm(t.status);
 t.source_url=safeURL(t.source_url);
 t.search=norm([t.player,clubSearchNames(t.from),clubSearchNames(t.to),t.league,t.summary].join(' '));
 return t;
}
const personKey = t => norm(t.player).replace(/\bjr\.?$/,'').replace(/[^a-z0-9]/g,'');
export function deduplicate(records) {
 const seen=new Map();
 for(const raw of records) {
  if(raw._visited || raw._quarantined || !raw.player || !STATUS[raw.status] || !dateValid(raw.date)) continue;
  const t=normalize(raw);
  // Separate dated events and status changes. Never let a rumor hide a signing.
  const key=[personKey(t),norm(t.to),t.status,t.date].join('|');
  if(!seen.has(key)){seen.set(key,t);continue;}
  const old=seen.get(key);
  const winner=(t.verified_at && !old.verified_at)?t:old;
  const other=winner===old?t:old;
  for(const field of ['from','pos','contract','summary','nationality']) if(unknown(winner[field]) && !unknown(other[field])) winner[field]=other[field];
  winner.alias_ids=[...new Set([...(old.alias_ids||[]),...(t.alias_ids||[]),old.id,t.id])].filter(id=>id!==winner.id);
  winner.sources=[...new Map([...(old.sources||[]),...(t.sources||[]),{url:old.source_url,name:old.source_name},{url:t.source_url,name:t.source_name}].filter(s=>safeURL(s.url)).map(s=>[s.url,s])).values()];
  winner.league=[...new Set([...old.leagues,...t.leagues])].join(' / ');
  seen.set(key,normalize(winner));
 }
 return [...seen.values()].sort((a,b)=>b.date.localeCompare(a.date)||a.player.localeCompare(b.player));
}
export function filterTransfers(items,f={}) {
 const q=norm(f.q), team=norm(clubName(f.team));
 return items.filter(t=>(!q||t.search.includes(q)) && (!team||norm(t.from)===team||norm(t.to)===team)
  &&(!f.league||t.leagues.includes(f.league))&&(!f.pos||(t.pos.split(/[\/,-]/).map(p=>p.trim()).includes(f.pos)||(f.pos==='G'&&/PG|SG/.test(t.pos))||(f.pos==='F'&&/SF|PF/.test(t.pos))))
  &&(!f.status||t.status===f.status)&&(!f.from||t.date>=f.from)&&(!f.until||t.date<=f.until));
}
export function counts(items){return {all:items.length,...Object.fromEntries(Object.keys(STATUS).map(s=>[s,items.filter(t=>t.status===s).length]))};}

export function isNewTransfer(record, now=Date.now()) {
 const added=Date.parse(record.added_at);
 return Number.isFinite(added) && added<=now && now-added<72*60*60*1000;
}
