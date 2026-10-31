// Audio lifecycle regression without requiring a speaker or paid model call.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const ts=require('../dashboard/node_modules/typescript');
const instances=[];
class AudioContextFixture{
 constructor(){this.state='running';this.currentTime=0;this.destination={};this.closed=0;this.starts=[];instances.push(this)}
 createMediaStreamDestination(){return {stream:{getAudioTracks:()=>[]}}}
 createGain(){return {gain:{value:0,setValueAtTime(){},linearRampToValueAtTime(){},exponentialRampToValueAtTime(){}},connect(){}}}
 createOscillator(){return {frequency:{setValueAtTime(){}},connect(){},start:at=>this.starts.push(at),stop(){}}}
 resume(){return instances.length===2?Promise.reject(Error('Simulated device refusal')):Promise.resolve()}
 close(){assert.notEqual(this.state,'closed','Closed audio must not be closed again');this.state='closed';this.closed++;return Promise.resolve()}
}
const code=ts.transpileModule(fs.readFileSync(require('node:path').join(__dirname,'../dashboard/src/clipMedia.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const mod={exports:{}};vm.runInNewContext(code,{module:mod,exports:mod.exports,AudioContext:AudioContextFixture});
(async()=>{
 const {soundtrack,closeAudio,voiceFailure}=mod.exports;let failures=0;
 for(let run=0;run<3;run++){const audio=soundtrack(.2,()=>failures++);await Promise.resolve();assert(audio.context.starts.length>0);assert(audio.context.starts.every(t=>t>=0&&t<18));closeAudio(audio.context);closeAudio(audio.context)}
 assert.equal(new Set(instances).size,3);assert.equal(failures,1);assert(instances.every(c=>c.closed===1));
 assert.equal(voiceFailure('canceled'),false);assert.equal(voiceFailure('interrupted'),false);assert.equal(voiceFailure('audio-busy'),true);
 console.log('PASS: three fresh playback audio sessions, handled resume rejection, idempotent cleanup, expected speech cancellations ignored.');
})().catch(error=>{console.error(error);process.exitCode=1});
