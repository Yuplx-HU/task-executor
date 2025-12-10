# TaskExecutor

A lightweight Python utility for executing synchronous tasks with optional parallelization, timeout control, retry logic, and progress tracking.

## Features

- **Dual Execution Modes**: Run tasks sequentially or in parallel (async)
- **Timeout Control**: Set per-task timeouts to prevent hanging
- **Retry Mechanism**: Automatically retry failed tasks with customizable filters
- **Progress Tracking**: Real-time progress bars with `tqdm` integration
- **Flexible Error Handling**: Separate results for successful and failed tasks
- **Result Processing**: Optional callback for immediate result handling

## Installation

Requires Python 3.7+ with the following dependencies:

```bash
pip install tqdm
```

## Quick Start

```python
from task_executor import TaskExecutor

# Define your synchronous task function
def process_item(unique_kwargs, common_kwargs):
    # Your task logic here
    item_id = unique_kwargs['id']
    multiplier = common_kwargs.get('multiplier', 1)
    return item_id * multiplier

# Optional result processor
def log_result(result):
    print(f"Got result: {result}")

# Create executor
executor = TaskExecutor(verbose=True, timeout=5.0)

# Execute tasks
task_names = ["task_1", "task_2", "task_3"]
unique_kwargs = [{"id": 1}, {"id": 2}, {"id": 3}]
common_kwargs = {"multiplier": 10}

success, failed = executor.execute(
    sync_func=process_item,
    task_names=task_names,
    unique_kwargs_list=unique_kwargs,
    common_kwargs=common_kwargs,
    result_processor=log_result,
    parallel=True,  # Use async parallel execution
    max_retry_times=2,
    retry_task_filters=["timeout", "error"]
)

print(f"Success: {len(success)} tasks")
print(f"Failed: {len(failed)} tasks")
```

## API Reference

### `TaskExecutor(verbose=True, timeout=0.0)`

**Parameters:**
- `verbose` (bool): Show progress bars and real-time logging
- `timeout` (float): Task timeout in seconds (0 = no timeout)

### `execute()`

```python
execute(
    sync_func: Callable,
    task_names: Iterable[str],
    unique_kwargs_list: Iterable[Dict],
    common_kwargs: Dict = {},
    result_processor: Callable = None,
    parallel: bool = False,
    max_retry_times: int = 1,
    retry_task_filters: Iterable[str] = []
) -> Tuple[List, List]
```

**Parameters:**
- `sync_func`: Synchronous function accepting `(unique_kwargs, common_kwargs)`
- `task_names`: Names for each task (for logging)
- `unique_kwargs_list`: Individual parameters for each task
- `common_kwargs`: Shared parameters for all tasks
- `result_processor`: Optional callback to process results immediately
- `parallel`: Use async parallel execution when True
- `max_retry_times`: Maximum retry attempts
- `retry_task_filters`: Which failure types to retry: ["timeout", "error"]

**Returns:** Tuple of (succeeded_tasks, failed_tasks)

**Task Result Format:**
- Success: `("success", task_name, unique_kwargs, result)`
- Timeout: `("timeout", task_name, unique_kwargs, message)`
- Error: `("error", task_name, unique_kwargs, error_message)`

## Advanced Examples

### Sequential Execution with Retries

```python
executor = TaskExecutor(verbose=True)
success, failed = executor.execute(
    sync_func=my_task,
    task_names=names,
    unique_kwargs_list=params,
    common_kwargs=shared_params,
    parallel=False,  # Sequential execution
    max_retry_times=3,
    retry_task_filters=["error"]  # Retry only errors, not timeouts
)
```

### Batch Processing with Immediate Storage

```python
results = []

def store_result(result):
    results.append(result)
    # Or save to database/file immediately

executor.execute(
    sync_func=data_processor,
    task_names=[f"item_{i}" for i in range(1000)],
    unique_kwargs_list=[{"index": i} for i in range(1000)],
    result_processor=store_result,
    parallel=True
)
```

## Error Handling

The executor automatically catches and categorizes errors:

- **Timeouts**: Tasks exceeding the specified timeout
- **Exceptions**: Any other exceptions raised during execution
- **Retry Logic**: Failed tasks can be retried based on failure type

## Notes

1. For parallel execution, `sync_func` runs in a thread pool (using `asyncio.to_thread`)
2. Timeout only applies to parallel (async) execution mode
3. The `result_processor` runs immediately upon task completion
4. Task names are for identification and logging only
