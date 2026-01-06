import asyncio
from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio
from typing import Callable, Dict, Iterable


class TaskExecutor:
    def __init__(self, description: str = "Processing tasks", verbose: bool = True, timeout: float = None):
        self.description = description
        self.verbose = verbose
        self.timeout = timeout

    async def _async_task(self, sync_func: Callable, task_name: str,
                          unique_kwargs: Dict, common_kwargs: Dict,
                          result_processor: Callable):
        try:
            result = await asyncio.wait_for(asyncio.to_thread(sync_func, **unique_kwargs, **common_kwargs),
                                            timeout=self.timeout)
            if result_processor:
                result_processor(result)
            return (True, task_name, unique_kwargs, result)
        except asyncio.TimeoutError:
            msg = f"timeout (>={self.timeout}s)" if self.timeout else "timeout"
            tqdm_asyncio.write(f"⚠️ Task [{task_name}] failed: {msg}")
            return (False, task_name, unique_kwargs, msg)
        except Exception as e:
            tqdm_asyncio.write(f"❌ Task [{task_name}] failed: {str(e)}")
            return (False, task_name, unique_kwargs, str(e))

    def _sync_task(self, sync_func: Callable, task_name: str,
                   unique_kwargs: Dict, common_kwargs: Dict,
                   result_processor: Callable):
        try:
            result = sync_func(**unique_kwargs, **common_kwargs)
            if result_processor:
                result_processor(result)
            return (True, task_name, unique_kwargs, result)
        except asyncio.TimeoutError:
            msg = f"timeout (>={self.timeout}s)" if self.timeout else "timeout"
            tqdm.write(f"⚠️ Task [{task_name}] failed: {msg}")
            return (False, task_name, unique_kwargs, msg)
        except Exception as e:
            tqdm.write(f"❌ Task [{task_name}] failed: {str(e)}")
            return (False, task_name, unique_kwargs, str(e))

    def execute(self, sync_func: Callable, task_names: Iterable[str],
                unique_kwargs_list: Iterable[Dict] = None,
                common_kwargs: Dict = {},
                result_processor: Callable = None,
                max_retry_times: int = 1,
                parallel: bool = True):
        if unique_kwargs_list is None:
            unique_kwargs_list = [{}] * len(list(task_names))
        
        succeed_tasks = []
        failed_tasks = [(False, name, kwargs, "")
                        for name, kwargs in zip(task_names, unique_kwargs_list)]
        
        for retry_time in range(max_retry_times):
            if not failed_tasks:
                break
                
            results = []
            
            if parallel:
                async_tasks = [self._async_task(sync_func, name, kwargs, common_kwargs, result_processor)
                               for _, name, kwargs, _ in failed_tasks]
                
                if self.verbose:
                    gatherer = tqdm_asyncio.gather(*async_tasks, desc=f"{self.description} (try {retry_time + 1})")
                else:
                    gatherer = asyncio.gather(*async_tasks)
                    
                results = asyncio.run(gatherer)
            else:
                task_iterator = tqdm(failed_tasks, desc=f"{self.description} (try {retry_time + 1})", disable=not self.verbose)
                for _, name, kwargs, _ in task_iterator:
                    results.append(self._sync_task(sync_func, name, kwargs, common_kwargs, result_processor))
            
            failed_tasks = []
            for result in results:
                success, name, kwargs, _ = result
                if success:
                    succeed_tasks.append(result)
                else:
                    failed_tasks.append(result)
        
        return succeed_tasks, failed_tasks
