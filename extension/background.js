chrome.runtime.onMessage.addListener((message,sender,respond)=>{
 if(sender.id!==chrome.runtime.id||!sender.tab||message.type!=='selection-ready')return;
 if(typeof message.text!=='string'||!message.text.trim()||message.text.length>20000){respond({ok:false});return}
 chrome.storage.session.set({selectedText:message.text}).then(()=>chrome.action.openPopup()).catch(()=>{});
 respond({ok:true});
});
