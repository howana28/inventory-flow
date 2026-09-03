import type {Metadata} from 'next';import './globals.css';
export const metadata:Metadata={title:'Inventory Flow',description:'Plataforma multioperador para contagem, validação e reconciliação de inventário'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="pt-BR" suppressHydrationWarning><body>{children}</body></html>}
