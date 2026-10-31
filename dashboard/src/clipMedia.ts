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
export function drawBrief(canvas:HTMLCanvasElement,image:HTMLImageElement|null,time:number,playing:boolean,caption:string,ids:string[],findings:Region[],music:boolean,museScript=true){
 const ctx=canvas.getContext('2d');if(!ctx)return;
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 const t=reduced?0:time,scene=Math.min(2,Math.floor(time/6)),phase=(time%6)/6;
 const palettes=[['#ff815b','#ffca79','#653dde'],['#b59aff','#ff8ed4','#2d55cf'],['#56e4dd','#a3f19b','#3766d7']];
 const [accent,secondary,deep]=palettes[scene];
 const bg=ctx.createLinearGradient(0,0,960,540);bg.addColorStop(0,'#131d46');bg.addColorStop(.55,deep);bg.addColorStop(1,'#251245');ctx.fillStyle=bg;ctx.fillRect(0,0,960,540);
 // Slow aurora clouds and orbital ribbons: decorative motion, never a security score.
 for(let i=0;i<3;i++){const x=150+i*340+Math.sin(t*.45+i)*65,y=160+Math.cos(t*.4+i)*180;const g=ctx.createRadialGradient(x,y,0,x,y,310);g.addColorStop(0,[accent+'66',secondary+'55','#615bff66'][i]);g.addColorStop(1,'#00000000');ctx.fillStyle=g;ctx.fillRect(0,0,960,540)}
 ctx.save();ctx.translate(740,245);ctx.rotate(t*.13);for(let i=0;i<3;i++){ctx.strokeStyle=[accent+'44',secondary+'33','#ffffff22'][i];ctx.lineWidth=16-i*4;ctx.beginPath();ctx.ellipse(0,0,240+i*35,85+i*35,i*.7,0,Math.PI*2);ctx.stroke()}ctx.restore();
 for(let i=0;i<28;i++){const x=(i*137+Math.sin(t*.5+i)*30+960)%960,y=(i*79+Math.cos(t*.45+i)*23+540)%540;ctx.fillStyle=i%2?secondary+'77':'#ffffff55';ctx.beginPath();ctx.arc(x,y,1.5+i%3,0,Math.PI*2);ctx.fill()}
 ctx.fillStyle='#fff';ctx.font='bold 21px sans-serif';ctx.fillText('AgentShield AI',32,42);ctx.font='12px sans-serif';ctx.fillStyle='#e8e5ff';ctx.fillText('INVOICE STORY / 18 SECONDS',32,65);
 rounded(ctx,752,23,176,34,17,'#ffffff22');ctx.fillStyle='#fff';ctx.font='bold 12px sans-serif';ctx.fillText(['01 / OBSERVE','02 / UNDERSTAND','03 / REVIEW'][scene],770,45);
 const entrance=reduced?1:1-Math.pow(1-Math.min(1,phase*6),3);
 const float=reduced?0:Math.sin(t*1.5)*5;
 ctx.save();ctx.translate(30+(1-entrance)*-50,96+float);ctx.rotate(reduced?0:Math.sin(t*.65)*.012);
 ctx.shadowColor='#080d4566';ctx.shadowBlur=28;rounded(ctx,0,0,300,349,22,'#fff');ctx.shadowBlur=0;
 rounded(ctx,12,12,276,25,10,'#eef2ff');ctx.fillStyle='#3c466c';ctx.font='bold 10px sans-serif';ctx.fillText('YOUR PRIVATE INVOICE / PAGE 1',26,29);
 ctx.save();ctx.beginPath();ctx.roundRect(12,46,276,290,10);ctx.clip();
 if(image){const scale=Math.min(276/image.width,290/image.height),w=image.width*scale,h=image.height*scale,x=12+(276-w)/2,y=46;ctx.drawImage(image,x,y,w,h);
 for(const f of findings){if(ids.length&&!ids.includes(f.id))continue;const b=f.box;ctx.strokeStyle='#c05d14';ctx.lineWidth=2;ctx.fillStyle=`rgba(255,159,40,${.18+(playing&&!reduced?Math.sin(t*3)*.05:0)})`;ctx.fillRect(x+b.x*w,y+b.y*h,b.w*w,b.h*h);ctx.strokeRect(x+b.x*w,y+b.y*h,b.w*w,b.h*h)}
 if(playing&&!reduced){const scan=y+h*phase;const g=ctx.createLinearGradient(0,scan-18,0,scan+2);g.addColorStop(0,'#26b4c900');g.addColorStop(1,'#26b4c977');ctx.fillStyle=g;ctx.fillRect(x,scan-18,w,20);ctx.strokeStyle='#128fa8';ctx.beginPath();ctx.moveTo(x,scan);ctx.lineTo(x+w,scan);ctx.stroke()}}
 ctx.restore();ctx.restore();
 // A floating evidence label carries actual recorded counts, not a fabricated verdict.
 rounded(ctx,170,420+float,180,38,12,accent);ctx.fillStyle='#21203b';ctx.font='bold 12px sans-serif';ctx.fillText(`${findings.length} visibility observation(s)`,183,444+float);
 ctx.save();ctx.translate((1-entrance)*45,0);
 rounded(ctx,366,100,562,330,26,'#ffffff');rounded(ctx,386,119,112,25,12,accent);ctx.fillStyle='#26213a';ctx.font='bold 11px sans-serif';ctx.fillText(['THE EVIDENCE','THE MEANING','YOUR NEXT STEP'][scene],398,136);
 ctx.fillStyle='#596386';ctx.font='bold 16px sans-serif';ctx.fillText(names[scene],388,176);
 ctx.fillStyle='#1c2547';ctx.font='bold 34px sans-serif';
 const words=caption.split(/\s+/);const count=reduced||!playing?words.length:Math.max(1,Math.ceil(words.length*Math.min(1,phase*4)));
 wrap(ctx,words.slice(0,count).join(' '),388,223,510,42);
 rounded(ctx,386,360,520,50,12,'#f0f3fb');ctx.fillStyle='#405378';ctx.font='13px sans-serif';wrap(ctx,`Evidence: ${ids.join(', ')||'general guidance'} / first-page visibility only`,400,382,490,18);
 ctx.restore();
 ctx.fillStyle='#f2ecff';ctx.font='12px sans-serif';ctx.fillText('Observations are not proof of fraud or payment approval.',373,452);
 for(let i=0;i<3;i++){rounded(ctx,32+i*304,481,290,6,3,'#ffffff33');const progress=Math.max(0,Math.min(1,(time-i*6)/6));if(progress)rounded(ctx,32+i*304,481,290*progress,6,3,palettes[i][0])}
 ctx.fillStyle='#f0eaff';ctx.font='11px sans-serif';ctx.fillText(museScript?'MUSE SCRIPT / AGENTSHIELD MOTION':'LOCAL EVIDENCE / AGENTSHIELD MOTION',32,517);ctx.font='bold 13px sans-serif';ctx.fillText(`${Math.floor(time).toString().padStart(2,'0')} / 18s`,844,517);
 if(music){for(let i=0;i<13;i++){const h=playing&&!reduced?4+Math.abs(Math.sin(t*5+i*.65))*15:4;rounded(ctx,648+i*7,516-h,3,h,2,secondary)}ctx.font='9px sans-serif';ctx.fillText('SOUNDTRACK',749,517)}
}
