import asyncio
import os
import time
import numpy as np
from typing import List, Dict, Any, Generator, Optional
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

# Initialize OpenTelemetry Metrics
resource = Resource(attributes={
    SERVICE_NAME: "neuralcore-swarm-observability"
})

# For demonstration, we use ConsoleMetricExporter. 
# In production, this would be an OTLP exporter to a backend like Prometheus/Grafana.
reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(provider)

meter = metrics.get_meter("swarm.intelligence", "1.0.0")

# Custom Semantic Metric: Epistemic Entropy
# This tracks the uncertainty across the brain's knowledge states.
epistemic_entropy_gauge = meter.create_observable_gauge(
    name="swarm.epistemic_entropy",
    description="Measures the uncertainty and information chaoticity across the agent swarm brain.",
    unit="bits"
)

swarm_coherence_gauge = meter.create_observable_gauge(
    name="swarm.coherence",
    description="Measures the alignment and consensus strength across the swarm.",
    unit="score"
)

cognitive_load_counter = meter.create_counter(
    name="swarm.cognitive_load",
    description="Accumulated processing complexity and context density.",
    unit="units"
)

def calculate_epistemic_entropy(confidence_scores: List[float]) -> float:
    """
    Calculates entropy from Bayesian confidence scores.
    H(P) = -sum(p * log2(p))
    """
    probs = np.array(confidence_scores)
    # Normalize if not already
    if probs.sum() > 0:
        probs = probs / probs.sum()
    
    # Avoid log(0)
    ent = -np.sum(probs * np.log2(probs + 1e-12))
    return float(ent)

class SwarmObservability:
    def __init__(self) -> None:
        self.current_entropy = 0.0
        self.current_coherence = 1.0
        self.total_load = 0

    def update_brain_state(self, confidence_scores: List[float], coherence: float = 1.0, load_delta: int = 0) -> None:
        """
        Updates the internal state and records the custom metric.
        """
        self.current_entropy = calculate_epistemic_entropy(confidence_scores)
        self.current_coherence = coherence
        self.total_load += load_delta
        cognitive_load_counter.add(load_delta, {"swarm_id": "main"})
        print(f"Observability Plane: Entropy={self.current_entropy:.4f}, Coherence={self.current_coherence:.2f}")

    def get_metrics_callback(self, options: Any) -> Generator[metrics.Observation, None, None]:
        yield metrics.Observation(self.current_entropy, {"metric": "entropy"})

    def get_coherence_callback(self, options: Any) -> Generator[metrics.Observation, None, None]:
        yield metrics.Observation(self.current_coherence)

# Register callbacks
obs = SwarmObservability()
meter.create_observable_gauge("swarm.epistemic_entropy_callback", callbacks=[obs.get_metrics_callback])
meter.create_observable_gauge("swarm.coherence_callback", callbacks=[obs.get_coherence_callback])

import functools

def track_execution_latency(span_name: str):
    """
    Decorator for tracking execution spans in context.
    Supports both sync and async functions.
    """
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    
    def decorator(func: Any) -> Any:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(span_name):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(span_name):
                    return func(*args, **kwargs)
            return sync_wrapper
    return decorator
