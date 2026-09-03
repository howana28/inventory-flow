from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def ck(name,ok):checks.append((name,bool(ok)));print(f"{name}: {'OK' if ok else 'FALHOU'}")
required=['frontend/app/page.tsx','frontend/app/dashboard/page.tsx','frontend/app/bipagem/page.tsx','frontend/app/validacao/page.tsx','frontend/app/recontagem/page.tsx','frontend/app/integracoes/page.tsx','backend/app/main.py','backend/app/services/integrations.py','backend/.env.example','Dockerfile','README.md']
for f in required:ck(f,(ROOT/f).exists())
files=[p for p in ROOT.rglob('*') if p.is_file() and p.resolve()!=Path(__file__).resolve() and p.suffix.lower() in {'.py','.ts','.tsx','.md','.env','.json','.yaml','.yml','.sql','.css'}]
text='\n'.join(p.read_text(errors='ignore') for p in files)
ck('Sem referência à empresa original','enaltecer' not in text.lower())
ck('Sem URLs de Supabase reais','supabase.co' not in text.lower())
ck('Sem segredo Bling preenchido',not re.search(r'(?m)^BLING_CLIENT_SECRET[ \t]*=[ \t]*[^#\r\n \t]+',text))
ck('Provider demo presente','DemoERP' in text or 'sync_demo_catalog' in text)
ck('Bling OAuth presente','oauth' in (ROOT/'backend/app/services/integrations.py').read_text().lower())
ck('Locks por rua e SKU','COUNTING' in text and 'RECOUNT' in text and 'resource_locks' in text)
if not all(v for _,v in checks):raise SystemExit(1)
print('\nINVENTORYFLOW PORTFOLIO — ESTRUTURA OK')
