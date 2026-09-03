# Portfolio case study

## Problem

Physical inventories become risky when several operators count simultaneously: duplicated work, stale spreadsheets, unclear ownership of locations, inconsistent recounts and poor auditability.

## Solution

InventoryFlow models the workflow as a transactional, multi-user application. The catalog is snapshotted before counting, zones are reserved through expiring locks, validation is deterministic, and recount work is distributed by SKU with the same concurrency guarantees.

## What this edition demonstrates

- Full-stack architecture with Next.js + FastAPI.
- Persistent RBAC and secure server-side sessions.
- Multi-operator concurrency control with heartbeat.
- Barcode/SKU-driven mobile-friendly counting.
- Immutable inventory snapshot and deterministic reconciliation.
- Recount queue with per-item reservation.
- Audit trail and Excel export.
- Pluggable ERP provider with a public synthetic demo and optional Bling OAuth 2.0 integration.
- Dockerized single-service deployment.

All sample products, stock quantities, users and inventory events in this repository are fictional.
