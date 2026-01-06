Simple usage:
```
succeed_tasks, failed_tasks = TaskExecutor(description="Fetch Protein Sequences").execute(
    get_protein_sequence,
    indices,
    [{"uniprot_id": uniprot_id} for uniprot_id in uniprot_ids],
    {"timeout": 10},
    max_retry_times=5,
    parallel=True,
)
```
