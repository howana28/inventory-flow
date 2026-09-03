export const statusLabel=(status:string)=>({
  EM_CONTAGEM:'Em contagem',
  VALIDACAO:'Em validação',
  ENCERRADO:'Encerrado',
  CANCELADO:'Cancelado',
  PENDENTE:'Pendente',
  CONTADO:'Contado',
  DIVERGENTE:'Divergente',
  RECONTAGEM:'Recontagem',
  APROVADO:'Aprovado',
  FINALIZADA:'Finalizada',
  OK:'OK',
  SUCCESS:'Sucesso',
  ERROR:'Erro',
  FAILED:'Falha',
}[status]||String(status||'').replaceAll('_',' ').toLowerCase().replace(/^./,c=>c.toUpperCase()));

export const roleLabel=(role:string)=>({
  ADMIN:'Administrador',
  SUPERVISOR:'Supervisor',
  OPERADOR:'Operador',
}[role]||role);

export const permissionLabel=(permission:string)=>({
  DASHBOARD:'Visão geral',
  PREPARAR_INVENTARIO:'Preparar inventário',
  BIPAGEM:'Bipagem',
  VALIDACAO:'Validação',
  RECONTAGEM:'Recontagem',
  HISTORICO:'Histórico',
  USUARIOS:'Usuários',
  INTEGRACOES:'Integrações',
}[permission]||permission.replaceAll('_',' '));

export const auditActionLabel=(action:string)=>({
  ZONE_RESERVED:'Rua reservada',
  ITEM_COUNTED:'Item contado',
  ZONE_FINALIZED:'Rua finalizada',
  RECOUNT_REQUESTED:'Recontagem solicitada',
  DIVERGENCE_APPROVED:'Divergência aprovada',
  RECOUNT_RESERVED:'Recontagem reservada',
  RECOUNT_SUBMITTED:'Recontagem registrada',
  INVENTORY_STARTED:'Inventário iniciado',
  VALIDATION_CONSOLIDATED:'Validação consolidada',
  INVENTORY_CLOSED:'Inventário encerrado',
}[action]||String(action||'').replaceAll('_',' '));
