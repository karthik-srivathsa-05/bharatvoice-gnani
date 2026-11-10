import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field
from .engine import Strict,process,Revision
from .store import Store,Conflict
from .stt import GnaniPrisma,STTError
from .evaluation import evaluate,FIXTURES
import json

load_dotenv()
def create_app(db=None):
    app=FastAPI(title='BharatVoice',version='0.1.0')
    path=db or os.getenv('BHARATVOICE_DB','work/bharatvoice.sqlite3')
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    store=Store(path);app.state.store=store;app.state.stt=GnaniPrisma()
    def get(sid):
        try:return store.get(sid)
        except KeyError:raise HTTPException(404,'Session not found')
    def save(s,version):
        try:store.save(s,version)
        except Conflict as e:raise HTTPException(409,str(e))
    def check(s,version):
        if s.version!=version:raise HTTPException(409,'Session changed. Resume and retry.')
    @app.get('/api/health')
    def health():return {'ok':True,'gnani_configured':bool(os.getenv('GNANI_API_KEY')),'model':'prisma-v3.0','extractor':'bounded-offline-grammar','live_verified':False}
    @app.post('/api/sessions',status_code=201)
    def create():return store.create().view()
    @app.get('/api/sessions/{sid}')
    def resume(sid:str):return get(sid).view()
    @app.post('/api/sessions/{sid}/turns')
    def turn(sid:str,body:Turn):
        s=get(sid);check(s,body.version)
        if body.target_id and not any(i.id==body.target_id for i in s.issues):raise HTTPException(404,'Issue not found')
        process(s,body.text,'typed',body.target_id);save(s,body.version);return s.view()
    @app.post('/api/sessions/{sid}/fixtures/{number}')
    def fixture(sid:str,number:int,body:Version):
        fixtures=json.loads(FIXTURES.read_text())
        if not 1<=number<=len(fixtures):raise HTTPException(404,'Fixture not found')
        s=get(sid);check(s,body.version)
        for text in fixtures[number-1]['turns']:process(s,text,'synthetic_fixture')
        save(s,body.version);return s.view()
    @app.post('/api/sessions/{sid}/audio')
    async def audio(sid:str,version:int=Form(...),authorized:bool=Form(...),audio_file:UploadFile=File(...)):
        s=get(sid);check(s,version)
        if not authorized:raise HTTPException(422,'Use only recordings you are authorized to process.')
        data=await audio_file.read(10*1024*1024+1)
        try:result=await app.state.stt.transcribe(data,audio_file.filename or '')
        except STTError as e:raise HTTPException(e.status,e.message)
        if result['transcript'].strip():process(s,result['transcript'],'gnani_live')
        else:s.turns.append({'text':'','source':'gnani_live'});s.version+=1
        s.turns[-1]['stt_metadata']=result
        save(s,version);return s.view()
    @app.post('/api/sessions/{sid}/issues/{iid}/review')
    def review(sid:str,iid:str,body:Review):
        s=get(sid);check(s,body.version)
        issue=next((i for i in s.issues if i.id==iid),None)
        if not issue:raise HTTPException(404,'Issue not found')
        if body.action=='clarify':
            issue.blocked=False;issue.confirmed=False;issue.version+=1
        elif body.action=='revoke':issue.confirmed=False;issue.version+=1
        else:
            if issue.missing:raise HTTPException(422,'Incomplete or unresolved issues cannot be confirmed.')
            issue.confirmed=True
        s.turns.append({'text':body.action,'source':'explicit_review','issue_id':iid,'issue_version':issue.version})
        s.prompts=[f'{i.category.title()}: please provide '+', '.join(i.missing)+'.' for i in s.issues if i.missing]
        s.version+=1;save(s,body.version);return s.view()
    @app.post('/api/sessions/{sid}/issues/{iid}/fields')
    def fields(sid:str,iid:str,body:ManualFields):
        s=get(sid);check(s,body.version)
        issue=next((i for i in s.issues if i.id==iid),None)
        if not issue:raise HTTPException(404,'Issue not found')
        for field in ('category','location','time_reference'):
            value=getattr(body,field)
            if field!='category':value=value.strip() or None
            previous=getattr(issue,field)
            if previous!=value:
                issue.revisions.append(Revision(field=field,before=previous,after=value,evidence='Explicit citizen field review'))
                setattr(issue,field,value)
        issue.confirmed=False;issue.version+=1
        s.turns.append({'text':'Fields reviewed by citizen','source':'explicit_field_review','issue_id':iid,'fields':body.model_dump(exclude={'version'})})
        s.prompts=[f'{i.category.title()}: please provide '+', '.join(i.missing)+'.' for i in s.issues if i.missing]
        s.version+=1;save(s,body.version);return s.view()
    @app.get('/api/diagnostics')
    def diagnostics():return evaluate()
    static=Path(__file__).parent/'static'
    app.mount('/static',StaticFiles(directory=static),name='static')
    @app.get('/')
    def index():return FileResponse(static/'index.html')
    return app

class Version(Strict):
    version:int=Field(ge=0)
class Turn(Version):
    text:str=Field(min_length=1,max_length=8000,pattern=r'\S')
    target_id:str|None=None
class ManualFields(Version):
    category:Literal['water','streetlight','drainage','garbage','unknown']
    location:str=Field(max_length=300)
    time_reference:str=Field(max_length=200)
class Review(Version):
    action:Literal['confirm','revoke','clarify']
app=create_app()
