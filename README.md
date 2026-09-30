# Dashboard Tiflux

Painel de chamados do Tiflux: visão por cliente, mesa e técnico, atrasos de SLA e exportação XLSX/CSV.

```bash
docker compose up -d --build     # sobe api, sync e web (Postgres é o container compartilhado "Postgres")
```
- Painel: http://localhost:8080 (porta `WEB_PORT` do `.env`)
- Postgres (externo): `localhost:${DB_PORT}`, banco `DB_NAME`, schema `SCHEMA_NAME`
- Primeira carga leva ~15 min (acompanhe com `docker compose logs -f sync`); depois atualiza a cada `SYNC_INTERVAL_MINUTES`.
- Forçar atualização agora: `docker compose restart sync` (roda um ciclo ao iniciar).
- Configuração: copie `.env.example` para `.env` e preencha `TOKEN_TIFLUX` e `DB_PASSWORD`.

Documentação técnica: `docs/INDEX.md`.
