export {requestJson as lifeApi} from './requestJson';
export function fileData(file:File):Promise<string>{return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(Error('File could not be read'));reader.readAsDataURL(file)})}
