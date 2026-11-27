// Altri redditi (prestazioni occasionali, ritenuta d'acconto, stima 730). Dati solo in locale (extra.json).
let EX={items:[]},eyear=null;
const XCFG={metodo:"netto",addizionali_pct:2,base_override:0},xcfg=()=>({...XCFG,...(SET.extra_cfg||{})});
const irpefLorda=r=>{r=Math.max(0,r);return Math.min(r,28000)*.23+Math.max(0,Math.min(r,50000)-28000)*.33+Math.max(0,r-50000)*.43};   // L. 199/2025: 23/33/43%
const detrLav=r=>r<=15000?1955:r<=28000?1910+1190*(28000-r)/13000:r<=50000?1910*(50000-r)/22000:0;                                   // art. 13 TUIR
const irpefNetta=r=>Math.max(0,irpefLorda(r)-detrLav(r));
const xcalc=(it,c)=>{const n=+it.importo||0;if(!it.ritenuta)return{netto:n,lordo:n,rit:0};const rit=c.metodo==="lordo"?n/.8*.2:n*.2;return{netto:n,lordo:n+rit,rit}};
function baseAnnua(year,c){if(c.base_override>0)return c.base_override;const all=P();if(!all.length)return 0;let ps=all.filter(p=>p.anno===year);const proj=!ps.length;if(proj)ps=all;
 const l=ps[ps.length-1],pr=l.campi.prog_imponibile_fisc;if(!pr)return 0;return(year>all[0].anno||proj)?pr/l.mese*12:pr}
function xsum(year){const c=xcfg(),its=EX.items.filter(i=>i.data.startsWith(year)),base=baseAnnua(+year,c);
 const r=a=>{const s=a.reduce((t,i)=>{const k=xcalc(i,c);t.net+=k.netto;t.lordo+=k.lordo;t.rit+=k.rit;return t},{net:0,lordo:0,rit:0});
  s.imp=s.lordo?irpefNetta(base+s.lordo)-irpefNetta(base)+s.lordo*c.addizionali_pct/100:0;s.saldo=s.imp-s.rit;s.marg=s.lordo?s.imp/s.lordo*100:0;return s};
 return{base,c,its,inc:r(its.filter(i=>i.incassato)),tot:r(its),da:r(its.filter(i=>!i.incassato))}}
let xsaveBusy=false;const xsave=async items=>{if(xsaveBusy)return;xsaveBusy=true;const controls=()=>document.querySelectorAll("#xadd,#xsav,tr[data-id] input,tr[data-id] button");controls().forEach(el=>el.disabled=true);try{const r=await fetch("/api/extra",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({items})});if(!r.ok)throw new Error(`Salvataggio non riuscito (${r.status})`);EX=await r.json();sig="";await load()}catch(e){alert(e.message||"Errore durante il salvataggio dei redditi.")}finally{xsaveBusy=false;controls().forEach(el=>el.disabled=false)}};
const bracketSplit=(base,x)=>[[0,28000,"23%"],[28000,50000,"33%"],[50000,1e12,"43%"]].map(([a,b,l])=>[l,Math.max(0,Math.min(base,b)-a),Math.max(0,Math.min(base+x,b)-Math.max(a,base))]);
function extraViews(){const o={};
 o.alt=()=>{const ys=[...new Set([String(new Date().getFullYear()),...EX.items.map(i=>i.data.slice(0,4))])].sort().reverse();if(!eyear||!ys.includes(eyear))eyear=ys[0];
  const X=xsum(eyear),c=X.c,i=X.inc,t=X.tot,sp=bracketSplit(X.base,t.lordo),inpsAlert=t.lordo>5000;
  const row=it=>{const k=xcalc(it,c);return `<tr data-id="${esc(it.id)}"><td class="l">${it.data.split("-").reverse().join("/")}</td><td class="l">${esc(it.descrizione)||"—"}</td><td class="num">${n2(k.netto)}</td><td class="num">${k.rit?n2(k.rit):"—"}</td><td class="num">${n2(k.lordo)}</td>
   <td><input type="checkbox" data-f="incassato" ${it.incassato?"checked":""} title="Già incassato"></td><td><input type="checkbox" data-f="ritenuta" ${it.ritenuta?"checked":""} title="Ritenuta d'acconto già applicata"></td><td><button data-del="1">Elimina</button></td></tr>`};
  return `<div class="grid k">${kpi("Incassato (netto)",eur(i.net),"nell'anno "+eyear,"var(--g)")}${kpi("Da incassare",eur(X.da.net),"crediti ancora aperti","var(--a)")}${kpi("Ritenute versate",eur(i.rit),"già incluse nelle tasse dell'anno","var(--r)")}
  ${kpi("Imposta stimata su incassato",eur(i.imp),pc(i.marg)+" del lordo (IRPEF + addizionali)","var(--c)")}${kpi(i.saldo>=0?"730: da versare (stima)":"730: a credito (stima)",eur(Math.abs(i.saldo)),"imposta stimata − ritenute","var(--m)")}</div>
  <div class="grid g2" style="margin-top:16px"><div class="card"><h3>Nuovo reddito</h3><div style="display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));align-items:end">
   <label>Data<br><input type="date" id="xd" value="${new Date().toISOString().slice(0,10)}" style="width:100%"></label><label>Descrizione<br><input id="xn" maxlength="80" style="width:100%"></label><label>Importo netto ricevuto (€)<br><input id="xi" type="number" step="0.01" min="0" style="width:100%"></label></div>
   <div style="display:flex;gap:20px;margin:12px 0;flex-wrap:wrap"><label><input type="checkbox" id="xc" checked style="width:auto"> Già incassato</label><label><input type="checkbox" id="xr" checked style="width:auto"> Ritenuta d'acconto 20% applicata</label></div><button id="xadd" class="primary">Aggiungi</button></div>
   <div class="card"><h3>Parametri della stima</h3><div style="display:grid;gap:10px">
   <label>Calcolo della ritenuta<br><select id="xm" style="width:100%"><option value="netto" ${c.metodo==="netto"?"selected":""}>20% dell'importo netto inserito</option><option value="lordo" ${c.metodo==="lordo"?"selected":""}>20% del lordo (netto ÷ 0,80)</option></select></label>
   <label>Addizionali regionale + comunale (%)<br><input id="xa" type="number" step="0.01" min="0" max="5" value="${c.addizionali_pct}" style="width:100%"></label>
   <label>Reddito imponibile annuo da lavoro (€) <span class="note">vuoto = stima dalle buste paga: ${eur(X.base)}</span><br><input id="xb" type="number" step="1" min="0" value="${c.base_override||""}" style="width:100%"></label><button id="xsav">Salva parametri</button></div></div></div>
  <div class="grid g2" style="margin-top:16px"><div class="card"><h3>Stima 730 · ${eyear}</h3><table><tr><th class="l"></th><th>Già incassato</th><th>Con crediti da incassare</th></tr>
   ${[["Compensi lordi",i.lordo,t.lordo],["IRPEF + addizionali sui compensi",i.imp,t.imp],["Ritenute già versate",-i.rit,-t.rit]].map(r=>trow([r[0],n2(r[1]),n2(r[2])])).join("")}
   <tr class="tot"><td class="l">Saldo al 730</td><td class="num">${i.saldo>=0?"da versare":"a credito"} ${n2(Math.abs(i.saldo))}</td><td class="num">${t.saldo>=0?"da versare":"a credito"} ${n2(Math.abs(t.saldo))}</td></tr></table>
   <p class="note">Il reddito da lavoro stimato (${eur(X.base)}) cade nello scaglione del ${X.base>50000?"43":X.base>28000?"33":"23"}%. Aliquota media sull'extra: ${pc(t.marg)}.</p>
   ${c.metodo==="netto"?`<p class="note warn">Per legge la ritenuta è il 20% del compenso lordo: se l'importo inserito è il netto, la ritenuta reale è il 25% del netto. Puoi cambiare il metodo nei parametri.</p>`:""}
   ${inpsAlert?`<p class="note warn">Sopra 5.000 € di compensi occasionali annui scatta in genere il contributo INPS alla Gestione separata: non è incluso nella stima.</p>`:""}</div>
  <div class="card"><h3>Dove cade nello scaglione IRPEF</h3><table><tr><th class="l">Scaglione</th><th>Reddito da lavoro</th><th>Altri redditi (con crediti)</th></tr>${sp.map(r=>trow([r[0],n2(r[1]),n2(r[2])])).join("")}</table>
   <p class="note">Stima indicativa: IRPEF lorda con scaglioni 2026 (23% / 33% / 43%) meno detrazione da lavoro dipendente, differenza con e senza l'extra. Non considera altre detrazioni, bonus e il trattamento integrativo. Per la dichiarazione definitiva rivolgiti a un CAF o a un commercialista.</p></div></div>
  <div class="card" style="margin-top:16px"><h3>Redditi registrati · ${eyear} <select id="xy">${ys.map(y=>`<option ${y===eyear?"selected":""}>${y}</option>`).join("")}</select></h3>
   ${X.its.length?`<div class="sc"><table><tr><th class="l">Data</th><th class="l">Descrizione</th><th>Netto</th><th>Ritenuta</th><th>Lordo</th><th>Incassato</th><th>Ritenuta</th><th></th></tr>${[...X.its].sort((a,b)=>b.data.localeCompare(a.data)).map(row).join("")}</table></div>`:'<div class="note">Nessun reddito registrato per quest\'anno.</div>'}</div>`};
 o.alt.after=()=>{$("#xy").onchange=e=>{eyear=e.target.value;render()};
  $("#xadd").onclick=()=>{const v=+$("#xi").value,d=$("#xd").value;if(!(v>0)||!d)return alert("Inserisci data e importo.");xsave([...EX.items,{id:Date.now().toString(36)+Math.random().toString(36).slice(2,6),data:d,descrizione:$("#xn").value.trim(),importo:v,incassato:$("#xc").checked,ritenuta:$("#xr").checked}])};
  $("#xsav").onclick=()=>post({extra_cfg:{metodo:$("#xm").value,addizionali_pct:+$("#xa").value||0,base_override:+$("#xb").value||0}});
  document.querySelectorAll("tr[data-id]").forEach(tr=>{const id=tr.dataset.id;tr.querySelectorAll("input[data-f]").forEach(cb=>cb.onchange=()=>xsave(EX.items.map(i=>i.id===id?{...i,[cb.dataset.f]:cb.checked}:i)));
   tr.querySelector("[data-del]").onclick=()=>confirm("Eliminare questo reddito?")&&xsave(EX.items.filter(i=>i.id!==id))})};
 return o}
