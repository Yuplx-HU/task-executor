import asyncio
from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio
from typing import Callable, Dict, Iterable


class TaskExecutor:
    def __init__(self, verbose: bool = True, timeout: float = 0.0):
        self.verbose = verbose
        self.timeout = timeout

    async def _async_task(self, sync_func: Callable, task_name: str,
                          unique_kwargs: Dict, common_kwargs: Dict, result_processor: Callable):
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(sync_func, **unique_kwargs, **common_kwargs),
                timeout=self.timeout
            )
            if result_processor:
                result_processor(result)
            return ("success", task_name, unique_kwargs, result)
        except asyncio.TimeoutError:
            msg = f"timeout (>={self.timeout}s)" if self.timeout else "timeout"
            tqdm_asyncio.write(f"⚠️ Task [{task_name}] failed: {msg}")
            return ("timeout", task_name, unique_kwargs, msg)
        except Exception as e:
            tqdm_asyncio.write(f"❌ Task [{task_name}] failed: {str(e)}")
            return ("error", task_name, unique_kwargs, str(e))

    def _sync_task(self, sync_func: Callable, task_name: str,
                   unique_kwargs: Dict, common_kwargs: Dict, result_processor: Callable):
        try:
            result = sync_func(**unique_kwargs, **common_kwargs)
            if result_processor:
                result_processor(result)
            return ("success", task_name, unique_kwargs, result)
        except asyncio.TimeoutError:
            msg = f"timeout (>={self.timeout}s)" if self.timeout else "timeout"
            tqdm.write(f"⚠️ Task [{task_name}] failed: {msg}")
            return ("timeout", task_name, unique_kwargs, msg)
        except Exception as e:
            tqdm.write(f"❌ Task [{task_name}] failed: {str(e)}")
            return ("error", task_name, unique_kwargs, str(e))

    def execute(self, sync_func: Callable, task_names: Iterable[str],
                unique_kwargs_list: Iterable[Dict], common_kwargs: Dict = {}, result_processor: Callable = None,
                # Async or sync.
                parallel: bool = False,
                # Retry.
                max_retry_times: int = 1, retry_task_filters: Iterable[str] = []):
        succeed_tasks = []
        failed_tasks = [("start", n, kw, "") for n, kw in zip(task_names, unique_kwargs_list)]

        for retry_time in range(max_retry_times):
            if not failed_tasks:
                break

            results = []
            filtered_tasks = [task for task in failed_tasks if task[0] == "start" or task[0] in retry_task_filters]
            if parallel:
                filtered_tasks = [self._async_task(sync_func, n, kw, common_kwargs, result_processor) for _, n, kw, _ in filtered_tasks]
                gatherer = tqdm_asyncio.gather(*filtered_tasks, desc=f"Processing tasks (try {retry_time + 1})") if self.verbose else asyncio.gather(*filtered_tasks)
                results = asyncio.run(gatherer)
            else:
                for _, n, kw, _ in tqdm(filtered_tasks, desc=f"Processing tasks (try {retry_time + 1})", disable=not self.verbose):
                    results.append(self._sync_task(sync_func, n, kw, common_kwargs, result_processor))

            failed_tasks = []
            for result in results:
                if result[0] == "success":
                    succeed_tasks.append(result)
                else:
                    failed_tasks.append(result)

        return succeed_tasks, failed_tasks
