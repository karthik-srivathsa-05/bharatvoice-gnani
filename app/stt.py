"""Verified against https://docs.gnani.ai/api/STT/speech-to-text on 2026-11-10."""
import io
import os
from typing import Protocol
from uuid import uuid4
import httpx
import soundfile as sf

class STTError(Exception):
    def __init__(self,message,status=502): self.message=message;self.status=status
class Transcriber(Protocol):
    async def transcribe(self,audio: bytes,filename: str) -> dict: ...

def validate_audio(audio,filename):
    if not filename.lower().endswith(('.wav','.flac','.ogg')):
        raise STTError('MVP accepts WAV, FLAC or OGG only. Recordings are encoded as WAV.',422)
    if not audio or len(audio)>10*1024*1024: raise STTError('Audio must be nonempty and at most 10 MiB.',422)
    try:
        info=sf.info(io.BytesIO(audio))
        if info.format not in ('WAV','FLAC','OGG') or not 0.1<=info.duration<=30 or not 1<=info.channels<=2:
            raise ValueError()
    except Exception:
        raise STTError('Invalid audio: use decodable WAV/FLAC/OGG, mono/stereo, 0.1–30 seconds.',422)

class GnaniPrisma:
    async def transcribe(self,audio,filename):
        validate_audio(audio,filename)
        key=os.getenv('GNANI_API_KEY')
        if not key: raise STTError('Gnani key is not configured. No live API call was made.',503)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(25,connect=5)) as client:
                r=await client.post('https://api.vachana.ai/stt/v3',headers={'X-API-Key-ID':key,'X-API-Request-ID':str(uuid4())},data={'model':'prisma-v3.0','language_code':'kn-IN,en-IN','format':'transliterate'},files={'audio_file':(filename,audio)})
            if r.status_code!=200:
                raise STTError(f'Gnani HTTP {r.status_code}. Check credentials, credit, rate limits or retry later.')
            data=r.json()
            if not isinstance(data,dict): raise STTError('Unexpected Gnani response.')
            if data.get('success') is not True or not isinstance(data.get('transcript'),str): raise STTError('Unexpected Gnani response.')
            if data.get('truncated'): raise STTError('Gnani transcript was truncated. Retry a shorter clip.')
            if data.get('transcript') and data.get('model')!='prisma-v3.0': raise STTError('Gnani did not report the requested Prisma v3.0 model.')
            return {'source':'gnani_live','transcript':data['transcript'],'request_id':data.get('request_id'),'model':data.get('model')}
        except (httpx.TimeoutException,httpx.RequestError) as e: raise STTError('Gnani request timed out or could not connect. No transcript was saved.') from e
        except ValueError as e: raise STTError('Gnani returned invalid JSON.') from e
