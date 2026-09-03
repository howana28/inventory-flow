import React from 'react';
export function Panel({children,className=''}:{children:React.ReactNode,className?:string}){return <section className={`panel ${className}`}>{children}</section>}
export function Metric({label,value,detail}:{label:string,value:React.ReactNode,detail?:string}){return <div className="metric"><span>{label}</span><strong>{value}</strong>{detail&&<small>{detail}</small>}</div>}
export function Alert({children,type='info'}:{children:React.ReactNode,type?:'info'|'success'|'error'|'warn'}){return <div className={`alert ${type}`}>{children}</div>}
export function Badge({children,tone='neutral'}:{children:React.ReactNode,tone?:string}){return <span className={`badge ${tone}`}>{children}</span>}
export function Loading(){return <div className="loading"><span></span><p>Carregando...</p></div>}
export function Empty({title,children}:{title:string,children?:React.ReactNode}){return <div className="empty"><div className="emptyMark">IF</div><h3>{title}</h3>{children&&<p>{children}</p>}</div>}
