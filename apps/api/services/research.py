"""Persistent local research records and safe document retrieval."""
from __future__ import annotations
import json, re, uuid
from pathlib import Path
from threading import Lock
from datetime import datetime, timezone

ROOT=Path(__file__).parents[1]; STORE=ROOT/'data'/'research.json'; UPLOADS=ROOT/'data'/'uploads'; LOCK=Lock()
def _blank(): return {'sessions':{},'documents':{},'reports':{}}
def read():
 with LOCK:
  if not STORE.exists(): return _blank()
  try:return {**_blank(),**json.loads(STORE.read_text(encoding='utf8'))}
  except (OSError,json.JSONDecodeError):return _blank()
def write(d):
 with LOCK:
  STORE.parent.mkdir(exist_ok=True);STORE.write_text(json.dumps(d,indent=2),encoding='utf8');return d
def now():return datetime.now(timezone.utc).isoformat()
def session(title='Untitled research'):
 d=read(); ident=str(uuid.uuid4()); d['sessions'][ident]={'id':ident,'title':title[:120],'created_at':now(),'updated_at':now(),'messages':[],'documents':[],'experiments':[]};write(d);return d['sessions'][ident]
def sessions(query=''):
 d=read(); q=query.lower();return [x for x in d['sessions'].values() if q in x['title'].lower()]
def get(ident):return read()['sessions'].get(ident)
def update(ident,body):
 d=read(); s=d['sessions'].get(ident)
 if not s:return None
 if 'title'in body:s['title']=str(body['title'])[:120]
 s['updated_at']=now();write(d);return s
def delete(ident):
 d=read()
 if ident not in d['sessions']:return False
 del d['sessions'][ident];write(d);return True
def message(ident,role,content,sources=None):
 d=read();s=d['sessions'].get(ident)
 if not s:return None
 item={'id':str(uuid.uuid4()),'role':role,'content':content,'created_at':now(),'sources':sources or []};s['messages'].append(item);s['updated_at']=now();write(d);return item
def chunks(text,size=1100):
 text=re.sub(r'\s+',' ',text).strip();return [text[i:i+size] for i in range(0,len(text),size) if text[i:i+size].strip()]
def add_document(filename,content,mime):
 d=read();ident=str(uuid.uuid4());d['documents'][ident]={'id':ident,'filename':filename,'mime_type':mime,'text':content,'chunks':chunks(content),'created_at':now()};write(d);return d['documents'][ident]
def retrieve(ids,query,limit=4):
 d=read(); words=set(re.findall(r'[a-zA-Z]{3,}',query.lower())); scored=[]
 for did in ids:
  doc=d['documents'].get(did)
  if not doc:continue
  for n,chunk in enumerate(doc['chunks']):
   score=sum(w in chunk.lower() for w in words)
   if score:scored.append((score,{'document_id':did,'filename':doc['filename'],'section':n+1,'text':chunk}))
 return [x[1] for x in sorted(scored,key=lambda x:x[0],reverse=True)[:limit]]
