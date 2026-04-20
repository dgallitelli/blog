#!/usr/bin/env python3
"""
SageMaker Inference Cost Calculator
====================================
Estimates wall-clock time and cost for:
  - Real-Time Endpoint (always-on)
  - Batch Transform (per-job)
  - Async Inference (scale-to-zero)

Usage:
    python sagemaker_inference_cost_calculator.py

Adjust the parameters in the CONFIG section below, or import the functions
into your own scripts:

    from sagemaker_inference_cost_calculator import estimate_all
    results = estimate_all(
        total_items=100_000,
        latency_per_item_sec=30,
        instance_type_cost_per_hour=0.922,
        ...
    )
"""

from dataclasses import dataclass


# ─── CONFIG (edit these) ──────────────────────────────────────────────────────

TOTAL_ITEMS = 100_000                   # Number of items to run inference on
LATENCY_PER_ITEM_SEC = 30               # Seconds per single inference call
INSTANCE_TYPE = "ml.m5.4xlarge"         # Instance type
INSTANCE_COST_PER_HOUR = 0.922          # On-demand price (us-east-1)

# Real-Time Endpoint
RT_INSTANCE_COUNT = 3                   # Instances behind the endpoint
RT_CLIENT_CONCURRENCY = 20              # Client-side parallel requests

# Batch Transform
BT_INSTANCE_COUNT = 20                  # Instances for the transform job
BT_CONCURRENT_PER_INSTANCE = 4          # max_concurrent_transforms
BT_COLD_START_MINUTES = 10              # Provisioning + model download

# Async Inference
ASYNC_MAX_INSTANCES = 20                # Max auto-scaling capacity
ASYNC_CONCURRENT_PER_INSTANCE = 4       # max_concurrent_invocations_per_instance
ASYNC_COLD_START_MINUTES = 10           # Scale-from-zero cold start
ASYNC_SCALE_IN_COOLDOWN_MIN = 10        # Cooldown before scaling in

# Scheduling
RUNS_PER_WEEK = 1                       # How often the batch job runs
WEEKS_PER_MONTH = 4.33                  # Average weeks per month


# ─── DATA CLASSES ─────────────────────────────────────────────────────────────

@dataclass
class RealTimeEstimate:
    instance_type: str
    instance_count: int
    client_concurrency: int
    wall_clock_hours_serial: float
    wall_clock_hours_parallel: float
    monthly_cost: float
    utilization_pct: float

    def __str__(self):
        return (
            f"Real-Time Endpoint ({self.instance_type} × {self.instance_count})\n"
            f"  Serial wall-clock:   {self.wall_clock_hours_serial:,.1f} hours\n"
            f"  Parallel wall-clock: {self.wall_clock_hours_parallel:,.1f} hours "
            f"({self.client_concurrency} concurrent)\n"
            f"  Monthly cost:        ${self.monthly_cost:,.2f} (always-on)\n"
            f"  Utilization:         {self.utilization_pct:.1f}% "
            f"({self.wall_clock_hours_parallel:.1f}h useful / {168:.0f}h per week)"
        )


@dataclass
class BatchTransformEstimate:
    instance_type: str
    instance_count: int
    concurrent_per_instance: int
    total_concurrency: int
    compute_hours: float
    cold_start_hours: float
    wall_clock_hours: float
    cost_per_job: float
    monthly_cost: float

    def __str__(self):
        return (
            f"Batch Transform ({self.instance_type} × {self.instance_count})\n"
            f"  Concurrency:     {self.total_concurrency} "
            f"({self.instance_count} inst × {self.concurrent_per_instance} concurrent)\n"
            f"  Compute time:    {self.compute_hours:,.2f} hours\n"
            f"  Cold start:      {self.cold_start_hours * 60:,.0f} minutes\n"
            f"  Wall-clock:      {self.wall_clock_hours:,.2f} hours\n"
            f"  Cost per job:    ${self.cost_per_job:,.2f}\n"
            f"  Monthly cost:    ${self.monthly_cost:,.2f} "
            f"({RUNS_PER_WEEK}×/week)"
        )


@dataclass
class AsyncInferenceEstimate:
    instance_type: str
    max_instances: int
    concurrent_per_instance: int
    total_concurrency: int
    compute_hours: float
    cold_start_hours: float
    wall_clock_hours: float
    cost_per_batch_run: float
    monthly_cost_batch_only: float
    scales_to_zero: bool

    def __str__(self):
        return (
            f"Async Inference ({self.instance_type}, max {self.max_instances} instances)\n"
            f"  Concurrency:         {self.total_concurrency} "
            f"({self.max_instances} inst × {self.concurrent_per_instance} concurrent)\n"
            f"  Compute time:        {self.compute_hours:,.2f} hours\n"
            f"  Cold start:          {self.cold_start_hours * 60:,.0f} minutes\n"
            f"  Wall-clock:          {self.wall_clock_hours:,.2f} hours\n"
            f"  Cost per batch run:  ${self.cost_per_batch_run:,.2f}\n"
            f"  Monthly (batch):     ${self.monthly_cost_batch_only:,.2f} "
            f"({RUNS_PER_WEEK}×/week)\n"
            f"  Scales to zero:      {'Yes' if self.scales_to_zero else 'No'} "
            f"(no cost between runs)"
        )


# ─── ESTIMATION FUNCTIONS ─────────────────────────────────────────────────────

def estimate_realtime(
    total_items: int = TOTAL_ITEMS,
    latency_sec: float = LATENCY_PER_ITEM_SEC,
    instance_count: int = RT_INSTANCE_COUNT,
    client_concurrency: int = RT_CLIENT_CONCURRENCY,
    cost_per_hour: float = INSTANCE_COST_PER_HOUR,
    instance_type: str = INSTANCE_TYPE,
) -> RealTimeEstimate:
    """Estimate cost and time for an always-on real-time endpoint."""
    serial_hours = (total_items * latency_sec) / 3600
    parallel_hours = (total_items / client_concurrency * latency_sec) / 3600
    monthly_cost = instance_count * 168 * WEEKS_PER_MONTH * cost_per_hour
    utilization = (parallel_hours / 168) * 100

    return RealTimeEstimate(
        instance_type=instance_type,
        instance_count=instance_count,
        client_concurrency=client_concurrency,
        wall_clock_hours_serial=serial_hours,
        wall_clock_hours_parallel=parallel_hours,
        monthly_cost=monthly_cost,
        utilization_pct=utilization,
    )


def estimate_batch_transform(
    total_items: int = TOTAL_ITEMS,
    latency_sec: float = LATENCY_PER_ITEM_SEC,
    instance_count: int = BT_INSTANCE_COUNT,
    concurrent_per_instance: int = BT_CONCURRENT_PER_INSTANCE,
    cold_start_min: float = BT_COLD_START_MINUTES,
    cost_per_hour: float = INSTANCE_COST_PER_HOUR,
    instance_type: str = INSTANCE_TYPE,
) -> BatchTransformEstimate:
    """Estimate cost and time for a Batch Transform job."""
    total_concurrency = instance_count * concurrent_per_instance
    compute_sec = (total_items / total_concurrency) * latency_sec
    compute_hours = compute_sec / 3600
    cold_start_hours = cold_start_min / 60
    wall_clock_hours = compute_hours + cold_start_hours

    # All instances billed for full job duration (including cold start)
    cost_per_job = instance_count * wall_clock_hours * cost_per_hour
    monthly_cost = cost_per_job * RUNS_PER_WEEK * WEEKS_PER_MONTH

    return BatchTransformEstimate(
        instance_type=instance_type,
        instance_count=instance_count,
        concurrent_per_instance=concurrent_per_instance,
        total_concurrency=total_concurrency,
        compute_hours=compute_hours,
        cold_start_hours=cold_start_hours,
        wall_clock_hours=wall_clock_hours,
        cost_per_job=cost_per_job,
        monthly_cost=monthly_cost,
    )


def estimate_async_inference(
    total_items: int = TOTAL_ITEMS,
    latency_sec: float = LATENCY_PER_ITEM_SEC,
    max_instances: int = ASYNC_MAX_INSTANCES,
    concurrent_per_instance: int = ASYNC_CONCURRENT_PER_INSTANCE,
    cold_start_min: float = ASYNC_COLD_START_MINUTES,
    cost_per_hour: float = INSTANCE_COST_PER_HOUR,
    instance_type: str = INSTANCE_TYPE,
) -> AsyncInferenceEstimate:
    """Estimate cost and time for Async Inference with scale-to-zero."""
    total_concurrency = max_instances * concurrent_per_instance
    compute_sec = (total_items / total_concurrency) * latency_sec
    compute_hours = compute_sec / 3600
    cold_start_hours = cold_start_min / 60
    wall_clock_hours = compute_hours + cold_start_hours

    # Async billing: per-instance-second while instances are running
    # With scale-to-zero, cost ≈ instances × job_duration (similar to BT)
    cost_per_run = max_instances * wall_clock_hours * cost_per_hour
    monthly_cost = cost_per_run * RUNS_PER_WEEK * WEEKS_PER_MONTH

    return AsyncInferenceEstimate(
        instance_type=instance_type,
        max_instances=max_instances,
        concurrent_per_instance=concurrent_per_instance,
        total_concurrency=total_concurrency,
        compute_hours=compute_hours,
        cold_start_hours=cold_start_hours,
        wall_clock_hours=wall_clock_hours,
        cost_per_batch_run=cost_per_run,
        monthly_cost_batch_only=monthly_cost,
        scales_to_zero=True,
    )


def estimate_all(**kwargs) -> dict:
    """Run all three estimates and return as a dict."""
    return {
        "realtime": estimate_realtime(**{k: v for k, v in kwargs.items()
                                         if k in estimate_realtime.__code__.co_varnames}),
        "batch_transform": estimate_batch_transform(**{k: v for k, v in kwargs.items()
                                                        if k in estimate_batch_transform.__code__.co_varnames}),
        "async_inference": estimate_async_inference(**{k: v for k, v in kwargs.items()
                                                       if k in estimate_async_inference.__code__.co_varnames}),
    }


def print_comparison(rt: RealTimeEstimate, bt: BatchTransformEstimate, ai: AsyncInferenceEstimate):
    """Print a side-by-side comparison."""
    bt_savings = (1 - bt.monthly_cost / rt.monthly_cost) * 100
    ai_savings = (1 - ai.monthly_cost_batch_only / rt.monthly_cost) * 100

    print("=" * 72)
    print(f"  SageMaker Inference Cost Comparison")
    print(f"  {TOTAL_ITEMS:,} items @ {LATENCY_PER_ITEM_SEC}s/item | {INSTANCE_TYPE}")
    print("=" * 72)
    print()
    print(rt)
    print()
    print(bt)
    print()
    print(ai)
    print()
    print("-" * 72)
    print(f"  Batch Transform vs Real-Time:  {bt_savings:+.1f}% monthly cost")
    print(f"  Async Inference vs Real-Time:   {ai_savings:+.1f}% monthly cost")
    print(f"  BT wall-clock:  {bt.wall_clock_hours:.1f}h  vs  RT parallel: {rt.wall_clock_hours_parallel:.1f}h")
    print(f"  Async wall-clock: {ai.wall_clock_hours:.1f}h  vs  RT parallel: {rt.wall_clock_hours_parallel:.1f}h")
    print("-" * 72)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    rt = estimate_realtime()
    bt = estimate_batch_transform()
    ai = estimate_async_inference()
    print_comparison(rt, bt, ai)
