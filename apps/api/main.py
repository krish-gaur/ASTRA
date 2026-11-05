from __future__ import annotations
import json
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from scientific.orbit import propagate, OrbitInputError
from services import learning
from services import research, ai
from pypdf import PdfReader
from io import BytesIO
from uuid import uuid4

app = FastAPI(title='ASTRA Orbit Lab API', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3000'], allow_methods=['*'], allow_headers=['*'])
SIMS, EXPERIMENTS = {}, {}
class Config(BaseModel):
    altitude_km: float = Field(400, ge=100, le=100000)
    inclination_deg: float = Field(51.6, ge=0, le=180)
    velocity_kms: float = Field(7.668, ge=1, le=20)
    duration_s: float = Field(5400, ge=1, le=604800)
    time_step_s: float = Field(20, ge=1, le=3600)
class Experiment(BaseModel): name: str; notes: str = ''; config: Config; result: Optional[dict] = None
@app.get('/health')
def health(): return {'status':'ok'}
@app.post('/api/v1/simulations')
def create_simulation(config: Config):
    ident=str(uuid4()); SIMS[ident]={'id':ident,'config':config.model_dump(),'status':'ready'}; return SIMS[ident]
@app.post('/api/v1/simulations/{ident}/run')
def run_simulation(ident: str):
    if ident not in SIMS: raise HTTPException(404,'Simulation not found')
    try: SIMS[ident].update(status='completed', result=propagate(SIMS[ident]['config']))
    except (OrbitInputError, RuntimeError) as exc: raise HTTPException(422, str(exc))
    return SIMS[ident]
@app.get('/api/v1/simulations/{ident}')
def get_simulation(ident: str):
    if ident not in SIMS: raise HTTPException(404,'Simulation not found')
    return SIMS[ident]
@app.get('/api/v1/simulations/{ident}/results')
def results(ident: str):
    if ident not in SIMS or 'result' not in SIMS[ident]: raise HTTPException(404,'Results not found')
    return SIMS[ident]['result']
@app.get('/api/v1/experiments')
def list_experiments(): return list(EXPERIMENTS.values())
@app.post('/api/v1/experiments')
def save_experiment(exp: Experiment):
    ident=str(uuid4()); EXPERIMENTS[ident]={'id':ident, **exp.model_dump()}; return EXPERIMENTS[ident]
@app.get('/api/v1/experiments/{ident}')
def get_experiment(ident: str):
    if ident not in EXPERIMENTS: raise HTTPException(404,'Experiment not found')
    return EXPERIMENTS[ident]
@app.put('/api/v1/experiments/{ident}')
def update_experiment(ident: str, exp: Experiment):
    if ident not in EXPERIMENTS: raise HTTPException(404,'Experiment not found')
    EXPERIMENTS[ident]={'id':ident, **exp.model_dump()}; return EXPERIMENTS[ident]
@app.delete('/api/v1/experiments/{ident}')
def delete_experiment(ident: str):
    if ident not in EXPERIMENTS: raise HTTPException(404,'Experiment not found')
    del EXPERIMENTS[ident]; return {'deleted':True}
def orbit_messages(payload:dict):
    q=str(payload.get('message','')).strip(); result=payload.get('result') or {}; metrics=result.get('metrics',{})
    if not q or len(q)>8000:raise HTTPException(422,'Message must be between 1 and 8,000 characters.')
    # Send only generated scientific output, never frontend secrets or unrelated state.
    fields=('orbital_period_s','current_altitude_km','orbital_velocity_kms','escape_velocity_kms','eccentricity','specific_energy_jkg','angular_momentum_m2s','semi_major_axis_km','simulation_duration_s')
    context={k:metrics[k] for k in fields if k in metrics}
    history=payload.get('history',[])[-8:]
    safe_history=[{'role':x.get('role'),'content':str(x.get('text',''))[:4000]} for x in history if x.get('role') in ('user','assistant')]
    system='You are ASTRA, a concise aerospace simulation copilot. Explain science rigorously. The simulation context below is authoritative; never invent numerical metrics. State when no simulation has been run. Use Markdown and LaTex-style equations where helpful.\nSimulation context: '+str(context)
    return [{'role':'system','content':system},*safe_history,{'role':'user','content':q}]
@app.get('/api/v1/agent/health')
def agent_health():
    """A genuine provider probe; connected is only returned after inference succeeds."""
    return ai.diagnostic()
@app.post('/api/v1/agent/chat')
def chat(payload: dict):
    try:return {'message':ai.chat(orbit_messages(payload)),'provider':'openai-compatible'}
    except ai.AIError as e:raise HTTPException(503,str(e))
@app.post('/api/v1/agent/chat/stream')
def chat_stream(payload:dict):
    messages=orbit_messages(payload)
    def events():
      try:
       for token in ai.stream(messages): yield 'data: '+json.dumps({'token':token})+'\n\n'
       yield 'data: [DONE]\n\n'
      except ai.AIError as e:yield 'data: '+json.dumps({'error':str(e)})+'\n\n'
    return StreamingResponse(events(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

@app.get('/api/v1/learn/paths')
def learning_paths(): return learning.progress()
@app.get('/api/v1/learn/lessons/{ident}')
def learning_lesson(ident: str):
    item=learning.lesson(ident)
    if not item: raise HTTPException(404,'Lesson not found')
    return item
@app.get('/api/v1/learn/progress')
def learning_progress(): return learning.progress()
@app.put('/api/v1/learn/progress')
def update_learning_progress(payload: dict):
    state=learning.read(); state.update({k:v for k,v in payload.items() if k in {'current_lesson','seconds'}})
    if 'completed_lesson' in payload and payload['completed_lesson'] not in state['completed']: state['completed'].append(payload['completed_lesson'])
    return learning.write(state)
@app.post('/api/v1/learn/bookmarks/{ident}')
def bookmark(ident: str):
    if not learning.lesson(ident): raise HTTPException(404,'Lesson not found')
    state=learning.read(); state['bookmarks'] = [x for x in state['bookmarks'] if x != ident] if ident in state['bookmarks'] else state['bookmarks']+[ident]
    learning.write(state); return {'bookmarked':ident in state['bookmarks'],'bookmarks':state['bookmarks']}
@app.put('/api/v1/learn/notes/{ident}')
def note(ident: str,payload:dict):
    state=learning.read(); state['notes'][ident]=str(payload.get('text',''))[:10000]; learning.write(state); return {'text':state['notes'][ident]}
@app.post('/api/v1/learn/quiz/{ident}')
def quiz(ident: str,payload:dict):
    item=learning.lesson(ident)
    if not item or 'quiz' not in item: raise HTTPException(404,'Quiz not found')
    answer=payload.get('answer'); correct=answer==item['quiz']['answer']; state=learning.read(); state['attempts'][ident]={'answer':answer,'correct':correct}; learning.write(state)
    return {'correct':correct,'explanation':item['quiz']['explanation'] if correct else 'Try relating the equation to radius before checking again.'}
@app.get('/api/v1/learn/orbital-velocity')
def orbital_velocity(altitude_km:float=400):
    try:return learning.velocity(altitude_km)
    except ValueError as e: raise HTTPException(422,str(e))
@app.post('/api/v1/learn/agent/chat')
def learning_chat(payload:dict):
    item=learning.lesson(payload.get('lesson_id','orbital-velocity')); question=str(payload.get('message',''))
    if not item: raise HTTPException(404,'Lesson not found')
    if 'hint' in question.lower(): text=f"Hint: start with {item.get('equation','the governing relationship')} and identify which quantity changes."
    else: text=f"In {item['title']}: {item['summary']} {item['sections'][0]['body']} This local tutor uses the active lesson context; configure a provider adapter for generative answers."
    return {'message':text,'provider':'local','lesson_id':item['id']}

# Phase 3: Research workspace.  Records are local-user scoped for this no-auth MVP.
@app.get('/api/v1/research/provider-status')
def provider_status(): return ai.settings()
@app.get('/api/v1/research/sessions')
def research_sessions(q:str=''): return research.sessions(q)
@app.post('/api/v1/research/sessions')
def create_research_session(payload:dict): return research.session(str(payload.get('title','Untitled research')))
@app.get('/api/v1/research/sessions/{ident}')
def research_session(ident:str):
 s=research.get(ident)
 if not s: raise HTTPException(404,'Research session not found')
 return s
@app.put('/api/v1/research/sessions/{ident}')
def rename_research_session(ident:str,payload:dict):
 s=research.update(ident,payload)
 if not s: raise HTTPException(404,'Research session not found')
 return s
@app.delete('/api/v1/research/sessions/{ident}')
def delete_research_session(ident:str):
 if not research.delete(ident):raise HTTPException(404,'Research session not found')
 return {'deleted':True}
@app.post('/api/v1/research/sessions/{ident}/documents')
async def upload_research_document(ident:str,file:UploadFile=File(...)):
 s=research.get(ident)
 if not s:raise HTTPException(404,'Research session not found')
 allowed={'application/pdf','text/plain','text/markdown'}
 if file.content_type not in allowed:raise HTTPException(415,'Only PDF, plain text, and Markdown documents are supported.')
 raw=await file.read()
 if not raw or len(raw)>10_000_000:raise HTTPException(422,'Document must be between 1 byte and 10 MB.')
 try:
  text=''.join(page.extract_text() or '' for page in PdfReader(BytesIO(raw)).pages) if file.content_type=='application/pdf' else raw.decode('utf8')
 except Exception:raise HTTPException(422,'The document could not be extracted. Upload a readable PDF or UTF-8 text file.')
 if len(text.strip())<30:raise HTTPException(422,'No usable document text was found.')
 doc=research.add_document(file.filename or 'document',text,file.content_type)
 data=research.read();data['sessions'][ident]['documents'].append(doc['id']);research.write(data)
 return {'id':doc['id'],'filename':doc['filename'],'chunks':len(doc['chunks'])}
@app.post('/api/v1/research/sessions/{ident}/chat')
def research_chat(ident:str,payload:dict):
 s=research.get(ident); question=str(payload.get('message','')).strip()
 if not s:raise HTTPException(404,'Research session not found')
 if not question or len(question)>8000:raise HTTPException(422,'Research question must be between 1 and 8,000 characters.')
 evidence=research.retrieve(s['documents'],question)
 context='\n\n'.join(f"[Source: {x['filename']}, section {x['section']}]\n{x['text']}" for x in evidence)
 system='You are ASTRA Research, a rigorous aerospace research assistant. Distinguish evidence from inference. Do not fabricate citations, numerical simulation outputs, or paper findings. Cite supplied sources as [filename, section N]. If no source is supplied, say this is general scientific knowledge. Use compact Markdown.'
 prompt=question+(f"\n\nRetrieved document evidence:\n{context}" if context else '')
 research.message(ident,'user',question)
 try: answer=ai.chat([{'role':'system','content':system},{'role':'user','content':prompt}])
 except ai.AIError as e:raise HTTPException(503,str(e))
 msg=research.message(ident,'assistant',answer,[{'filename':x['filename'],'section':x['section']} for x in evidence])
 return msg
@app.post('/api/v1/research/sessions/{ident}/reports')
def research_report(ident:str,payload:dict):
 s=research.get(ident)
 if not s:raise HTTPException(404,'Research session not found')
 question=str(payload.get('question') or s['title'])
 evidence=research.retrieve(s['documents'],question)
 prompt='Create a cautious research report in Markdown with exactly: Title, Research question, Background, Methodology, Findings, Supporting evidence, Equations, Limitations, Conclusion, References. Do not assert unsupported claims. Question: '+question+'\nEvidence:\n'+ '\n'.join(x['text'] for x in evidence)
 try:content=ai.chat([{'role':'system','content':'You are an aerospace research report writer. Clearly label uncertainty.'},{'role':'user','content':prompt}])
 except ai.AIError as e:raise HTTPException(503,str(e))
 return {'title':question,'content':content,'sources':[{'filename':x['filename'],'section':x['section']} for x in evidence]}
