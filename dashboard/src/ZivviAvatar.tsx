import React,{useEffect,useRef,useState} from 'react';import './zivvi-avatar.css';
// Full-character pose frames: no separate hand or limb overlay.
export default function ZivviAvatar({alt='Zivvi, your application guide'}:{alt?:string}){
 const[ready,setReady]=useState(false),[frame,setFrame]=useState(0);const timer=useRef<ReturnType<typeof setInterval>|null>(null);
 function stop(){if(timer.current){clearInterval(timer.current);timer.current=null}setFrame(0)}
 useEffect(()=>{let alive=true;const sheet=new Image();sheet.onload=()=>{if(alive)setReady(true)};sheet.src='/zivvi-wave-sheet.png';return()=>{alive=false;sheet.onload=null;if(timer.current)clearInterval(timer.current)}},[]);
 function greet(){if(!ready||window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;stop();const sequence=[0,1,2,3,4,5,2,1,0,1,2,3,4,5,0];let step=0;timer.current=setInterval(()=>{step++;if(step>=sequence.length){stop();return}setFrame(sequence[step])},135)}
 return <span className={'zivvi-avatar'+(ready?' zivvi-poses-ready':'')} tabIndex={0} role="img" aria-label={alt+' - say hello'} onPointerEnter={greet} onPointerLeave={stop} onPointerDown={greet} onFocus={greet} onBlur={stop}><img src="/guide-muse.png" alt=""/>{ready&&<svg className="zivvi-pose" viewBox={`${(frame%3)*512} ${Math.floor(frame/3)*512} 512 512`} preserveAspectRatio="xMidYMid meet" aria-hidden="true"><image href="/zivvi-wave-sheet.png" width="1536" height="1024"/></svg>}<span className="zivvi-hello" aria-hidden="true">Hi! I'm Zivvi.</span></span>
}
