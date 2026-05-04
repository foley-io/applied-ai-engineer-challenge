# Sample data

Tiny synthetic dataset for local development. The real compliance database
lives in Redshift; talk to the data team for access.

- `drivers.csv` — 5 sample drivers
- `documents/` — driver-submitted documents (create per-driver `.txt` files
  named `D-XXXX.txt` to test the document review path)
- `violations.db` — SQLite. The agent expects this; create it with the schema
  in `schema.sql` if you want to run end-to-end.
