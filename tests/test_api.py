import io
import asyncio
import wave
import pytest
import httpx
from fastapi.testclient import TestClient
from app.main import create_app
from app.stt import GnaniPrisma,STTError,validate_audio

def wav(seconds=1):
    b=io.BytesIO()
    with wave.open(b,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\x00\x00'*int(16000*seconds))
    return b.getvalue()
@pytest.fixture
def client(tmp_path):return TestClient(create_app(str(tmp_path/'api.db')))
def new(c):return c.post('/api/sessions').json()
def turn(c,s,text):return c.post(f"/api/sessions/{s['id']}/turns",json={'version':s['version'],'text':text}).json()
def review(c,s,action='confirm'):
    return c.post(f"/api/sessions/{s['id']}/issues/{s['issues'][0]['id']}/review",json={'version':s['version'],'action':action})
def test_confirmation_gate(client):
    s=turn(client,new(client),'Water since yesterday')
    assert review(client,s).status_code==422
    s=turn(client,s,'at house 24');s=review(client,s).json()
    assert s['issues'][0]['status']=='confirmed'
    assert client.get('/api/sessions/'+s['id']).json()['issues'][0]['confirmed']
    s=turn(client,s,'actually house 42');assert not s['issues'][0]['confirmed']
def test_stale_confirmation(client):
    s=turn(client,new(client),'Water at house 24');turn(client,s,'actually house 42')
    assert review(client,s).status_code==409

def test_contradictory_gate(client):
    s=turn(client,new(client),'Water at house 24');s=turn(client,s,'confirm but do not confirm')
    assert review(client,s).status_code==422
    s=review(client,s,'clarify').json();assert review(client,s).json()['issues'][0]['confirmed']

def test_no_source_or_confirmation_injection(client):
    s=new(client)
    r=client.post(f"/api/sessions/{s['id']}/turns",json={'version':0,'text':'water','source':'gnani_live','confirmed':True})
    assert r.status_code==422

def test_missing_and_invalid(client):
    assert client.get('/api/sessions/not-found').status_code==404
    s=new(client)
    assert client.post(f"/api/sessions/{s['id']}/turns",json={'version':0,'text':'   '}).status_code==422

def test_audio_missing_key(client,monkeypatch):
    monkeypatch.delenv('GNANI_API_KEY',raising=False);s=new(client)
    r=client.post(f"/api/sessions/{s['id']}/audio",data={'version':0,'authorized':'true'},files={'audio_file':('x.wav',wav(),'audio/wav')})
    assert r.status_code==503
    assert not client.get('/api/sessions/'+s['id']).json()['turns']

def test_audio_authorization(client):
    s=new(client);r=client.post(f"/api/sessions/{s['id']}/audio",data={'version':0,'authorized':'false'},files={'audio_file':('x.wav',wav())})
    assert r.status_code==422

@pytest.mark.parametrize('audio,name',[(b'','x.wav'),(b'junk','x.wav'),(wav(),'x.exe'),(wav(31),'x.wav'),(wav(.01),'x.wav'),(b'x'*(10*1024*1024+1),'x.wav')])
def test_audio_validation(audio,name):
    with pytest.raises(STTError):validate_audio(audio,name)

def test_valid_wav():validate_audio(wav(),'x.wav')

def fake_client(monkeypatch,response=None,error=None,capture=None):
    class Client:
        def __init__(self,**kw):assert isinstance(kw['timeout'],httpx.Timeout)
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def post(self,url,**kw):
            if capture is not None:capture.update({'url':url,**kw})
            if error:raise error
            return response
    monkeypatch.setenv('GNANI_API_KEY','synthetic-test-key');monkeypatch.setattr(httpx,'AsyncClient',Client)

def test_documented_contract_mocked(monkeypatch):
    capture={};fake_client(monkeypatch,httpx.Response(200,json={'success':True,'transcript':'Water at house 24','model':'prisma-v3.0','request_id':'synthetic'}),capture=capture)
    result=asyncio.run(GnaniPrisma().transcribe(wav(),'x.wav'))
    assert capture['url']=='https://api.vachana.ai/stt/v3'
    assert capture['data']=={'model':'prisma-v3.0','language_code':'kn-IN,en-IN','format':'transliterate'}
    assert capture['headers']['X-API-Key-ID']=='synthetic-test-key'
    assert 'audio_file' in capture['files'] and result['source']=='gnani_live'

@pytest.mark.parametrize('response',[httpx.Response(401),httpx.Response(429),httpx.Response(504),httpx.Response(200,text='bad'),httpx.Response(200,json={'success':True,'transcript':'x','model':'prisma-v2.5'}),httpx.Response(200,json={'success':True,'transcript':'x','truncated':True}),httpx.Response(200,json={'success':False}),httpx.Response(200,json=[])])
def test_upstream_failure_mocked(monkeypatch,response):
    fake_client(monkeypatch,response)
    with pytest.raises(STTError):asyncio.run(GnaniPrisma().transcribe(wav(),'x.wav'))

def test_timeout_mocked(monkeypatch):
    fake_client(monkeypatch,error=httpx.ReadTimeout('synthetic'))
    with pytest.raises(STTError):asyncio.run(GnaniPrisma().transcribe(wav(),'x.wav'))

def test_empty_speech_mocked(monkeypatch):
    fake_client(monkeypatch,httpx.Response(200,json={'success':True,'transcript':''}))
    assert asyncio.run(GnaniPrisma().transcribe(wav(),'x.wav'))['transcript']==''

def test_ui_and_diagnostics(client):
    assert client.get('/').status_code==200
    assert client.get('/static/app.js').status_code==200
    assert client.get('/api/diagnostics').json()['synthetic'] is True

def test_manual_review_arbitrary_location(client):
    s=turn(client,new(client),'Water at house 24');s=review(client,s).json()
    r=client.post(f"/api/sessions/{s['id']}/issues/{s['issues'][0]['id']}/fields",json={'version':s['version'],'category':'water','location':'24, 5th Cross, Indiranagar, Bengaluru','time_reference':'since last night'})
    assert r.status_code==200
    s=r.json();assert not s['issues'][0]['confirmed']
    assert s['issues'][0]['location']=='24, 5th Cross, Indiranagar, Bengaluru'
    assert s['issues'][0]['revisions'][-1]['evidence']=='Explicit citizen field review'
    assert review(client,s).json()['issues'][0]['confirmed']

def test_spoken_house_correction_requires_explicit_confirmation(client):
    transcript='There is no water at house number forty-two. Sorry. Not forty-two, house number twenty-four. The problem started on Monday.'
    s=turn(client,new(client),transcript)
    i=s['issues'][0]
    assert i['location']=='House 24' and i['status']=='awaiting_confirmation'
    assert not i['confirmed'] and s['turns'][0]['text']==transcript
    assert any(r['before']=='House 42' and r['after']=='House 24' for r in i['revisions'])
    assert review(client,s).json()['issues'][0]['status']=='confirmed'
