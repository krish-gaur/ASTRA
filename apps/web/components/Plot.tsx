// @ts-nocheck
'use client';
import dynamic from 'next/dynamic';
const Plotly=dynamic(()=>import('react-plotly.js'),{ssr:false});
export default function Plot({x,y,title,color='#9b7cff'}:{x:number[];y:number[];title:string;color?:string}){return <Plotly data={[{x,y,type:'scatter',mode:'lines',line:{color,width:2}}]} layout={{title:{text:title,font:{color:'#dce6ff',size:13}},paper_bgcolor:'#0a1020',plot_bgcolor:'#0a1020',font:{color:'#9dadca'},margin:{l:42,r:12,t:36,b:35},xaxis:{gridcolor:'#1b2943'},yaxis:{gridcolor:'#1b2943'}}} config={{displayModeBar:false}} style={{width:'100%',height:210}} useResizeHandler/>}
