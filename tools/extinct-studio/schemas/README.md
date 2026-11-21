These JSON Schemas describe the public, redacted project contracts. The runtime
validator in `../lib.mjs` deliberately applies extra safety rules that are harder
to express in a schema: private Drive/Docs URL rejection, credential detection,
sequential state transitions, proof-clock checks, and owner-manual publication.

Schemas are contracts, not evidence. A schema-valid file still needs the relevant
human review and source receipts.
