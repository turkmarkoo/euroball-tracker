export const STATUS = {signed:'Signed',rumor:'Rumor',left:'Departure',extended:'Extension'};
export const norm = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[đĐ]/g,'d').replace(/[łŁ]/g,'l').toLowerCase().trim();
const aliases = {
 'fc barcelona':'Barcelona','partizan belgrade':'Partizan Mozzart Bet Belgrade','cholet basket':'Cholet','energa trefl sopot':'Trefl Sopot','wks slask wroclaw':'Slask Wroclaw','denizli basket':'Yukatel Denizli',
 'partizan':'Partizan Mozzart Bet Belgrade','zalgiris':'Zalgiris Kaunas','asvel':'LDLC ASVEL',
 'fc bayern munich':'Bayern Munich','bayern munchen':'Bayern Munich','fenerbahce':'Fenerbahce Beko',
 'borac cacak':'Borac Mozzart','rotterdam city':'Rotterdam City','zeeuw & zeeuw rotterdam':'Rotterdam City',
 'zeeuw & zeeuw rotterdam city':'Rotterdam City','u-bt cluj-napoca':'UBT Cluj-Napoca',
 'tuerk telekom':'Turk Telekom','twarde pierniki torun':'Twarde Pierniki Torun',
 'frankfurt skyliners':'Skyliners Frankfurt','filou oostende':'Coretec Oostende',
 'csu sibiu':'CSU Sibiu','bc csu sibiu':'CSU Sibiu','kk krka':'Krka',
 'baskonia':'Baskonia','kosner baskonia':'Baskonia','tofas':'Tofas',
 'crvena zvezda meridianbet':'Crvena zvezda','crvena zvezda':'Crvena zvezda'
};
const leagues = {'greek basket league':'GBL','israeli winner league':'Israeli BSL','turkish bsl':'BSL','pro a':'Betclic Elite','lega':'Lega Basket','greek a1':'GBL','vtb united league':'VTB','croatian hkl':'HKL','ht liga':'HKL','croatian htl':'HKL','nbia hungary':'Hungarian NB1'};
export const clubName = name => aliases[norm(name)] || String(name ?? '').trim();
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
 t.search=norm([t.player,t.from,t.to,t.league,t.summary].join(' '));
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
 const q=norm(f.q), team=norm(f.team);
 return items.filter(t=>(!q||t.search.includes(q)) && (!team||norm(t.from)===team||norm(t.to)===team)
  &&(!f.league||t.leagues.includes(f.league))&&(!f.pos||(t.pos.split(/[\/,-]/).map(p=>p.trim()).includes(f.pos)||(f.pos==='G'&&/PG|SG/.test(t.pos))||(f.pos==='F'&&/SF|PF/.test(t.pos))))
  &&(!f.status||t.status===f.status)&&(!f.from||t.date>=f.from)&&(!f.until||t.date<=f.until));
}
export function counts(items){return {all:items.length,...Object.fromEntries(Object.keys(STATUS).map(s=>[s,items.filter(t=>t.status===s).length]))};}
