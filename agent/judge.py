"""Trusted synthetic fixtures and layout heuristic; never enroll uploaded templates."""
import base64,json,math,time
from pathlib import Path
import workspace as ws,visual
ROOT=Path(__file__).resolve().parents[1]
CASES=[('clean','synthetic-invoice.pdf','Clean utility / service bill'),('hidden','synthetic-hidden-injection.pdf','Hidden prompt injection'),('shifted','synthetic-layout-swap.pdf','Look-alike merchant + routing shift')]
def migrate(db):db.execute('CREATE TABLE IF NOT EXISTS judge_pack (owner_id TEXT NOT NULL, case_id TEXT NOT NULL, document_id TEXT NOT NULL, invoice_id TEXT NOT NULL, PRIMARY KEY(owner_id,case_id))')
def load(owner,connect,pg):
    result=[]
    for case,filename,label in CASES:
        with connect() as db:row=ws.query(db,'SELECT document_id,invoice_id FROM judge_pack WHERE owner_id=? AND case_id=?',(owner,case),pg).fetchone()
        if row:result.append({'case':case,'label':label,'document_id':row[0],'invoice_id':row[1]});continue
        doc=visual.ingest({'filename':filename,'mime':'application/pdf','data':base64.b64encode((ROOT/'samples'/filename).read_bytes()).decode(),'use_muse':False},owner,connect,pg)
        inv=visual.confirm({'document_id':doc['id'],'fields':{'reference':'JUDGE-'+case.upper(),'vendor':'Acme Consulting','recipient':'vendor_acme','amount_cents':10000,'due_date':'2026-11-04','text':doc['fields']['invoice_text']}},owner,connect,pg)
        with connect() as db:ws.query(db,'INSERT INTO judge_pack(owner_id,case_id,document_id,invoice_id) VALUES (?,?,?,?)',(owner,case,doc['id'],inv['id']),pg)
        result.append({'case':case,'label':label,'document_id':doc['id'],'invoice_id':inv['id']})
    return {'cases':result,'source':'Synthetic, server-owned fixture pack. No payments executed; geometry is PDF-derived until you explicitly run SAM.'}

def baseline():
    import fitz
    boxes=[]
    with fitz.open(ROOT/'samples/synthetic-invoice.pdf') as doc:
        page=doc[0]
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                text=' '.join(s['text'] for s in line.get('spans',[]))
                if text.startswith(('Bank account:','Routing details:')):
                    x,y,r,b=line['bbox'];boxes.append({'x':x/page.rect.width,'y':y/page.rect.height,'w':(r-x)/page.rect.width,'h':(b-y)/page.rect.height})
    return boxes

def check(db,pg,owner,payment):
    result={'id':'visual','label':'Visual Template Anchor Binding','status':'not_measured','detail':'No linked document with a trusted Acme template. Manual invoices cannot receive layout verification.'}
    row=ws.query(db,'SELECT d.payload,i.vendor FROM documents d JOIN invoices i ON i.id=d.invoice_id WHERE d.invoice_id=? AND d.owner_id=?',(payment.get('invoice_id',''),owner),pg).fetchone()
    if not row:return result
    doc=json.loads(row[0])
    if row[1].strip().lower() not in ('acme consulting','acme corp'):result['detail']='No trusted template for this merchant; manual review required.';return result
    sam=doc.get('sam',{});use_sam=sam.get('status')=='completed' and sam.get('boxes')
    anchors=sam['boxes'] if use_sam else doc.get('anchors',[])
    source='live SAM 3.1 segments' if use_sam else 'PDF text geometry (SAM not measured)'
    banking=[a for a in anchors if a.get('label')=='banking'];expected=baseline()
    def distance(a,b):return math.hypot(a['x']+a['w']/2-b['x']-b['w']/2,a['y']+a['h']/2-b['y']-b['h']/2)
    deviations=[min((distance(a,b) for a in banking),default=1) for b in expected]
    # Normalized geometry, independent of raster resolution. No claim that a shift proves fraud.
    anomaly=not expected or max(deviations,default=1)>.035
    text=doc.get('fields',{}).get('invoice_text','')
    details_ok='Routing details: DEMO-NOT-A-BANK' in text
    result.update(status='fail' if anomaly or not details_ok else 'pass',detail=f'Trusted synthetic Acme template vs {source}; max normalized center deviation {max(deviations,default=1):.4f}, tolerance 0.035. '+('Layout/routing anomaly: review required.' if anomaly or not details_ok else 'Banking anchors and synthetic routing text match.'),evidence={'template_source':'Trusted synthetic Acme PDF geometry','observed_source':source,'expected':expected,'observed':banking,'deviations':deviations,'threshold':0.035,'routing_text_matches':details_ok})
    return result
