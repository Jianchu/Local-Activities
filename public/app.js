/* No source HTML is injected into the page. Every activity field is escaped. */
const $ = (s) => document.querySelector(s);
const categories = {
  'Nature & outdoors': { tint: '#e4ebd9', accent: '#8aa169', symbol: '❋' },
  'Arts & culture': { tint: '#eee4dc', accent: '#b5947d', symbol: '◈' },
  'Sports & wellness': { tint: '#dee9e6', accent: '#7caaa0', symbol: '↗' },
  'Learn & create': { tint: '#e9e5ef', accent: '#a092b3', symbol: '✎' },
  'Community & festivals': { tint: '#f0ead7', accent: '#b2a063', symbol: '☀' }
};
let events = [], city = 'all', category = 'all';
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const iso = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
const today = () => new Date(new Intl.DateTimeFormat('en-CA', {timeZone:'America/Vancouver',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date())+'T12:00:00');
function range(value) {
  const a=today(), b=new Date(a);
  if(value==='custom') return [$('#from').value || iso(a), $('#to').value || '9999-12-31'];
  if(value==='today') return [iso(a),iso(a)];
  if(value==='week') { b.setDate(b.getDate()+6); return [iso(a),iso(b)]; }
  if(value==='weekend') { const day=a.getDay(); a.setDate(a.getDate()+(day===0?0:(6-day+7)%7)); b.setTime(a.getTime()); b.setDate(a.getDate()+(a.getDay()===0?0:1)); return [iso(a),iso(b)]; }
  if(value==='month') { a.setMonth(a.getMonth()+1,1); b.setFullYear(a.getFullYear(),a.getMonth()+1,0); return [iso(a),iso(b)]; }
  return [iso(a),'9999-12-31'];
}
function timeMatches(raw, filter) {
  if(filter==='all') return true;
  // Match published intervals, including multi-line opening hours. Unknown times are excluded.
  const normalized=raw.toLowerCase().replace(/\./g,'').replace(/\bnoon\b/g,'12pm').replace(/\bmidnight\b/g,'12am');
  const windows={morning:[0,12],afternoon:[12,17],evening:[17,24]}, [lo,hi]=windows[filter];
  const hour=(h,m,ap)=>Number(h)%12+Number(m||0)/60+(ap==='pm'?12:0);
  const intervals=[...normalized.matchAll(/(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*[-–—]\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)/g)];
  if(intervals.length) return intervals.some(m=> {let start=hour(m[1],m[2],m[3]||m[6]),end=hour(m[4],m[5],m[6]); if(!m[3]&&start>end)start-=12; return end<start ? start<hi || end>lo : start<hi&&end>lo;});
  return [...normalized.matchAll(/(\d{1,2})(?::(\d{2}))?\s*(am|pm)/g)].some(m=>{const h=hour(m[1],m[2],m[3]);return h>=lo&&h<hi;});
}
const clock='<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7"/><path d="M10 5v5l3 2"/></svg>';
const pin='<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M16 8c0 5-6 9-6 9S4 13 4 8a6 6 0 1 1 12 0Z"/><circle cx="10" cy="8" r="2"/></svg>';
function safeUrl(raw){ try{const u=new URL(raw); return u.protocol==='https:' ? u.href : '#';}catch{return '#';} }
function card(e) {
  const c=categories[e.category]||categories['Community & festivals'];
  const d=e.startDate ? new Date(e.startDate+'T12:00:00') : null;
  const multi=e.startDate && e.endDate && e.startDate!==e.endDate;
  const ongoing=multi&&e.startDate<iso(today());
  const stamp=d?`<strong>${d.getDate()}</strong><span>${d.toLocaleDateString('en-CA',{month:'short'})}<br>${d.getFullYear()}</span>`:'<strong>↗</strong><span>Date<br>see source</span>';
  return `<article class="card" style="--tint:${c.tint};--accent:${c.accent}"><div class="card-cap"><div class="date-stamp">${ongoing?'<strong>↻</strong><span>Ongoing<br>activity</span>':stamp}</div><span class="cap-symbol" aria-hidden="true">${c.symbol}</span></div><div class="card-body"><div class="card-meta"><span class="city-label">${esc(e.city)}</span>${e.isFree?'<span class="free">Free entry</span>':''}</div><h3>${esc(e.title)}</h3><div class="facts"><div class="fact">${clock}<span>${esc(e.time)}</span></div><div class="fact">${pin}<span>${esc(e.location)}</span></div></div>${multi?`<p class="range-label">${esc(e.dateLabel)} · Schedule varies</p>`:''}<p class="description" id="desc-${e.id}">${esc(e.description)}</p><button class="more" data-expand="${e.id}" aria-controls="desc-${e.id}" aria-expanded="false">Read description +</button><div class="card-bottom"><span>${esc(e.category)}</span><a href="${esc(safeUrl(e.url))}" target="_blank" rel="noopener noreferrer" aria-label="Official details for ${esc(e.title)} (opens in a new tab)">Event details <b>↗</b></a></div></div></article>`;
}
function render() {
  const [a,b]=range($('#when').value), q=$('#search').value.toLowerCase().trim();
  $('#date-error').hidden=a<=b;
  const filtered=events.filter(e=>(city==='all'||e.city===city)&&(category==='all'||e.category===category)&&(!q||`${e.title} ${e.description} ${e.location}`.toLowerCase().includes(q))&&a<=b&&(e.endDate||e.startDate||'9999')>=a&&(e.startDate||'0000')<=b&&timeMatches(e.time,$('#daytime').value));
  filtered.sort((x,y)=>(x.startDate<a?a:x.startDate||'9999').localeCompare(y.startDate<a?a:y.startDate||'9999')||x.title.localeCompare(y.title));
  $('#count').textContent=filtered.length;
  $('#live').textContent=`${filtered.length} activity listings found`;
  $('#result-title').firstChild.textContent=city==='all'?'Coming up nearby ':`Coming up in ${city} `;
  $('#reset').hidden=filtered.length>0;
  if(!filtered.length){$('#cards').innerHTML='<div class="empty"><span style="font-size:40px">✳</span><h3>A little too quiet here.</h3><p>Try another date, city, or activity type.</p></div>';return;}
  if($('#group').checked) $('#cards').innerHTML=Object.entries(categories).map(([name,c])=> {const group=filtered.filter(e=>e.category===name);return group.length?`<h3 class="section-title">${c.symbol} ${esc(name)} <small>${group.length}</small></h3><div class="card-grid">${group.map(card).join('')}</div>`:'';}).join('');
  else $('#cards').innerHTML=`<div class="card-grid">${filtered.map(card).join('')}</div>`;
}
document.querySelectorAll('[data-city]').forEach(b=>b.addEventListener('click',()=>{city=b.dataset.city;document.querySelectorAll('[data-city]').forEach(x=>{x.classList.toggle('selected',x===b);x.setAttribute('aria-pressed',x===b);});render();}));
document.querySelectorAll('[data-category]').forEach(b=>b.addEventListener('click',()=>{category=b.dataset.category;document.querySelectorAll('[data-category]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',x===b);});render();}));
['search','when','daytime','from','to','group'].forEach(id=>$('#'+id).addEventListener(id==='search'?'input':'change',()=>{$('#custom-dates').hidden=$('#when').value!=='custom';render();}));
$('#cards').addEventListener('click',e=>{const b=e.target.closest('[data-expand]');if(!b)return;const open=b.getAttribute('aria-expanded')!=='true';b.setAttribute('aria-expanded',open);b.textContent=open?'Less −':'Read description +';$('#desc-'+b.dataset.expand).classList.toggle('expanded',open);});
$('#reset').addEventListener('click',()=>{$('#search').value='';$('#when').value='upcoming';$('#daytime').value='all';$('#custom-dates').hidden=true;document.querySelector('[data-city="all"]').click();document.querySelector('[data-category="all"]').click();});
async function load(){try{const r=await fetch('/data/events.json');if(!r.ok)throw new Error('Data unavailable');const data=await r.json();if(!Array.isArray(data.events))throw new Error('Invalid data');events=data.events;const statuses=Object.entries(data.sources||{});const stale=statuses.filter(([,s])=>s.status!=='ok'||Date.now()-new Date(s.updatedAt).getTime()>48*3600*1000);if(stale.length){$('#notice').hidden=false;$('#notice').textContent=`${stale.map(([city])=>city).join(' and ')} listings may be out of date. Showing the last available collection; confirm plans with the official source.`;}$('#freshness').textContent=statuses.map(([city,s])=>`${city} updated ${s.updatedAt?new Date(s.updatedAt).toLocaleString('en-CA',{timeZone:'America/Vancouver',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}):'not yet'}`).join(' · ');render();}catch{$('#cards').innerHTML='<div class="empty"><h3>We couldn’t load the calendar.</h3><p>Please refresh or check the official city calendars.</p><a href="https://www.surrey.ca/news-events/events">Surrey ↗</a> · <a href="https://www.richmond.ca/culture/calendar/search/default.aspx">Richmond ↗</a></div>';$('#live').textContent='Unable to load activities.';}}
load();
