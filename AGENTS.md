# Transfer maintenance

When inserting a newly researched transfer, set `added_at` to the actual UTC insertion timestamp (ISO 8601). Preserve it on later corrections; do not reset it when verifying or editing an existing entry. Keep this field consistent in the main database, latest batch and maintenance review records. The UI uses it for the 24-hour New badge; the transfer/report date remains separate.

When multiple sources support an event, retain each verified direct URL and publisher in `sources` alongside the primary `source_url` and `source_name`. Open the actual sources before adding them. Prefer original club or league announcements and independent reporting; syndicated copies or articles repeating the same claim are not independent confirmation. Preserve earlier evidence and label rumors accurately. Player details display all supporting source links.
