# Transfer maintenance

When inserting a newly researched transfer, set `added_at` to the actual UTC insertion timestamp (ISO 8601). Preserve it on later corrections; do not reset it when verifying or editing an existing entry. Keep this field consistent in the main database, latest batch and maintenance review records. The UI uses it for the 72-hour New badge; the transfer/report date remains separate.
