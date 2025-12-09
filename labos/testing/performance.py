"""
Performance Testing

Tools for measuring execution time, memory usage, and benchmarking.
"""

from dataclasses import dataclass
from typing import Callable, Any, Dict, List, Optional
import time
import tracemalloc
from contextlib import contextmanager


@dataclass
class BenchmarkResult:
    """Results from a performance benchmark"""
    name: str
    execution_time: float  # seconds
    memory_used: float  # MB
    iterations: int
    avg_time_per_iteration: float
    metadata: Dict[str, Any]
    
    def summary(self) -> str:
        """
        Generate human-readable summary
        
        Returns:
            Summary string
        """
        lines = [
            f"Benchmark: {self.name}",
            f"  Iterations: {self.iterations}",
            f"  Total time: {self.execution_time:.4f}s",
            f"  Avg per iteration: {self.avg_time_per_iteration:.6f}s",
            f"  Memory used: {self.memory_used:.2f} MB"
        ]
        
        if self.metadata:
            lines.append("  Metadata:")
            for key, value in self.metadata.items():
                lines.append(f"    {key}: {value}")
                
        return "\n".join(lines)


class PerformanceBenchmark:
    """
    Performance benchmarking utility
    
    Educational Note:
        Benchmarking helps identify performance bottlenecks
        and regressions. Always benchmark on representative
        data sizes and conditions.
    """
    
    def __init__(self, name: str):
        """
        Initialize benchmark
        
        Args:
            name: Benchmark name
        """
        self.name = name
        self.results: List[BenchmarkResult] = []
        
    def run(
        self,
        func: Callable,
        iterations: int = 100,
        warmup: int = 10,
        *args,
        **kwargs
    ) -> BenchmarkResult:
        """
        Run performance benchmark
        
        Args:
            func: Function to benchmark
            iterations: Number of iterations
            warmup: Number of warmup iterations
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            BenchmarkResult
            
        Educational Note:
            Warmup iterations help stabilize timing by allowing
            JIT compilation, cache warming, and GC to settle.
        """
        # Warmup
        for _ in range(warmup):
            func(*args, **kwargs)
            
        # Start memory tracking
        tracemalloc.start()
        
        # Benchmark
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            func(*args, **kwargs)
            
        end_time = time.perf_counter()
        
        # Get memory stats
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        execution_time = end_time - start_time
        avg_time = execution_time / iterations
        memory_mb = peak / (1024 * 1024)
        
        result = BenchmarkResult(
            name=self.name,
            execution_time=execution_time,
            memory_used=memory_mb,
            iterations=iterations,
            avg_time_per_iteration=avg_time,
            metadata={
                "warmup_iterations": warmup,
                "function_name": func.__name__
            }
        )
        
        self.results.append(result)
        return result
    
    def compare(
        self,
        baseline: BenchmarkResult,
        current: BenchmarkResult
    ) -> Dict[str, Any]:
        """
        Compare two benchmark results
        
        Args:
            baseline: Baseline benchmark
            current: Current benchmark
            
        Returns:
            Comparison dictionary
            
        Educational Note:
            Regression detection compares current performance
            against baseline to catch performance degradation.
        """
        time_ratio = current.avg_time_per_iteration / baseline.avg_time_per_iteration
        time_change_pct = (time_ratio - 1.0) * 100.0
        
        memory_ratio = current.memory_used / baseline.memory_used if baseline.memory_used > 0 else 1.0
        memory_change_pct = (memory_ratio - 1.0) * 100.0
        
        comparison = {
            "baseline_name": baseline.name,
            "current_name": current.name,
            "time_ratio": time_ratio,
            "time_change_percent": time_change_pct,
            "memory_ratio": memory_ratio,
            "memory_change_percent": memory_change_pct,
            "is_regression": time_ratio > 1.1,  # >10% slower
            "is_improvement": time_ratio < 0.9  # >10% faster
        }
        
        return comparison


@contextmanager
def measure_execution_time(name: str = "operation"):
    """
    Context manager for measuring execution time
    
    Args:
        name: Operation name
        
    Yields:
        Dictionary to store timing results
        
    Example:
        with measure_execution_time("data_processing") as timer:
            # ... do work ...
            pass
        print(f"Took {timer['elapsed']:.4f}s")
        
    Educational Note:
        Context managers ensure cleanup (e.g., stopping timer)
        even if exceptions occur within the block.
    """
    timer = {"name": name, "start": 0.0, "end": 0.0, "elapsed": 0.0}
    
    timer["start"] = time.perf_counter()
    
    try:
        yield timer
    finally:
        timer["end"] = time.perf_counter()
        timer["elapsed"] = timer["end"] - timer["start"]


@contextmanager
def measure_memory_usage(name: str = "operation"):
    """
    Context manager for measuring memory usage
    
    Args:
        name: Operation name
        
    Yields:
        Dictionary to store memory results
        
    Example:
        with measure_memory_usage("data_loading") as mem:
            # ... load data ...
            pass
        print(f"Peak memory: {mem['peak_mb']:.2f} MB")
    """
    mem = {"name": name, "current_mb": 0.0, "peak_mb": 0.0}
    
    tracemalloc.start()
    
    try:
        yield mem
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        mem["current_mb"] = current / (1024 * 1024)
        mem["peak_mb"] = peak / (1024 * 1024)


def profile_function(func: Callable, iterations: int = 100) -> Dict[str, Any]:
    """
    Quick profiling of a function
    
    Args:
        func: Function to profile
        iterations: Number of iterations
        
    Returns:
        Profile results dictionary
        
    Educational Note:
        Quick profiling helps identify slow functions without
        setting up complex profiling infrastructure.
    """
    # Warmup
    func()
    
    # Time measurement
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append(end - start)
        
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    # Calculate standard deviation
    variance = sum((t - avg_time) ** 2 for t in times) / len(times)
    std_dev = variance ** 0.5
    
    profile = {
        "function": func.__name__,
        "iterations": iterations,
        "avg_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "std_dev": std_dev,
        "total_time": sum(times)
    }
    
    return profile


def benchmark_comparison(
    functions: List[tuple],
    iterations: int = 100
) -> List[Dict[str, Any]]:
    """
    Compare performance of multiple functions
    
    Args:
        functions: List of (name, function, args, kwargs) tuples
        iterations: Number of iterations per function
        
    Returns:
        List of benchmark results sorted by execution time
        
    Educational Note:
        Comparative benchmarking helps choose between different
        algorithm implementations or library choices.
    """
    results = []
    
    for name, func, args, kwargs in functions:
        benchmark = PerformanceBenchmark(name)
        result = benchmark.run(func, iterations, *args, **kwargs)
        
        results.append({
            "name": name,
            "avg_time": result.avg_time_per_iteration,
            "total_time": result.execution_time,
            "memory_mb": result.memory_used,
            "iterations": iterations
        })
        
    # Sort by average time
    results.sort(key=lambda x: x["avg_time"])
    
    return results
