import React from 'react';
type Props={name:string;size?:number};
export default function Icon({name,size=19}:Props){const common={width:size,height:size,viewBox:'0 0 24 24',fill:'none',stroke:'currentColor',strokeWidth:1.8,strokeLinecap:'round' as const,strokeLinejoin:'round' as const};const paths:any={
 dashboard:<><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></>,
 prepare:<><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/></>,
 scan:<><path d="M4 7V4h3M17 4h3v3M20 17v3h-3M7 20H4v-3"/><path d="M7 12h10M8 9v6M11 9v6M14 9v6M17 9v6"/></>,
 validate:<><path d="M9 11l2 2 4-4"/><path d="M5 4h14v16H5z"/></>,
 recount:<><path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/></>,
 history:<><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
 users:<><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></>,
 integrations:<><path d="M8 12h8M12 8v8"/><circle cx="12" cy="12" r="9"/></>,
 sun:<><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42"/></>,
 moon:<><path d="M20 15.5A8.5 8.5 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5z"/></>,
 logout:<><path d="M10 17l5-5-5-5M15 12H3"/><path d="M14 3h5a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-5"/></>,
 menu:<><path d="M4 6h16M4 12h16M4 18h16"/></>,
 chevron:<><path d="m9 18 6-6-6-6"/></>,
 panelCollapse:<><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M8 4v16"/><path d="m15 9-3 3 3 3"/></>,
 panelExpand:<><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M8 4v16"/><path d="m12 9 3 3-3 3"/></>,
};return <svg {...common}>{paths[name]||paths.dashboard}</svg>}
