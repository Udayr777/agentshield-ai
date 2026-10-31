// Original synthesized soundtrack: no downloaded songs or external audio service.
export function soundtrack(volume:number){
 const context=new AudioContext(),destination=context.createMediaStreamDestination(),master=context.createGain();master.gain.value=volume;master.connect(context.destination);master.connect(destination);
 const start=context.currentTime+.06,beat=60/112,notes=[293.66,369.99,440,587.33,440,369.99,329.63,440];
 function tone(freq:number,at:number,duration:number,gain:number,type:OscillatorType='sine'){
  const oscillator=context.createOscillator(),envelope=context.createGain();oscillator.type=type;oscillator.frequency.setValueAtTime(freq,at);envelope.gain.setValueAtTime(0,at);envelope.gain.linearRampToValueAtTime(gain,at+.015);envelope.gain.exponentialRampToValueAtTime(.0001,at+duration);oscillator.connect(envelope);envelope.connect(master);oscillator.start(at);oscillator.stop(at+duration+.01);
 }
 for(let step=0;step*beat/2<17.7;step++){
  const at=start+step*beat/2;tone(notes[step%notes.length],at,.23,.13,'triangle');
  if(step%4===0){tone(73.42,at,.42,.3);tone(110,at,.12,.18)}
  if(step%2===1)tone(1760,at,.035,.035);
 }
 master.gain.setValueAtTime(volume,start+16.8);master.gain.linearRampToValueAtTime(0,start+17.9);
 void context.resume();return {context,stream:destination.stream};
}

type Region={id:string;box:{x:number;y:number;w:number;h:number}};
const names=['See the evidence','Understand the signal','Choose your next step'];
function rounded(ctx:CanvasRenderingContext2D,x:number,y:number,w:number,h:number,r:number,color:string){ctx.fillStyle=color;ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fill()}
function wrap(ctx:CanvasRenderingContext2D,text:string,x:number,y:number,width:number,lineHeight:number){let line='';for(const word of text.split(/\s+/)){const next=line?line+' '+word:word;if(ctx.measureText(next).width>width&&line){ctx.fillText(line,x,y);y+=lineHeight;line=word}else line=next}ctx.fillText(line,x,y)}
export function drawBrief(canvas:HTMLCanvasElement,image:HTMLImageElement|null,time:number,playing:boolean,caption:string,ids:string[],findings:Region[],music:boolean){
 const ctx=canvas.getContext('2d');if(!ctx)return;
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches,t=reduced?0:time,scene=Math.min(2,Math.floor(time/6)),phase=(time%6)/6;
 const bg=ctx.createLinearGradient(0,0,960,540);bg.addColorStop(0,'#e4f7ff');bg.addColorStop(.55,'#f2f7ff');bg.addColorStop(1,'#e8e3ff');ctx.fillStyle=bg;ctx.fillRect(0,0,960,540);
 for(let i=0;i<24;i++){const x=(i*137+Math.sin(t*.4+i)*22)%960,y=(i*89+Math.cos(t*.5+i)*18)%540;ctx.fillStyle=i%2?'#8ba8ef22':'#2eb8c522';ctx.beginPath();ctx.arc(x,y,3+i%4,0,Math.PI*2);ctx.fill()}
 rounded(ctx,28,24,904,68,20,'#ffffffdd');ctx.fillStyle='#123c59';ctx.font='bold 21px sans-serif';ctx.fillText('AgentShield AI',50,54);ctx.font='13px sans-serif';ctx.fillStyle='#476b82';ctx.fillText('YOUR INVOICE · A CLEARER NEXT STEP',50,76);
 const sx=889,sy=57;ctx.strokeStyle='#168d9c';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(sx,sy-20);ctx.lineTo(sx+17,sy-13);ctx.lineTo(sx+13,sy+9);ctx.lineTo(sx,sy+21);ctx.lineTo(sx-13,sy+9);ctx.lineTo(sx-17,sy-13);ctx.closePath();ctx.stroke();
 rounded(ctx,28,109,316,349,18,'#fff');ctx.save();ctx.beginPath();ctx.roundRect(39,120,294,327,12);ctx.clip();
 if(image){const scale=Math.min(294/image.width,327/image.height),w=image.width*scale,h=image.height*scale,x=39+(294-w)/2,y=120;ctx.drawImage(image,x,y,w,h);for(const f of findings){if(ids.length&&!ids.includes(f.id))continue;const b=f.box;ctx.strokeStyle='#cf7618';ctx.lineWidth=2;ctx.fillStyle=`rgba(255,169,50,${.13+(playing&&!reduced?Math.sin(t*4)*.05:0)})`;ctx.fillRect(x+b.x*w,y+b.y*h,b.w*w,b.h*h);ctx.strokeRect(x+b.x*w,y+b.y*h,b.w*w,b.h*h)}if(playing&&!reduced){const scan=y+h*phase;ctx.strokeStyle='#2498ae88';ctx.beginPath();ctx.moveTo(x,scan);ctx.lineTo(x+w,scan);ctx.stroke()}}
 ctx.restore();
 const entrance=reduced?0:Math.max(0,1-Math.min(1,phase*7))*20;ctx.save();ctx.translate(entrance,0);ctx.fillStyle='#247a8d';ctx.font='bold 14px sans-serif';ctx.fillText(`CHAPTER 0${scene+1} / 03`,378,145);ctx.fillStyle='#153c58';ctx.font='bold 21px sans-serif';ctx.fillText(names[scene],378,179);ctx.font='bold 31px sans-serif';wrap(ctx,caption,378,233,520,41);ctx.font='14px sans-serif';ctx.fillStyle='#476578';wrap(ctx,`Evidence: ${ids.join(', ')||'general guidance'}`,378,375,510,22);ctx.restore();
 rounded(ctx,370,403,548,55,12,'#fff9');ctx.fillStyle='#4b6075';ctx.font='13px sans-serif';wrap(ctx,'First-page visibility only. Findings are not proof of fraud or payment approval.',385,425,510,18);
 for(let i=0;i<3;i++){rounded(ctx,28+i*306,477,294,5,3,'#c4d3e3');const progress=Math.max(0,Math.min(1,(time-i*6)/6));if(progress)rounded(ctx,28+i*306,477,294*progress,5,3,i===2?'#7656bb':'#168f9b')}
 ctx.font='12px sans-serif';ctx.fillStyle='#4f677d';ctx.fillText('MUSE SCRIPT / AGENTSHIELD MOTION',28,513);ctx.fillText(`${Math.floor(time).toString().padStart(2,'0')} / 18s`,837,513);
 if(music){for(let i=0;i<12;i++){const height=playing&&!reduced?5+Math.abs(Math.sin(t*6+i*.6))*13:4;rounded(ctx,645+i*8,510-height,4,height,2,'#4d92a6')}ctx.font='10px sans-serif';ctx.fillText('SOUNDTRACK',745,513)}
}
