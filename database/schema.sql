-- InventoryFlow Portfolio Edition
-- Reference PostgreSQL schema. The application also creates tables automatically
-- through SQLAlchemy, and SQLite is supported for zero-config local demos.

create table if not exists users (
  id varchar(36) primary key,
  name varchar(120) not null,
  email varchar(190) unique not null,
  password_hash text not null,
  role varchar(30) not null,
  permissions text not null default '[]',
  active boolean not null default true,
  created_at timestamp not null default current_timestamp
);

create table if not exists products (
  id varchar(36) primary key,
  sku varchar(60) unique not null,
  ean varchar(32) unique not null,
  name varchar(220) not null,
  brand varchar(100) not null,
  location varchar(80) not null,
  system_stock integer not null default 0,
  active boolean not null default true,
  updated_at timestamp not null default current_timestamp
);

create table if not exists inventories (
  id varchar(36) primary key,
  code varchar(40) unique not null,
  label varchar(160) not null,
  status varchar(30) not null,
  created_by varchar(36) not null,
  created_at timestamp not null default current_timestamp,
  closed_at timestamp null
);

-- Remaining operational tables are defined in backend/app/models.py:
-- inventory_zones, inventory_items, resource_locks, auth_sessions,
-- audit_logs, sync_logs and app_settings.
