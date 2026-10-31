"""Bounded first-page PDF visibility heuristics. No OCR, steganography or authenticity claims."""
import base64,io,math
from PIL import Image,ImageOps,ImageEnhance,ImageStat

VERSION='visibility-v1'
def load_fixture(data,owner,connect,pg):
    from pathlib import Path
    import visual,workspace as ws
    kind=data.get('kind')
    if kind not in ('clean','white_text','tiny_text','invisible_layer','overlap'):raise ws.APIError(400,'Choose a known synthetic visibility fixture.')
    path=Path(__file__).resolve().parents[1]/'samples'/'visual-inspection'/f'{kind}-1.pdf'
    return visual.ingest({'filename':path.name,'mime':'application/pdf','data':base64.b64encode(path.read_bytes()).decode(),'use_muse':False},owner,connect,pg)

def image_url(image):
    out=io.BytesIO();image.save(out,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(out.getvalue()).decode()

def inspect(preview,page=None):
    result={'version':VERSION,'page':1,'findings':[],'checks':{},'limits':'First-page heuristics only. A finding is suspicious evidence, not proof of an attack. No OCR, semantic text/image comparison, steganography detection or authenticity verification is performed.'}
    if not preview:
        result['status']='not_measured';result['reason']='No rendered image is available.';return result
    with Image.open(io.BytesIO(base64.b64decode(preview.split(',',1)[1]))) as source:
        image=source.convert('RGB')
    enhanced=ImageEnhance.Contrast(ImageOps.autocontrast(image.convert('L'),cutoff=0.5)).enhance(1.8)
    result['enhanced_preview']=image_url(enhanced)
    if page is None:
        result['status']='not_measured';result['reason']='Raster image: PDF text geometry is unavailable. Contrast view is provided; text visibility checks need a text-bearing PDF.'
        return result
    width,height=page.rect.width,page.rect.height
    spans=[s for b in page.get_text('dict')['blocks'] for line in b.get('lines',[]) for s in line.get('spans',[]) if s.get('text','').strip()]
    traces=page.get_texttrace();result['status']='measured';result['examined_spans']=min(len(spans),400);result['truncated']=len(spans)>400
    def box(bounds):
        x0,y0,x1,y1=bounds;x0=max(0,min(1,x0/width));y0=max(0,min(1,y0/height));x1=max(x0,min(1,x1/width));y1=max(y0,min(1,y1/height))
        return {'x':x0,'y':y0,'w':x1-x0,'h':y1-y0}
    def finding(kind,bounds,metrics):
        if len(result['findings'])<80:result['findings'].append({'id':'e'+str(len(result['findings'])+1),'kind':kind,'box':box(bounds),'metrics':metrics})
        else:result['findings_truncated']=True
    def luminance(rgb):
        channels=[c/255 for c in rgb];linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in channels]
        return .2126*linear[0]+.7152*linear[1]+.0722*linear[2]
    visible=[]
    for span in spans[:400]:
        bounds=span['bbox'];x0,y0,x1,y1=bounds
        if x1<=x0 or y1<=y0:continue
        b=box(bounds);left=int(b['x']*image.width);top=int(b['y']*image.height);right=min(image.width,math.ceil((b['x']+b['w'])*image.width));bottom=min(image.height,math.ceil((b['y']+b['h'])*image.height))
        if right<=left or bottom<=top:continue
        # Corners are a local background estimate, not a reconstruction of the document.
        points=[image.getpixel((max(0,min(image.width-1,x)),max(0,min(image.height-1,y)))) for x,y in ((left-2,top-2),(right+1,top-2),(left-2,bottom+1),(right+1,bottom+1))]
        background=tuple(sorted(p[c] for p in points)[2] for c in range(3));color=span.get('color',0);foreground=((color>>16)&255,(color>>8)&255,color&255)
        a,c=luminance(foreground),luminance(background);contrast=(max(a,c)+.05)/(min(a,c)+.05)
        if contrast<1.5:finding('low_contrast',bounds,{'contrast_ratio':round(contrast,2),'threshold_below':1.5,'background_method':'four neighboring corners'})
        if span.get('size',12)<6:finding('tiny_text',bounds,{'font_points':round(span['size'],2),'threshold_below':6})
        crop=image.crop((left,top,right,bottom)).convert('L');spread=ImageStat.Stat(crop).stddev[0]
        if spread<2:finding('render_visibility_mismatch',bounds,{'pixel_stddev':round(spread,2),'threshold_below':2,'method':'Extractable text with a nearly flat rendered region; not an OCR comparison'})
        visible.append(span)
    for trace in traces[:400]:
        if trace.get('type')==3 or trace.get('opacity',1)<.1:
            finding('invisible_text_layer',trace['bbox'],{'render_mode':trace.get('type'),'opacity':trace.get('opacity',1)})
    for i,s in enumerate(visible):
        a=s['bbox'];area=max(.001,(a[2]-a[0])*(a[3]-a[1]))
        for t in visible[i+1:]:
            if s['text']==t['text']:continue
            b=t['bbox'];intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]));ratio=intersection/min(area,max(.001,(b[2]-b[0])*(b[3]-b[1])))
            if ratio>.65:
                finding('overlapping_text',a,{'intersection_over_smaller_area':round(ratio,2),'threshold_above':.65});break
    for kind in ('low_contrast','tiny_text','render_visibility_mismatch','invisible_text_layer','overlapping_text'):
        result['checks'][kind]={'status':'measured','findings':sum(f['kind']==kind for f in result['findings'])}
    result['checks']['semantic_ocr_comparison']={'status':'not_measured','reason':'No independent OCR engine is configured.'}
    return result

def explain(data,owner,connect,pg):
    import os,json,time,uuid
    import visual,workspace as ws
    from meta_client import complete_json,MetaError
    doc=visual.get_document(data.get('document_id'),owner,connect,pg)
    if doc.get('source')=='gmail':raise ws.APIError(403,'Gmail evidence remains local-only; Muse explanation is disabled.')
    evidence=doc.get('inspection')
    if not evidence or evidence.get('status')!='measured':raise ws.APIError(400,'Upload a text-bearing PDF with measured visibility evidence first.')
    if os.getenv('ANALYZER_MODE')!='meta':raise ws.APIError(400,'Explanation requires live Meta mode.')
    now=int(time.time())
    with connect() as db:
        if pg:db.execute('SELECT pg_advisory_xact_lock(4815162347)')
        row=ws.query(db,'SELECT payload FROM inspection_explanations WHERE document_id=? AND owner_id=?',(doc['id'],owner),pg).fetchone()
        if row:
            cached=json.loads(row[0])
            if cached.get('status')=='complete':return cached
            raise ws.APIError(409,'An explanation was already attempted for this document. Inspect local evidence; no automatic retry is made.')
        if ws.query(db,'SELECT COUNT(*) FROM inspection_explanations WHERE owner_id=? AND created_at>?',(owner,now-3600),pg).fetchone()[0]>=5 or db.execute('SELECT COUNT(*) FROM inspection_explanations WHERE created_at>'+str(now-3600)).fetchone()[0]>=20:raise ws.APIError(429,'Explanation budget reached: five per account and twenty per deployment per hour.')
        ws.query(db,'INSERT INTO inspection_explanations(document_id,owner_id,payload,created_at) VALUES (?,?,?,?)',(doc['id'],owner,json.dumps({'status':'pending'}),now),pg)
    schema={'type':'object','properties':{'summary':{'type':'string'},'evidence_ids':{'type':'array','items':{'type':'string'}},'next_step':{'type':'string'}},'required':['summary','evidence_ids','next_step'],'additionalProperties':False}
    try:
        result,meta=complete_json('visual_evidence_explanation','Explain only the supplied first-page numerical PDF visibility findings. These are heuristic observations, not proof of an attack. Never invent text, merchant identity, OCR results, steganography, SAM results or payment authority. Cite only supplied finding IDs; for no findings return an empty evidence_ids array and state that no observed findings does not establish safety. Recommend manual comparison and field review. Keep summary and next_step each under 1200 characters.',{'findings':evidence['findings'],'checks':evidence['checks'],'limits':evidence['limits']},schema)
        allowed={f['id'] for f in evidence['findings']}
        if not isinstance(result.get('summary'),str) or not isinstance(result.get('next_step'),str) or not isinstance(result.get('evidence_ids'),list) or len(result['summary'])>1200 or len(result['next_step'])>1200 or any(not isinstance(i,str) or i not in allowed for i in result['evidence_ids']):raise ValueError('Invalid references')
        output={**result,'status':'complete','model':meta['model'],'usage':meta.get('usage',{}),'scope':'Numeric first-page findings only; no original image or invoice text supplied.'}
    except Exception:
        with connect() as db:ws.query(db,'UPDATE inspection_explanations SET payload=? WHERE document_id=? AND owner_id=?',(json.dumps({'status':'failed'}),doc['id'],owner),pg)
        raise ws.APIError(503,'Muse explanation failed. Local findings remain available; no automatic retry or payment action occurred.') from None
    with connect() as db:ws.query(db,'UPDATE inspection_explanations SET payload=? WHERE document_id=? AND owner_id=?',(json.dumps(output),doc['id'],owner),pg)
    return output

def cached_clip(ident,owner,connect,pg):
    import json,visual,workspace as ws
    doc=visual.get_document(ident,owner,connect,pg)
    with connect() as db:row=ws.query(db,'SELECT payload FROM inspection_explanations WHERE document_id=? AND owner_id=?',(doc['id']+':clip-v1',owner),pg).fetchone()
    return json.loads(row[0]) if row else {'status':'not_generated'}

def clip(data,owner,connect,pg):
    """Muse writes bounded captions; the browser renders video, not the model API."""
    import os,json,time
    import visual,workspace as ws
    from meta_client import complete_json
    doc=visual.get_document(data.get('document_id'),owner,connect,pg)
    if doc.get('source')=='gmail':raise ws.APIError(403,'Gmail documents cannot be sent for Muse clip scripting.')
    evidence=doc.get('inspection')
    if not evidence or evidence.get('status')!='measured':raise ws.APIError(400,'Load a PDF with measured first-page findings.')
    if os.getenv('ANALYZER_MODE')!='meta':raise ws.APIError(400,'Muse clip scripting requires live Meta mode.')
    cache_id=doc['id']+':clip-v1';now=int(time.time())
    with connect() as db:
        if pg:db.execute('SELECT pg_advisory_xact_lock(4815162347)')
        row=ws.query(db,'SELECT payload FROM inspection_explanations WHERE document_id=? AND owner_id=?',(cache_id,owner),pg).fetchone()
        if row:
            result=json.loads(row[0])
            if result.get('status')=='complete':return result
            raise ws.APIError(409,'Clip scripting was already attempted. No automatic retry is made.')
        if ws.query(db,'SELECT COUNT(*) FROM inspection_explanations WHERE owner_id=? AND created_at>?',(owner,now-3600),pg).fetchone()[0]>=5 or ws.query(db,'SELECT COUNT(*) FROM inspection_explanations WHERE created_at>?',(now-3600,),pg).fetchone()[0]>=20:raise ws.APIError(429,'New Muse generation limit reached: five per account and twenty per deployment in a rolling hour. Saved clips can still replay without credits. Try new generation after the window expires.')
        ws.query(db,'INSERT INTO inspection_explanations(document_id,owner_id,payload,created_at) VALUES (?,?,?,?)',(cache_id,owner,json.dumps({'status':'pending'}),now),pg)
    scene={'type':'object','properties':{'caption':{'type':'string'},'evidence_ids':{'type':'array','items':{'type':'string'}}},'required':['caption','evidence_ids'],'additionalProperties':False}
    schema={'type':'object','properties':{'scenes':{'type':'array','items':scene,'minItems':3,'maxItems':3}},'required':['scenes'],'additionalProperties':False}
    try:
        result,meta=complete_json('visual_clip_script','Write exactly THREE short scenes for an 18-second invoice VISIBILITY explanation: (1) observable findings, (2) their uncertainty/meaning, (3) next manual review step. EACH caption must contain 4 to 14 whitespace-separated words and at most 120 characters, suitable for six seconds of narration. Cite only supplied evidence IDs; use an empty list when making a general caution. Do not invent invoice text, amount, merchant, fraud, OCR, SAM, steganography or payment results. If no findings, say no findings under these checks does NOT establish safety. Never say clean, safe, authentic, approved or payment blocked: only first-page visibility is known. Next step must be inspect regions and manually verify fields/recipient, not execute a payment. All captions are plain text, no markup.',{'findings':evidence['findings'],'limits':evidence['limits'],'scope':'First-page PDF visibility only; no payment decision is supplied.'},schema)
        scenes=result.get('scenes');allowed={f['id'] for f in evidence['findings']}
        if not isinstance(scenes,list) or len(scenes)!=3:raise ValueError('Scene count')
        for s in scenes:
            if not isinstance(s,dict) or not isinstance(s.get('caption'),str) or not 4<=len(s['caption'].split())<=14 or len(s['caption'])>120 or not isinstance(s.get('evidence_ids'),list) or any(not isinstance(i,str) or i not in allowed for i in s['evidence_ids']):raise ValueError('Invalid scene')
        output={'status':'complete','duration_seconds':18,'scenes':scenes,'model':meta['model'],'usage':meta.get('usage',{}),'source':'Muse script; AgentShield browser animation; optional browser voice. Not Meta-generated video or audio.'}
    except Exception:
        with connect() as db:ws.query(db,'UPDATE inspection_explanations SET payload=? WHERE document_id=? AND owner_id=?',(json.dumps({'status':'failed'}),cache_id,owner),pg)
        raise ws.APIError(503,'Muse clip script failed validation or generation. No automatic retry or payment action occurred.') from None
    with connect() as db:ws.query(db,'UPDATE inspection_explanations SET payload=? WHERE document_id=? AND owner_id=?',(json.dumps(output),cache_id,owner),pg)
    return output
