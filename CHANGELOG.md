# Changelog

## 1.3.0
- Corrige o alinhamento das localizações no card demonstrativo da landing page.
- As colunas SKU, localização e status agora mantêm posições fixas entre todas as linhas.
- Ajuste responsivo para telas menores, evitando deslocamentos visuais entre linhas.

## 1.2.0 — 2026-09-03
- Interface e apresentação pública revisadas para português, mantendo apenas **Inventory Flow** como nome do produto.
- Landing page: “Controle Operacional de Inventário” e “Arquitetura” substituem os títulos em inglês.
- Removida a indicação “Portfolio Edition · Synthetic data only” do rodapé público.
- Dashboard passou a ser exibido como **Visão geral**.
- Integrações, permissões, funções, status e auditoria receberam rótulos mais naturais em português.
- Termos de interface como Demo Provider, Database, Engine, Sync e TTL foram substituídos por linguagem operacional em português.
- A Bipagem permanece sem imagens de produto nesta versão para priorizar velocidade e leitura no celular.

## 1.1.0 — 2026-09-03
- Interface operacional passou a usar **Rua** em vez de **Zona**.
- Controle de recolher/expandir menu redesenhado como uma alça discreta na borda lateral.
- Ajustadas mensagens do backend e textos da validação/dashboard para a mesma linguagem operacional.

# Changelog

## 1.0.0 — Portfolio Edition

- New independent InventoryFlow identity and architecture.
- Synthetic 420-product demo catalog across 18 zones.
- Opaque authentication sessions and RBAC permissions.
- Zone reservation, heartbeat and F5-safe counting flow.
- Validation based on physical count minus immutable system snapshot.
- Per-SKU recount reservations with optional next-item flow.
- Historical inventory and audit trail.
- Excel export.
- Admin-only Integrations module with safe database metadata and sync history.
- Demo ERP provider and optional Bling OAuth 2.0 provider.
- Demo scenarios for counting, validation and recount presentations.
- Docker, Render blueprint, tests and security/architecture documentation.
