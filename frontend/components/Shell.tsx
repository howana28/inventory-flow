'use client';
import {useEffect,useState} from 'react';
import {usePathname,useRouter} from 'next/navigation';
import Icon from './Icons';
import {api,browserSession} from '@/lib/api';
import {roleLabel} from '@/lib/labels';
import type {User} from '@/lib/types';
const nav=[
 ['/dashboard','Visão geral','dashboard','DASHBOARD'],['/preparar','Preparar inventário','prepare','PREPARAR_INVENTARIO'],['/bipagem','Bipagem','scan','BIPAGEM'],['/validacao','Validação','validate','VALIDACAO'],['/recontagem','Recontagem','recount','RECONTAGEM'],['/historico','Histórico','history','HISTORICO'],['/usuarios','Usuários','users','USUARIOS'],['/integracoes','Integrações','integrations','INTEGRACOES'],
] as const;
export default function Shell({title,permission,children}:{title:string;permission:string;children:React.ReactNode}){
 const[user,setUser]=useState<User|null>(null);const[ready,setReady]=useState(false);const[collapsed,setCollapsed]=useState(false);const[mobile,setMobile]=useState(false);const[theme,setTheme]=useState<'light'|'dark'>('light');const router=useRouter();const path=usePathname();
 useEffect(()=>{const c=localStorage.getItem('inventoryflow-sidebar')==='1';const t=(localStorage.getItem('inventoryflow-theme') as any)||'light';setCollapsed(c);setTheme(t);document.documentElement.dataset.theme=t;api<any>('/auth/me').then(d=>{setUser(d.user);if(!d.user.permissions.includes(permission))router.replace('/dashboard')}).catch(()=>router.replace('/login')).finally(()=>setReady(true))},[permission,router]);
 function toggleTheme(){const t=theme==='light'?'dark':'light';setTheme(t);localStorage.setItem('inventoryflow-theme',t);document.documentElement.dataset.theme=t}
 function toggleCollapse(){const n=!collapsed;setCollapsed(n);localStorage.setItem('inventoryflow-sidebar',n?'1':'0')}
 async function logout(){try{await api('/locks/release-session',{method:'POST',body:JSON.stringify({session_id:browserSession()})})}catch{}await api('/auth/logout',{method:'POST'}).catch(()=>{});router.push('/login')}
 if(!ready)return <div className="appBoot"><div className="brandMark">IF</div><span>Inventory Flow</span></div>;
 return <div className={`appShell ${collapsed?'collapsed':''}`}>
  <aside className={`sidebar ${mobile?'mobileOpen':''}`}>
   <div className="brand"><div className="brandMark">IF</div><div className="brandText"><strong>Inventory Flow</strong><span>Controle de Inventário</span></div></div>
   <button className="sidebarCollapse desktopOnly" onClick={toggleCollapse} title={collapsed?'Expandir menu':'Recolher menu'} aria-label={collapsed?'Expandir menu':'Recolher menu'}><Icon name={collapsed?'panelExpand':'panelCollapse'} size={17}/></button>
   <nav>{nav.filter(n=>user?.permissions.includes(n[3])).map(n=><a key={n[0]} href={`${n[0]}/`} className={path.startsWith(n[0])?'active':''} title={n[1]} onClick={()=>setMobile(false)}><Icon name={n[2]}/><span>{n[1]}</span></a>)}</nav>
   <div className="sidebarBottom"><div className="userCard"><div className="avatar">{user?.name?.slice(0,2).toUpperCase()}</div><div><strong>{user?.name}</strong><span>{roleLabel(user?.role||'')}</span></div></div><button className="sidebarAction" onClick={logout}><Icon name="logout"/><span>Sair</span></button></div>
  </aside>
  {mobile&&<button className="backdrop" onClick={()=>setMobile(false)} aria-label="Fechar menu"/>}
  <main className="main"><header className="topbar"><div><button className="iconBtn mobileOnly" onClick={()=>setMobile(true)}><Icon name="menu"/></button><div><span className="eyebrow">INVENTORY FLOW</span><h1>{title}</h1></div></div><button className="iconBtn" onClick={toggleTheme} title="Alternar tema"><Icon name={theme==='light'?'moon':'sun'}/></button></header><div className="page">{children}</div></main>
 </div>
}
