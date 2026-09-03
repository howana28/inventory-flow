export type User={id:string;name:string;email:string;role:string;permissions:string[];active:boolean};
export type Inventory={id:string;code:string;label:string;status:string;created_at:string;closed_at?:string|null};
export type Item={sku:string;ean:string;name:string;brand:string;location:string;zone:string;snapshot_stock:number;counted_qty:number|null;recount_qty:number|null;difference:number|null;status:string;difference_label:string;resolution:string;note:string};
