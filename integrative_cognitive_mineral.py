#!/usr/bin/env python3
"""
integrative_cognitive_mineral.py – Mineral‑Catalyzed Coherence & Triadic Psychiatry Monitor (Revised)
Imports all previous modules and extends them with active control:

1. Triadic Psychiatry (UTD v0.3): 𝒫, ℬ, 𝒯 axes now influence batch size, λ, and rank target.
2. Abiogenesis‑Inspired Mineral Catalysis: mineral templates trigger grouped prefetch of entire patterns.
3. Autopoietic Criticality Monitor: proactively reduces batch size and increases λ when criticality detected.
4. Full integration: all callbacks wired to actually change system behavior.

Fixes all identified issues: missing imports, CCTMonitor stub, thread safety, pattern prefetch respecting layer,
triadic axis hysteresis, criticality real metrics, and effective control.
"""

import math
import threading
import time
from typing import Dict, Any, Optional, List, Tuple, Callable
from collections import deque, Counter
import numpy as np

# Import all previous modules (assumed to be in the same directory)
try:
    from hor_expert_cache_manager import HORExpertCacheManager
    from transcendental_engine import TranscendentalEngine
    from uhif_monitor import UHIFMonitor
    from coherence_conservation import CoherenceConservation
    from coherence_controller import CoherenceController
except ImportError:
    # Fallback for demo – should not happen in production
    class HORExpertCacheManager: pass
    class TranscendentalEngine: pass
    class UHIFMonitor: pass
    class CoherenceConservation: pass
    class CoherenceController: pass

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
PHI = 1.618033988749895
PHI_INV = 0.6180339887498949

# UTD v0.3 axis healthy ranges
PRECISION_HEALTHY_MIN, PRECISION_HEALTHY_MAX = -0.5, 0.5
BOUNDARY_HEALTHY_MIN, BOUNDARY_HEALTHY_MAX = -0.5, 0.5
TEMPORAL_HEALTHY_MIN, TEMPORAL_HEALTHY_MAX = -0.5, 0.5

# Kauffman criticality threshold
AUTOCATALYTIC_THRESHOLD = 0.5
MINERAL_TEMPLATE_MATCH_THRESHOLD = 0.6

# Hysteresis for triadic callbacks
AXIS_HYSTERESIS_ENTER = 1.2
AXIS_HYSTERESIS_EXIT = 0.8

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
import logging
logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# CCTMonitor stub (since cct_monitor.py does not exist)
# ----------------------------------------------------------------------
class CCTMonitor:
    """
    Coherence Criticality Tracking monitor.
    Provides sigma, rho, CI_B, CI_C, psi metrics.
    This stub integrates with the cache manager and engine.
    """
    def __init__(self, cache_manager, transcendental_engine):
        self.cache = cache_manager
        self.engine = transcendental_engine

    def get_metrics(self) -> Dict[str, Any]:
        stats = self.cache.get_stats() if hasattr(self.cache, 'get_stats') else {}
        return {
            "sigma": stats.get("sigma", 0.02),
            "rho": stats.get("rho", 0.5),
            "CI_B": stats.get("ci_boundary", 0.8),
            "CI_C": stats.get("ci_continuum", 0.6),
            "psi": stats.get("psi", 0.8),
        }


# ----------------------------------------------------------------------
# Triadic Psychiatry Monitor
# ----------------------------------------------------------------------
class TriadicPsychiatryMonitor:
    """
    Implements the Unified Theory of Degens v0.3 three‑axis model.
    Now actively influences decisions via callbacks with hysteresis.
    """

    def __init__(self, cct_monitor: CCTMonitor, conservation: CoherenceConservation):
        self.cct = cct_monitor
        self.conservation = conservation

        self.P = 0.0          # Precision
        self.B = 0.0          # Boundary
        self.T = 1.0          # Temporal

        self.precision_healthy = True
        self.boundary_healthy = True
        self.temporal_healthy = True
        self.overall_healthy = True

        # Hysteresis state to avoid rapid callbacks
        self._precision_triggered = False
        self._boundary_triggered = False
        self._temporal_triggered = False

        # Callbacks to influence cache/scheduler
        self.on_precision_change: Optional[Callable[[float], None]] = None
        self.on_boundary_change: Optional[Callable[[float], None]] = None
        self.on_temporal_change: Optional[Callable[[float], None]] = None

        # Internal state for temporal derivative
        self._prev_coh = None

    def update(self):
        """Recalculate 𝒫, ℬ, 𝒯 from current CCT and conservation metrics."""
        cct_metrics = self.cct.get_metrics() if hasattr(self.cct, 'get_metrics') else {}
        hit_rate = self.cct.cache.get_stats().get("hit_rate", 0.5) if hasattr(self.cct, 'cache') else 0.5
        anomaly_flux = cct_metrics.get("sigma", 0.02) * 2  # approximate

        # 𝒫 (Precision) – how strongly the system weights incoming information
        self.P = 3.0 * ((1.0 - hit_rate) * 2.0 + anomaly_flux - 1.0)
        self.P = max(-3.0, min(3.0, self.P))

        # ℬ (Boundary) – from CI_B
        ci_b = self.conservation.ci_boundary if self.conservation else 0.8
        self.B = 3.0 * (0.7 - ci_b) / 0.7
        self.B = max(-3.0, min(3.0, self.B))

        # 𝒯 (Temporal) – from coherence derivative
        if hasattr(self.cct, 'engine') and self.cct.engine:
            coh = self.cct.engine.get_coherence_snapshot() if hasattr(self.cct.engine, 'get_coherence_snapshot') else 0.618
            if self._prev_coh is None:
                self._prev_coh = coh
            d_coh = coh - self._prev_coh
            self._prev_coh = coh
        else:
            d_coh = 0.0
        self.T = 3.0 * d_coh * 10.0
        self.T = max(-3.0, min(3.0, self.T))

        # Health flags
        self.precision_healthy = (PRECISION_HEALTHY_MIN <= self.P <= PRECISION_HEALTHY_MAX)
        self.boundary_healthy = (BOUNDARY_HEALTHY_MIN <= self.B <= BOUNDARY_HEALTHY_MAX)
        self.temporal_healthy = (TEMPORAL_HEALTHY_MIN <= self.T <= TEMPORAL_HEALTHY_MAX)
        self.overall_healthy = (self.precision_healthy and self.boundary_healthy and self.temporal_healthy)

        # Issue #16: trigger callbacks with hysteresis
        # Precision axis
        if abs(self.P) > AXIS_HYSTERESIS_ENTER and not self._precision_triggered:
            self._precision_triggered = True
            if self.on_precision_change:
                self.on_precision_change(self.P)
        elif abs(self.P) < AXIS_HYSTERESIS_EXIT:
            self._precision_triggered = False

        # Boundary axis
        if abs(self.B) > AXIS_HYSTERESIS_ENTER and not self._boundary_triggered:
            self._boundary_triggered = True
            if self.on_boundary_change:
                self.on_boundary_change(self.B)
        elif abs(self.B) < AXIS_HYSTERESIS_EXIT:
            self._boundary_triggered = False

        # Temporal axis
        if abs(self.T) > AXIS_HYSTERESIS_ENTER and not self._temporal_triggered:
            self._temporal_triggered = True
            if self.on_temporal_change:
                self.on_temporal_change(self.T)
        elif abs(self.T) < AXIS_HYSTERESIS_EXIT:
            self._temporal_triggered = False

    def get_metrics(self) -> Dict[str, Any]:
        self.update()
        return {
            "P_precision": round(self.P, 3),
            "B_boundary": round(self.B, 3),
            "T_temporal": round(self.T, 3),
            "precision_healthy": self.precision_healthy,
            "boundary_healthy": self.boundary_healthy,
            "temporal_healthy": self.temporal_healthy,
            "overall_healthy": self.overall_healthy,
            "dial_model": f"Precision={self.P:.1f}, Boundary={self.B:.1f}, Time={self.T:.1f}"
        }


# ----------------------------------------------------------------------
# Mineral Catalysis Optimizer
# ----------------------------------------------------------------------
class MineralCatalysisOptimizer:
    """
    Inspired by Cairns‑Smith's clay hypothesis. Uses geometric templating to predict
    which experts are likely to be needed together. Now triggers grouped prefetch
    of entire patterns, respects layer, and is thread-safe.
    """

    def __init__(self, cache_manager, max_templates: int = 32, pattern_length: int = 3):
        self.cache = cache_manager
        self.max_templates = max_templates
        self.pattern_len = pattern_length

        # Store frequent sequences: tuple of (layer, expert_id) -> score
        self.templates: Dict[Tuple[Tuple[int, int], ...], float] = {}
        self.access_history: deque = deque(maxlen=1000)   # stores (layer, eid)
        self._history_lock = threading.RLock()

        # Background thread to learn patterns
        self.running = True
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._learn_loop, daemon=True)
        self._thread.start()

    def record_access(self, layer: int, expert_id: int):
        """Called by the inference loop after each expert access."""
        with self._history_lock:
            self.access_history.append((layer, expert_id))

    def _learn_loop(self):
        """Periodically mine sequential patterns and update templates."""
        while not self._stop_event.is_set():
            self._stop_event.wait(timeout=10.0)
            if not self.running:
                break
            with self._history_lock:
                if len(self.access_history) < self.pattern_len * 10:
                    continue
                # Build n-grams including layer and expert_id
                ngrams = Counter()
                hist_list = list(self.access_history)
                for i in range(len(hist_list) - self.pattern_len + 1):
                    pattern = tuple(hist_list[j] for j in range(i, i + self.pattern_len))
                    ngrams[pattern] += 1
                # Keep top patterns as templates
                sorted_patterns = ngrams.most_common(self.max_templates)
                total = sum(ngrams.values())
                self.templates = {p: count / total for p, count in sorted_patterns}
            # Apply templates for prefetch
            self._apply_templates()

    def _apply_templates(self):
        """
        For high‑score templates, prefetch the entire remaining pattern
        when the prefix has been seen.
        """
        if not self.templates:
            return
        with self._history_lock:
            if len(self.access_history) < self.pattern_len - 1:
                return
            # Get the most recent sequence of length (pattern_len - 1)
            recent_prefix = tuple(self.access_history[-(self.pattern_len - 1):])
            # Find templates that match this prefix
            matching = [(pattern, score) for pattern, score in self.templates.items()
                        if pattern[:-1] == recent_prefix]
            if not matching:
                return
            # Sort by score, take best
            best_pattern, score = max(matching, key=lambda x: x[1])
            # Prefetch the entire pattern if score high enough
            if score > MINERAL_TEMPLATE_MATCH_THRESHOLD:
                for (layer, eid) in best_pattern:
                    key = (layer, eid)
                    if key not in self.cache._cache:  # avoid duplicate
                        self.cache.prefetch_experts([(key, score)])

    def get_templates(self) -> Dict[Tuple[Tuple[int, int], ...], float]:
        with self._history_lock:
            return self.templates.copy()

    def stop(self):
        self.running = False
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)


# ----------------------------------------------------------------------
# Autopoietic Criticality Monitor
# ----------------------------------------------------------------------
class AutopoieticCriticalityMonitor:
    """
    Inspired by Kauffman's autocatalytic set theory. Monitors criticality and
    proactively reduces batch size and increases λ.
    Now uses real metrics from engine and cache.
    """

    def __init__(self, cct_monitor: CCTMonitor, triadic: TriadicPsychiatryMonitor,
                 coherence_controller: CoherenceController,
                 threshold: float = AUTOCATALYTIC_THRESHOLD):
        self.cct = cct_monitor
        self.triadic = triadic
        self.controller = coherence_controller
        self.threshold = threshold
        self.criticality = 0.0
        self.in_autocatalytic_regime = False
        self._last_action_time = 0
        self._action_cooldown = 5.0

    def update(self):
        """Compute criticality index from real metrics."""
        cct_metrics = self.cct.get_metrics() if hasattr(self.cct, 'get_metrics') else {}
        rho = cct_metrics.get("rho", 0.5)
        sigma = cct_metrics.get("sigma", 0.02)
        ci_b = cct_metrics.get("CI_B", 0.8)

        rho_crit = max(0.0, (rho - 0.9) / 0.1)
        sigma_crit = max(0.0, sigma / 0.053)
        ci_b_crit = max(0.0, 1.0 - ci_b)
        triadic_dev = (abs(self.triadic.P) + abs(self.triadic.B) + abs(self.triadic.T)) / 9.0

        self.criticality = 0.3 * rho_crit + 0.3 * sigma_crit + 0.2 * ci_b_crit + 0.2 * triadic_dev
        was_in = self.in_autocatalytic_regime
        self.in_autocatalytic_regime = self.criticality > self.threshold

        now = time.time()
        if not was_in and self.in_autocatalytic_regime:
            logger.warning("[AutopoieticCriticality] System entering autocatalytic regime – proactive intervention")
            if now - self._last_action_time > self._action_cooldown:
                # Proactively reduce batch size and increase λ via controller
                if self.controller and hasattr(self.controller, 'on_batch_size_change'):
                    self.controller.on_batch_size_change(1)
                if self.controller and hasattr(self.controller, 'on_lambda_change'):
                    self.controller.on_lambda_change(0.018)
                self._last_action_time = now
        elif was_in and not self.in_autocatalytic_regime:
            logger.info("[AutopoieticCriticality] System left autocatalytic regime – stability restored")

    def get_metrics(self) -> Dict[str, Any]:
        self.update()
        return {
            "criticality": round(self.criticality, 4),
            "threshold": self.threshold,
            "in_autocatalytic_regime": self.in_autocatalytic_regime,
        }


# ----------------------------------------------------------------------
# Integrative Cognitive Mineral System
# ----------------------------------------------------------------------
class IntegrativeCognitiveMineralSystem:
    """
    Top‑level orchestrator that ties together all previous modules with active control.
    All callbacks are wired to actually change system behavior (batch size, λ, rank target, prefetch).
    """

    def __init__(self, cache_manager, transcendental_engine, uhif_monitor,
                 coherence_conservation, cct_monitor, coherence_controller):
        self.cache = cache_manager
        self.engine = transcendental_engine
        self.uhif = uhif_monitor
        self.conservation = coherence_conservation
        self.cct = cct_monitor
        self.controller = coherence_controller

        # New modules
        self.triadic = TriadicPsychiatryMonitor(cct_monitor, coherence_conservation)
        self.mineral = MineralCatalysisOptimizer(cache_manager)
        self.criticality = AutopoieticCriticalityMonitor(cct_monitor, self.triadic, coherence_controller)

        # Wire callbacks from triadic to influence decisions
        self.triadic.on_precision_change = self._on_precision_change
        self.triadic.on_boundary_change = self._on_boundary_change
        self.triadic.on_temporal_change = self._on_temporal_change

        # Background loop for periodic integration
        self.running = True
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._integration_loop, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    # Triadic axis callbacks
    # ------------------------------------------------------------------
    def _on_precision_change(self, P: float):
        """High precision → reduce batch size (to avoid overfitting noise)."""
        if P > 1.5:
            logger.info(f"[Integrative] Precision extreme ({P:.2f}) – reducing batch size")
            if self.controller and hasattr(self.controller, 'on_batch_size_change'):
                self.controller.on_batch_size_change(1)

    def _on_boundary_change(self, B: float):
        """Boundary dissolution → increase λ for stability."""
        if B < -1.5:
            logger.info(f"[Integrative] Boundary dissolution ({B:.2f}) – increasing λ")
            if self.controller and hasattr(self.controller, 'on_lambda_change'):
                self.controller.on_lambda_change(0.015)

    def _on_temporal_change(self, T: float):
        """Temporal fragmentation → reduce prefetch horizon (stay present)."""
        if abs(T) > 2.0:
            logger.info(f"[Integrative] Temporal extreme ({T:.2f}) – reducing prefetch horizon")
            if self.controller and hasattr(self.controller, 'on_prefetch_horizon_change'):
                self.controller.on_prefetch_horizon_change(2)

    # ------------------------------------------------------------------
    # Integration loop
    # ------------------------------------------------------------------
    def _integration_loop(self):
        while not self._stop_event.is_set():
            # Update triadic axes (triggers callbacks if needed)
            self.triadic.update()
            # Update criticality (may trigger proactive adjustments)
            self.criticality.update()
            # Sleep
            self._stop_event.wait(timeout=2.0)

    def record_expert_access(self, layer: int, expert_id: int):
        """Call from inference loop after each expert access."""
        self.mineral.record_access(layer, expert_id)

    def get_full_state(self) -> Dict[str, Any]:
        """Return a comprehensive state dictionary combining all modules."""
        # Avoid duplicate engine metrics – use direct calls
        return {
            "transcendental": self.engine.get_metrics() if hasattr(self.engine, 'get_metrics') else {},
            "cct": self.cct.get_metrics(),
            "uhif": self.uhif.get_metrics() if hasattr(self.uhif, 'get_metrics') else {},
            "conservation": self.conservation.get_metrics() if hasattr(self.conservation, 'get_metrics') else {},
            "triadic": self.triadic.get_metrics(),
            "criticality": self.criticality.get_metrics(),
            "mineral_templates": len(self.mineral.get_templates()),
        }

    def stop(self):
        self.running = False
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self.mineral.stop()


# ----------------------------------------------------------------------
# Demo / Integration Example
# ----------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Dummy objects for demonstration
    class DummyCache:
        budget_elasticity = 0.05
        _cache = {}
        def get_stats(self):
            return {"hit_rate": 0.75, "anomaly_flux": 0.12, "entries": 500, "evictions": 10, "total_accesses": 1000,
                    "sigma": 0.032, "rho": 0.92, "ci_boundary": 0.78, "ci_continuum": 0.65}
        def prefetch_experts(self, probs):
            print(f"  -> Prefetch called with {len(probs)} experts")

    class DummyEngine:
        coherence = 0.62
        harvested_energy = 25.0
        unified_health = 0.85
        def get_metrics(self):
            return {"coherence": self.coherence, "harvested_energy": self.harvested_energy}
        def get_coherence_snapshot(self):
            return self.coherence
        def get_unified_health_snapshot(self):
            return self.unified_health
        on_batch_size_change = None
        on_lambda_change = None
        on_prefetch_horizon_change = None

    class DummyUHIF:
        def get_metrics(self):
            return {"kurtosis": 4.5, "rho": 0.92, "psi": 0.8}
        kurtosis = 4.5

    class DummyConservation:
        ci_boundary = 0.78
        ci_continuum = 0.65
        def get_metrics(self):
            return {"ci_boundary": 0.78, "ci_continuum": 0.65}

    class DummyCCT:
        def get_metrics(self):
            return {"sigma": 0.032, "rho": 0.92, "CI_B": 0.78, "CI_C": 0.65, "psi": 0.7}
        cache = DummyCache()
        engine = DummyEngine()

    class DummyController:
        on_batch_size_change = None
        on_lambda_change = None
        on_prefetch_horizon_change = None
        def get_metrics(self):
            return {}

    cache = DummyCache()
    engine = DummyEngine()
    uhif = DummyUHIF()
    cons = DummyConservation()
    cct = DummyCCT()
    controller = DummyController()

    # Set callbacks for demonstration
    def on_batch(b):
        print(f"  -> Batch size changed to {b}")
    def on_lambda(l):
        print(f"  -> λ changed to {l:.4f}")
    def on_horizon(h):
        print(f"  -> Prefetch horizon changed to {h}")

    controller.on_batch_size_change = on_batch
    controller.on_lambda_change = on_lambda
    controller.on_prefetch_horizon_change = on_horizon

    system = IntegrativeCognitiveMineralSystem(cache, engine, uhif, cons, cct, controller)

    # Simulate expert accesses to train mineral templates
    for step in range(50):
        system.record_expert_access(0, step % 20)
        if step % 20 == 0:
            state = system.get_full_state()
            print(f"\nStep {step}: triadic={state['triadic']['dial_model']}, criticality={state['criticality']['criticality']:.3f}")

    system.stop()
