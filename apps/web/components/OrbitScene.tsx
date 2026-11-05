// @ts-nocheck
'use client';
import {Canvas,useFrame,useLoader} from '@react-three/fiber';
import {Line,OrbitControls,Stars} from '@react-three/drei';
import {useMemo,useRef} from 'react';
import * as THREE from 'three';

const textureRoot='https://threejs.org/examples/textures/planets/';
function Earth(){
 const earth=useRef<THREE.Group>(null!), clouds=useRef<THREE.Mesh>(null!);
 const [map,normal,specular,cloudMap]=useLoader(THREE.TextureLoader,[textureRoot+'earth_atmos_2048.jpg',textureRoot+'earth_normal_2048.jpg',textureRoot+'earth_specular_2048.jpg',textureRoot+'earth_clouds_1024.png']);
 useFrame((_,delta)=>{earth.current.rotation.y+=delta*.018;clouds.current.rotation.y+=delta*.026});
 return <group ref={earth}><mesh><sphereGeometry args={[2.2,96,96]}/><meshPhongMaterial map={map} normalMap={normal} specularMap={specular} specular={new THREE.Color('#2f6f9f')} shininess={12}/></mesh><mesh ref={clouds} scale={1.006}><sphereGeometry args={[2.2,72,72]}/><meshPhongMaterial map={cloudMap} transparent opacity={.36} depthWrite={false}/></mesh><mesh scale={1.035}><sphereGeometry args={[2.2,72,72]}/><shaderMaterial transparent side={THREE.BackSide} blending={THREE.AdditiveBlending} depthWrite={false} vertexShader={'varying vec3 vNormal; void main(){vNormal=normalize(normalMatrix*normal);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}' } fragmentShader={'varying vec3 vNormal; void main(){float rim=pow(0.62-dot(vNormal,vec3(0.,0.,1.)),3.0);gl_FragColor=vec4(0.16,0.48,1.0,rim*.34);}'}/></mesh></group>
}
function Satellite({points,progress}:{points:number[][];progress:number}){
 const group=useRef<THREE.Group>(null!);const ix=Math.min(points.length-1,Math.floor(progress*(points.length-1)));const p=points[ix]||[4,0,0];const next=points[Math.min(ix+1,points.length-1)]||p;const velocity=useMemo(()=>new THREE.Vector3(next[0]-p[0],next[1]-p[1],next[2]-p[2]).normalize(),[p,next]);
 useFrame(()=>{if(group.current){group.current.position.set(...p);group.current.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1),velocity)}});
 return <group ref={group}><mesh castShadow><boxGeometry args={[.19,.11,.25]}/><meshStandardMaterial color="#d8e6ef" metalness={.75} roughness={.32}/></mesh><mesh position={[0,0,.16]} rotation={[Math.PI/2,0,0]}><cylinderGeometry args={[.035,.035,.11,16]}/><meshStandardMaterial color="#d6b35e" metalness={.8}/></mesh><mesh position={[.43,0,0]}><boxGeometry args={[.66,.025,.2]}/><meshStandardMaterial color="#1a3968" metalness={.6} roughness={.25}/></mesh><mesh position={[-.43,0,0]}><boxGeometry args={[.66,.025,.2]}/><meshStandardMaterial color="#1a3968" metalness={.6} roughness={.25}/></mesh><arrowHelper args={[velocity,new THREE.Vector3(0,0,0),.55,0x61d5ff,.1,.06]}/></group>
}
function Scene({trajectory,progress}:{trajectory:number[][];progress:number}){const line=useMemo(()=>trajectory.map(p=>new THREE.Vector3(...p)),[trajectory]);return <><color attach="background" args={['#020610']}/><ambientLight intensity={.17}/><directionalLight position={[7,4,5]} intensity={2.8} color="#f7e9c7" castShadow/><pointLight position={[-7,-2,-4]} intensity={.12} color="#5c83ff"/><Stars radius={65} depth={45} count={3000} factor={1.6} saturation={0}/><Earth/>{line.length>1&&<Line points={line} color="#a58aff" lineWidth={1.15} transparent opacity={.78}/>}<Satellite points={trajectory} progress={progress}/><gridHelper args={[14,14,0x18375a,0x0c1b31]} rotation={[Math.PI/2,0,0]}/><axesHelper args={[3.1]}/><OrbitControls enableDamping dampingFactor={.08} minDistance={4.4} maxDistance={16} target={[0,0,0]}/></>}
export default function OrbitScene({trajectory,progress}:{trajectory:number[][];progress:number}){return <Canvas shadows dpr={[1,1.75]} camera={{position:[0,4.2,9.4],fov:40}} gl={{antialias:true,powerPreference:'high-performance'}}><Scene trajectory={trajectory} progress={progress}/></Canvas>}
