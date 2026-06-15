# ADR-001: PostgreSQL as System of Record

Status: Accepted

Decision:
PostgreSQL shall serve as the authoritative system of record for Havilah OS.

Rationale:
- Structured memory requires durable persistence.
- Approval Ledger requires transactional consistency.
- Domain events require auditability.
- Business entities must remain independent of any AI model.

Consequences:
- AI systems may read from and write to PostgreSQL.
- PostgreSQL remains the source of truth.
- AI memory is supplemental, not authoritative.
