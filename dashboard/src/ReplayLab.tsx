import React,{useEffect,useState} from 'react';
import './style.css';
type Scenario={id:string;name:string;expected:string;story:string};
type Payment={recipient:string;amount_cents:number;approval:string;approval_id?:string;invoice:string};
type Replay={scenario:Scenario;mandate:{recipient:string;amount_cents:number;currency:string;single_use:boolean;expires_at:number};baseline:{label:string;decision:string;recipient:string;amount_cents:number;explanation:string}};
type Event={id:string;decision:string;reason:string;payment:Payment;analysis:{mode:string;risk:string;reason:string};duration_ms:number;created_at:string;replay?:Replay};
async function api(path:string,init?:RequestInit){const r=await fetch('/api'+path,init);const data=await r.json();if(!r.ok)throw Error(data.error||'Service unavailable');return data}
const money=(c:number)=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(c/100);
export default function ReplayLab(){
 const[catalog,setCatalog]=useState<Scenario[]>([]),[events,setEvents]=useState<Event[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState(''),[selected,setSelected]=useState('redirect'),[amount,setAmount]=useState('100'),[result,setResult]=useState<Event|null>(null);
 const refresh=async()=>setEvents(await api('/events'));
 useEffect(()=>{Promise.all([api('/catalog').then(setCatalog),refresh()]).catch(e=>setError(e.message))},[]);
 async function run(){
  const cents=Math.round(Number(amount)*100);
  if(!Number.isFinite(cents)||cents<1||cents>100000){setError('Enter a payment between $0.01 and $1,000.');return}
  setBusy(true);setError('');setResult(null);
  try{const e=await api('/replay',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scenario:selected,amount_cents:cents})});setResult(e);await refresh()}catch(e){setError(String(e))}finally{setBusy(false)}
 }
 async function repeatPayment(){
  if(!result)return;setBusy(true);setError('');
  try{const e=await api('/payments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(result.payment)});setResult(e);await refresh()}catch(e){setError(String(e))}finally{setBusy(false)}
 }
 const spec=catalog.find(s=>s.id===selected),replays=events.filter(e=>e.replay),blocked=replays.filter(e=>e.decision==='deny');
 return <main className="replay-lab"><header><div className="logo">◈ AgentShield <span>AI</span></div><div className="badge">ADVERSARIAL PAYMENT LAB · SIMULATION</div></header>
 <section className="hero"><p className="eyebrow">THE INVOICE IS DATA. IT DOESN’T GET TO GIVE ORDERS.</p><h1>Same agent. Same attack.<br/><span>A different ending.</span></h1><p>Watch a vulnerable agent follow a malicious invoice. Replay the same proposed action through a gateway that demands a trusted, expiring, single-use payment approval.</p></section>
 <section className="stats"><article><b>{replays.length}</b><span>Audited replays · latest 200 records</span></article><article><b>{blocked.length}</b><span>Proposals blocked</span></article><article><b>{money(blocked.reduce((v,e)=>v+e.payment.amount_cents,0))}</b><span>Blocked simulated value · not money saved</span></article></section>
 <div className="lab-layout"><aside className="panel"><h2>Build the attack</h2><p>Choose a fixture and the original trusted payment amount.</p><label className="amount">Trusted payment (USD)<input type="number" min="0.01" max="1000" step="0.01" value={amount} onChange={e=>setAmount(e.target.value)} disabled={busy}/></label>
 <div className="scenario-list">{catalog.map((s,i)=><button className={s.id===selected?'scenario selected':'scenario'} key={s.id} disabled={busy} onClick={()=>{setSelected(s.id);setResult(null)}}><span className="number">0{i+1}</span><span>{s.name}<small>{s.expected==='allow'?'Legitimate control':'Adversarial fixture'}</small></span><span>↗</span></button>)}</div>
 <p className="story">{spec?.story}</p><button className="run" disabled={busy||!catalog.length} onClick={run}>{busy?'Inspecting and committing audit…':'▶ Replay the attack'}</button>{error&&<p role="alert" className="error">{error}</p>}
 <p className="disclosure">The unguarded agent is a scripted vulnerable fixture. This is not a claim that a live model was compromised.</p></aside>
 <section className="result-area"><div className="result-title"><h2>Attack replay</h2><span className="badge">{result?result.analysis.mode.toUpperCase()+' ANALYZER':'READY TO INSPECT'}</span></div>
 {!result?<div className="waiting"><div className="shield">◈</div><h2>{busy?'One proposal. Two outcomes.':'What happens when an invoice gives orders?'}</h2><p>Select an attack and run the replay. You’ll see the original mandate, the compromised proposal, and the committed security decision.</p><div className="flow">Trusted mandate → Untrusted invoice → Tool proposal → Gateway</div></div>:<>
 {result.replay&&<><div className="mandate"><span>OPERATOR’S ORIGINAL MANDATE</span><b>Pay {result.replay.mandate.recipient} {money(result.replay.mandate.amount_cents)}</b><small>USD · expiring approval · single use · server-issued capability</small></div>
 <div className="comparison"><article className="outcome vulnerable"><p className="eyebrow">WITHOUT AGENTSHIELD</p><h3>Would execute</h3><b>{money(result.replay.baseline.amount_cents)}</b><p>To <code>{result.replay.baseline.recipient}</code></p><small>Scripted baseline · no approval validation</small></article><article className="outcome protected"><p className="eyebrow">WITH AGENTSHIELD</p><h3>{result.decision==='deny'?'Blocked':'Allowed simulation'}</h3><b>{money(result.payment.amount_cents)}</b><p>{result.reason}</p><small>Committed audit · {result.analysis.mode} analysis</small></article></div></>}
 <section className="panel evidence"><h2>Why this decision happened</h2>{result.decision==='allow'&&<button className="refresh" disabled={busy} onClick={repeatPayment}>Attempt duplicate payment with the same approval</button>}<ol><li><b>Untrusted invoice</b><blockquote>{result.payment.invoice}</blockquote></li><li><b>Proposed tool action</b><p>transfer({result.payment.recipient}, {money(result.payment.amount_cents)}, USD)</p></li><li><b>Risk analysis · {result.analysis.mode}</b><p><span className={result.analysis.risk==='low'?'allow':'deny'}>{result.analysis.risk.toUpperCase()}</span> — {result.analysis.reason}</p></li><li><b>Policy + atomic approval check</b><p>{result.reason}</p></li><li><b>Durable audit receipt</b><p>{result.id} · {new Date(result.created_at).toLocaleTimeString()}</p></li></ol><details><summary>Inspect full evidence JSON</summary><pre>{JSON.stringify(result,null,2)}</pre></details></section>
 </>}
 </section></div>
 <section className="panel history"><div className="result-title"><h2>Audit history</h2><button className="refresh" onClick={()=>refresh().catch(e=>setError(e.message))}>Refresh</button></div><p>Inspect a previous decision. History includes earlier demo records.</p><div className="history-list">{events.slice(0,20).map(e=><button key={e.id} onClick={()=>setResult(e)}><strong className={e.decision}>{e.decision.toUpperCase()}</strong><span>{e.replay?.scenario.name||e.payment.recipient}</span><span>{money(e.payment.amount_cents)}</span><small>{e.analysis.mode} · {new Date(e.created_at).toLocaleTimeString()}</small></button>)}</div></section>
 <footer>Simulation only. Mock mode is deterministic and does not demonstrate Meta model accuracy. The replay console creates demo approvals; production operator authentication is not implemented. No banking APIs.</footer>
 </main>
}
