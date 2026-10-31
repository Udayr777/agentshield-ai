// Never retry mutations automatically: the server may have committed before a disconnect.
export async function requestJson(path:string,body?:unknown){
 let response:Response;
 try{response=await fetch('/api'+path,body===undefined?undefined:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})}
 catch{throw Error('Could not reach AgentShield. Check your connection and that the app servers are running. If you submitted an import or upload, refresh the draft list before retrying; it may already have completed.')}
 let data;
 try{data=await response.json()}
 catch{throw Error(`AgentShield returned an incomplete or invalid response (HTTP ${response.status}). Refresh the draft list before retrying. If this continues, check the server deployment logs.`)}
 if(!response.ok)throw Error(data?.error||`AgentShield request failed (HTTP ${response.status}).`);
 return data;
}
