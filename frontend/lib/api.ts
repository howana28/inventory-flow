export class ApiError extends Error{status:number;constructor(message:string,status:number){super(message);this.status=status}}
export async function api<T=any>(path:string,options:RequestInit={}):Promise<T>{
 const response=await fetch(`/api/v1${path}`,{...options,credentials:'include',headers:{'Content-Type':'application/json',...(options.headers||{})},cache:'no-store'});
 if(!response.ok){let message=`Erro ${response.status}`;try{const d=await response.json();message=d.detail||d.message||message}catch{}throw new ApiError(message,response.status)}
 const type=response.headers.get('content-type')||'';if(type.includes('application/json'))return response.json();return response as any;
}
export function browserSession(){const key='inventoryflow-browser-session';let id=localStorage.getItem(key);if(!id){id=crypto.randomUUID();localStorage.setItem(key,id)}return id}
