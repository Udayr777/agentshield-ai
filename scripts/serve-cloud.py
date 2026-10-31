"""Supervise the local-only Python service and public Go gateway in one free web service."""
import os,signal,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if not os.getenv('DATABASE_URL') or not os.getenv('LEDGER_SIGNING_KEY') or not os.getenv('SERVICE_TOKEN'):raise SystemExit('Cloud runtime requires DATABASE_URL, LEDGER_SIGNING_KEY and SERVICE_TOKEN.')
env={**os.environ,'AGENT_BIND':'127.0.0.1','AGENT_PORT':'8001','AGENT_URL':'http://127.0.0.1:8001','GATEWAY_ADDR':'0.0.0.0:'+os.getenv('PORT','10000'),'STATIC_DIR':str(ROOT/'dashboard/dist')}
children=[];stopping=False
def stop(*args):
    global stopping
    stopping=True
    for p in children:
        if p.poll() is None:p.terminate()
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
try:
    children.append(subprocess.Popen([sys.executable,'app.py'],cwd=ROOT/'agent',env=env))
    ready=False
    for _ in range(90):
        if stopping or children[0].poll() is not None:break
        try:
            with urllib.request.urlopen('http://127.0.0.1:8001/health',timeout=1) as r:ready=r.status==200
        except Exception:pass
        if ready:break
        time.sleep(1)
    if not ready:raise RuntimeError('Python service did not become ready; inspect migration logs.')
    children.append(subprocess.Popen([str(ROOT/'gateway/gateway')],cwd=ROOT/'gateway',env=env))
    while not stopping and all(p.poll() is None for p in children):time.sleep(.5)
    if not stopping:raise RuntimeError('A service exited; restarting the full container is required.')
finally:
    stop()
    for p in children:
        try:p.wait(timeout=8)
        except subprocess.TimeoutExpired:p.kill();p.wait()
