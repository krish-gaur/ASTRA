"""Single server-only, OpenAI-compatible provider adapter for ASTRA."""
from __future__ import annotations
import json, logging, os, re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from dotenv import load_dotenv

ROOT=Path(__file__).parents[2]
load_dotenv(ROOT/'.env',override=False); load_dotenv(ROOT/'.env.local',override=False)
LOG=logging.getLogger('astra.ai')
class AIError(Exception):
 def __init__(self,message,status=None,code=None,request_id=None):
  super().__init__(message);self.status=status;self.code=code;self.request_id=request_id
def _config():
 base=os.getenv('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
 return {'key':os.getenv('OPENAI_API_KEY'),'base':base,'model':os.getenv('OPENAI_MODEL','gpt-4o-mini'),'provider':os.getenv('AI_PROVIDER','openai-compatible')}
def settings():
 c=_config();return {'configured':bool(c['key']),'provider':c['provider'],'model':c['model'],'endpoint_host':urlparse(c['base']).netloc,'base_url_configured':bool(os.getenv('OPENAI_BASE_URL'))}
def configured():return bool(_config()['key'])
def _safe_text(value):
 # Never echo credentials even if an upstream proxy includes them in its response.
 return re.sub(r'(sk-|Bearer\s+)[A-Za-z0-9_\-]{8,}',r'\1[redacted]',str(value))[:700]
def _provider_error(error:HTTPError):
 raw=error.read().decode('utf8','replace')[:4000]
 code=None;message='Provider request failed.'
 try:
  parsed=json.loads(raw); detail=parsed.get('error',parsed); code=detail.get('code') or detail.get('type'); message=detail.get('message') or message
 except (ValueError,AttributeError):message=raw or message
 request_id=error.headers.get('x-request-id') or error.headers.get('request-id')
 message=_safe_text(message)
 category={400:'Invalid provider request or unsupported parameter.',401:'Authentication failed with the provider.',403:'Provider access was denied.',404:'The configured model or endpoint was not found.',429:'Provider rate limit or quota exceeded.'}.get(error.code,'Provider server error.' if error.code>=500 else 'Provider request failed.')
 LOG.warning('ai_provider_error provider=%s status=%s code=%s host=%s model=%s request_id=%s message=%s',_config()['provider'],error.code,code,urlparse(_config()['base']).netloc,_config()['model'],request_id,_safe_text(message))
 return AIError(category,status=error.code,code=code,request_id=request_id)
def _request(messages,stream=False,temperature=.25):
 c=_config()
 if not c['key']:raise AIError('No server-side AI key is loaded.',code='missing_key')
 payload={'model':c['model'],'messages':messages,'temperature':temperature}
 if stream:payload['stream']=True
 return Request(c['base']+'/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+c['key'],'Content-Type':'application/json','Accept':'text/event-stream' if stream else 'application/json'},method='POST')
def chat(messages,temperature=.25):
 try:
  with urlopen(_request(messages,False,temperature),timeout=45) as response:data=json.loads(response.read().decode())
 except HTTPError as e:raise _provider_error(e)
 except (URLError,TimeoutError) as e:
  LOG.warning('ai_provider_network_error host=%s model=%s error=%s',urlparse(_config()['base']).netloc,_config()['model'],type(e).__name__);raise AIError('The AI provider timed out or is unavailable.',code='network_error')
 try:return data['choices'][0]['message']['content']
 except (KeyError,IndexError,TypeError):raise AIError('The AI provider returned an invalid response.',code='invalid_response')
def stream(messages,temperature=.25):
 try:
  with urlopen(_request(messages,True,temperature),timeout=60) as response:
   for raw in response:
    line=raw.decode('utf8').strip()
    if not line.startswith('data: '):continue
    value=line[6:]
    if value=='[DONE]':return
    try:token=json.loads(value)['choices'][0]['delta'].get('content','')
    except (ValueError,KeyError,IndexError,TypeError):token=''
    if token:yield token
 except HTTPError as e:raise _provider_error(e)
 except (URLError,TimeoutError) as e:raise AIError('The AI provider timed out or is unavailable.',code='network_error')
def diagnostic():
 try: chat([{'role':'user','content':'Reply with exactly: ok'}],temperature=0)
 except AIError as e:return {'status':'error','http_status':e.status,'provider_error_code':e.code,'message':str(e),'request_id':e.request_id,**settings()}
 return {'status':'connected','http_status':200,'provider_error_code':None,'message':'Provider inference succeeded.','request_id':None,**settings()}
