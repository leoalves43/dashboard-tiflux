# HANDOFF (2026-10-01)
DONE: plans 001, 002. Plan 003 (description copied into the DB + "Descrição" export column) REVERTED: sync only syncs tickets again; hover/modal read the description live from Tiflux; ticket export has no description column. nginx re-resolve fix kept. UI http://localhost:8080.
NEXT: LATER (server): store descriptions + communications + attachments (redo 003 via `git revert` of the revert commit). Optional — link ticket numbers to Tiflux web; business-hours SLA; async full XLSX export (~95 s). Old volume `dashboard-tiflux_pgdata` orphaned — delete when sure.
RISKS: table `ticket_descriptions` left in the DB with the rows already copied (no code reads it; reuse on the server or DROP). Modal/hover description and communications need Tiflux up. Attachment links may expire. Depends on external `Postgres` container.
CONTEXT: docs/ARCHITECTURE.md, docs/plans/003-ticket-description.md (reverted status).
