export type Config={altitude_km:number;inclination_deg:number;velocity_kms:number;duration_s:number;time_step_s:number};
export type Result={metrics:Record<string,number|null>;series:Record<string,number[]>;validation:Record<string,number>;initial_state:unknown;final_state:unknown;frame:string};
const base=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000';
async function req(path:string, init?:RequestInit){const r=await fetch(base+path,{headers:{'Content-Type':'application/json'},...init});if(!r.ok)throw new Error((await r.json().catch(()=>({detail:r.statusText}))).detail||'API request failed');return r.json()}
export async function simulate(config:Config){const s=await req('/api/v1/simulations',{method:'POST',body:JSON.stringify(config)});return req(`/api/v1/simulations/${s.id}/run`,{method:'POST'})}
export const saveExperiment=(x:unknown)=>req('/api/v1/experiments',{method:'POST',body:JSON.stringify(x)});
export const listExperiments=()=>req('/api/v1/experiments');
export const ask=(message:string,result:Result|null)=>req('/api/v1/agent/chat',{method:'POST',body:JSON.stringify({message,result})});
export const agentHealth=()=>req('/api/v1/agent/health');
export async function streamAsk(message:string,result:Result|null,history:{role:string;text:string}[],onToken:(token:string)=>void,signal?:AbortSignal){const response=await fetch(base+'/api/v1/agent/chat/stream',{method:'POST',headers:{'Content-Type':'application/json','Accept':'text/event-stream'},body:JSON.stringify({message,result,history}),signal});if(!response.ok)throw new Error((await response.json().catch(()=>({detail:'Assistant request failed'}))).detail||'Assistant request failed');const reader=response.body?.getReader();if(!reader)throw new Error('Streaming is unavailable in this browser.');const decoder=new TextDecoder();let buffer='';while(true){const {done,value}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});const events=buffer.split('\n\n');buffer=events.pop()||'';for(const event of events){const data=event.split('\n').find(x=>x.startsWith('data: '))?.slice(6);if(!data||data==='[DONE]')continue;const parsed=JSON.parse(data);if(parsed.error)throw new Error(parsed.error);if(parsed.token)onToken(parsed.token)}}}
export const learnPaths=()=>req('/api/v1/learn/paths');
export const lesson=(id:string)=>req('/api/v1/learn/lessons/'+id);
export const learnProgress=(body:unknown)=>req('/api/v1/learn/progress',{method:'PUT',body:JSON.stringify(body)});
export const toggleBookmark=(id:string)=>req('/api/v1/learn/bookmarks/'+id,{method:'POST'});
export const saveLessonNote=(id:string,text:string)=>req('/api/v1/learn/notes/'+id,{method:'PUT',body:JSON.stringify({text})});
export const submitQuiz=(id:string,answer:number)=>req('/api/v1/learn/quiz/'+id,{method:'POST',body:JSON.stringify({answer})});
export const orbitalVelocity=(altitude:number)=>req('/api/v1/learn/orbital-velocity?altitude_km='+altitude);
export const askTutor=(lesson_id:string,message:string)=>req('/api/v1/learn/agent/chat',{method:'POST',body:JSON.stringify({lesson_id,message})});
export const researchStatus=()=>req('/api/v1/research/provider-status');
export const researchSessions=(q='')=>req('/api/v1/research/sessions?q='+encodeURIComponent(q));
export const newResearchSession=(title:string)=>req('/api/v1/research/sessions',{method:'POST',body:JSON.stringify({title})});
export const getResearchSession=(id:string)=>req('/api/v1/research/sessions/'+id);
export const renameResearchSession=(id:string,title:string)=>req('/api/v1/research/sessions/'+id,{method:'PUT',body:JSON.stringify({title})});
export const deleteResearchSession=(id:string)=>req('/api/v1/research/sessions/'+id,{method:'DELETE'});
export const researchChat=(id:string,message:string)=>req('/api/v1/research/sessions/'+id+'/chat',{method:'POST',body:JSON.stringify({message})});
export const uploadResearchDocument=async(id:string,file:File)=>{const fd=new FormData();fd.append('file',file);const r=await fetch(base+'/api/v1/research/sessions/'+id+'/documents',{method:'POST',body:fd});if(!r.ok)throw new Error((await r.json()).detail||'Upload failed');return r.json()};
export const researchReport=(id:string,question:string)=>req('/api/v1/research/sessions/'+id+'/reports',{method:'POST',body:JSON.stringify({question})});
