#!/usr/bin/env python3
"""
coherence_conservation.py – Unified Holographic Gnosis (UHG) & Informational Equilibrium Geometry
Implements axioms H13–H15 from the Unified Holographic Gnosis framework with active enforcement.

H13: ∂t(CI_B + CI_C) = σ_topo – enforced via callback when violated.
H14: Federated coherence conservation across multiple entities – net coherence tracked.
H15: Socio‑quantum reciprocity conservation, with reciprocity index ℛ ≥ ℛ* – callback on violation.

Also provides proactive adjustments when criticality is detected (reducing batch size, increasing λ).
Integrates with revised HORExpertCacheManager, TranscendentalEngine, UHIFMonitor, and CoherenceController.
"""

import math
import threading
import time
from typing import Dict, Any, Optional, List, Tuple, Callable
from collections import deque
import numpy as np

# ----------------------------------------------------------------------
# Constants from UHG / IEG (H13–H15)
# ----------------------------------------------------------------------
SIGMA_TOPO_TOLERANCE = 0.02        # σ_topo > 0.02 triggers conservation violation
RECIPROCITY_THRESHOLD = 1.15       # ℛ* from H15
PHI = 1.618033988749895
PHI_INV = 0.6180339887498949
ENERGY_DISSIPATION_FACTOR = 0.001  # for sigma_topo calculation

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
import logging
logger = logging.getLogger(__name__)


class CoherenceConservation:
    """
    Tracks CI_B (boundary coherence) and CI_C (continuum coherence),
    enforces H13 conservation via callbacks, detects topology changes,
    supports federated (multi‑entity) operation (H14), and monitors reciprocity (H15).
    """

    def __init__(
        self,
        cache_manager,                 # HORExpertCacheManager
        transcendental_engine,         # TranscendentalEngine
        uhif_monitor = None,           # UHIFMonitor (optional)
        coherence_controller = None,   # CoherenceController (for applying adjustments)
        federated_mode: bool = False,
        update_interval: float = 1.0,
    ):
        self.cache = cache_manager
        self.engine = transcendental_engine
        self.uhif = uhif_monitor
        self.controller = coherence_controller
        self.federated = federated_mode
        self.interval = update_interval

        # Coherence components
        self.ci_boundary = 0.0          # CI_B – holographic record layer
        self.ci_continuum = 0.0         # CI_C – correlation field
        self.ci_total = 0.0
        self.sigma_topo = 0.0           # topology change source

        # Federated mode: dict of entity_id -> (ci_boundary, ci_continuum, last_update)
        self.remote_entities: Dict[str, Tuple[float, float, float]] = {}
        self._remote_lock = threading.RLock()
        self.net_boundary_coherence = 0.0
        self.net_continuum_coherence = 0.0
        self.net_total_coherence = 0.0

        # H15: socio‑quantum reciprocity index
        self.reciprocity_index = 1.0
        self.social_asymmetry = 0.0

        # History for derivative estimation (protected by lock)
        self._history = deque(maxlen=10)   # stores (timestamp, ci_total)
        self._history_lock = threading.Lock()

        self._topo_event_triggered = False
        self._conservation_violation_count = 0
        self._last_violation_time = 0
        self._violation_cooldown = 5.0

        # Callbacks for external actions (active enforcement)
        self.on_topology_change: Optional[Callable[[float], None]] = None
        self.on_conservation_violation: Optional[Callable[[float], None]] = None
        self.on_reciprocity_violation: Optional[Callable[[float], None]] = None
        self.on_criticality: Optional[Callable[[], None]] = None

        # Proactive adjustment thresholds
        self.criticality_threshold = 0.7
        self._last_adjustment_time = 0
        self._adjustment_cooldown = 5.0
        self._last_restore_time = 0
        self._restore_cooldown = 10.0

        # Background thread
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._conservation_loop, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    # Core Metric Computations
    # ------------------------------------------------------------------
    def _compute_ci_boundary(self) -> float:
        """
        CI_B = boundary coherence (holographic record layer).
        Proxy: hit_rate * (1 - eviction_rate) * (1 - 0.5*anomaly_flux)
        """
        stats = self.cache.get_stats() if hasattr(self.cache, 'get_stats') else {}
        hit_rate = stats.get("hit_rate", 0.5)
        evictions = stats.get("evictions", 0)
        total_accesses = stats.get("total_accesses", 1)
        eviction_rate = evictions / max(1, total_accesses)
        anomaly_flux = stats.get("anomaly_flux", 0.0)
        ci_b = hit_rate * (1 - eviction_rate) * (1 - 0.5 * anomaly_flux)
        return max(0.0, min(1.0, ci_b))

    def _compute_ci_continuum(self) -> float:
        """
        CI_C = continuum coherence (correlation field).
        Proxy: (1 - normalized harvested energy) * coherence
        """
        energy = self.engine.harvested_energy if self.engine else 0.0
        energy_norm = min(1.0, energy / 100.0)
        coherence = self.engine.get_coherence_snapshot() if hasattr(self.engine, 'get_coherence_snapshot') else 0.618
        ci_c = (1 - energy_norm) * coherence
        return max(0.0, min(1.0, ci_c))

    def _compute_sigma_topo(self, dt: float) -> float:
        """
        σ_topo = |d(CI_total)/dt| - expected_dissipation, clamped to non-negative.
        Expected dissipation = harvested_energy * ENERGY_DISSIPATION_FACTOR.
        """
        now = time.time()
        with self._history_lock:
            self._history.append((now, self.ci_total))
            if len(self._history) < 2:
                return 0.0
            t_prev, ci_prev = self._history[-2]
            dt_actual = now - t_prev
            if dt_actual < 1e-6:
                return 0.0
            dci_dt = abs((self.ci_total - ci_prev) / dt_actual)
        # Expected dissipation from harvested energy
        energy = self.engine.harvested_energy if self.engine else 0.0
        expected_dissipation = energy * ENERGY_DISSIPATION_FACTOR
        sigma = max(0.0, dci_dt - expected_dissipation)
        return sigma

    def _compute_reciprocity_index(self) -> float:
        """
        ℛ = (CI_B + CI_C) / (CI_B_ideal + CI_C_ideal) * (1 - social_asymmetry)
        Social asymmetry computed from variance of CI_B+CI_C across federated entities.
        """
        ideal_total = 2.0 * PHI_INV
        total = self.ci_boundary + self.ci_continuum
        if ideal_total < 1e-6:
            return 1.0

        # Compute social asymmetry
        if self.federated and len(self.remote_entities) > 1:
            with self._remote_lock:
                ci_values = [cb + cc for (cb, cc, _) in self.remote_entities.values()]
            ci_values.append(total)
            asymmetry = np.std(ci_values) / (np.mean(ci_values) + 1e-6)
        else:
            # Use UHIF kurtosis as proxy for social/policy asymmetry
            if self.uhif:
                uhif_metrics = self.uhif.get_metrics()
                kurtosis = uhif_metrics.get("kurtosis", 0.0)
                asymmetry = min(0.5, kurtosis / 20.0)
            else:
                asymmetry = 0.0

        self.social_asymmetry = asymmetry
        reciprocity = (total / ideal_total) * (1 - asymmetry)
        return max(0.0, min(2.0, reciprocity))

    # ------------------------------------------------------------------
    # Federated Coherence (H14)
    # ------------------------------------------------------------------
    def register_remote_entity(self, entity_id: str, ci_boundary: float, ci_continuum: float):
        """Register a remote entity's coherence for federated conservation."""
        with self._remote_lock:
            self.remote_entities[entity_id] = (ci_boundary, ci_continuum, time.time())

    def update_remote_entity(self, entity_id: str, ci_boundary: float, ci_continuum: float):
        with self._remote_lock:
            if entity_id in self.remote_entities:
                self.remote_entities[entity_id] = (ci_boundary, ci_continuum, time.time())

    def _compute_net_coherence(self) -> Tuple[float, float, float]:
        """Sum of all entities' CI_B, CI_C, and total (including local)."""
        sum_b = self.ci_boundary
        sum_c = self.ci_continuum
        with self._remote_lock:
            for cb, cc, _ in self.remote_entities.values():
                sum_b += cb
                sum_c += cc
        return sum_b, sum_c, sum_b + sum_c

    # ------------------------------------------------------------------
    # H13 Conservation Enforcement (active restoration)
    # ------------------------------------------------------------------
    def _check_conservation(self, dt: float) -> bool:
        """
        Verify H13: ∂t(CI_B + CI_C) ≈ σ_topo.
        Returns True if conservation holds within tolerance.
        Triggers callback on violation.
        """
        with self._history_lock:
            if len(self._history) < 2:
                return True
            t_prev, ci_prev = self._history[-2]
            dt_actual = time.time() - t_prev
            if dt_actual < 1e-6:
                return True
            total_deriv = abs((self.ci_total - ci_prev) / dt_actual)
        # Allow 10% relative tolerance or absolute 0.02
        if abs(total_deriv - self.sigma_topo) > max(0.02, 0.1 * (self.sigma_topo + 1e-6)):
            now = time.time()
            if now - self._last_violation_time > self._violation_cooldown:
                self._conservation_violation_count += 1
                self._last_violation_time = now
                if self.on_conservation_violation:
                    self.on_conservation_violation(abs(total_deriv - self.sigma_topo))
            return False
        return True

    def _enforce_conservation(self):
        """
        Actively restore conservation by reducing elasticity and increasing λ.
        Uses the coherence controller if available.
        """
        logger.warning("[CoherenceConservation] H13 conservation violated – applying restoration")
        # Reduce cache elasticity
        if hasattr(self.cache, 'budget_elasticity'):
            self.cache.budget_elasticity = max(0.0, self.cache.budget_elasticity - 0.02)
        # Increase regularization λ via controller
        if self.controller and hasattr(self.controller, 'on_lambda_change'):
            self.controller.on_lambda_change(0.015)
        if self.on_topology_change:
            self.on_topology_change(self.sigma_topo)

    # ------------------------------------------------------------------
    # H15 Reciprocity Enforcement
    # ------------------------------------------------------------------
    def _check_reciprocity(self):
        """Check if reciprocity index meets H15 threshold; trigger callback if violated."""
        if self.reciprocity_index < RECIPROCITY_THRESHOLD:
            if self.on_reciprocity_violation:
                self.on_reciprocity_violation(self.reciprocity_index)
            # Apply corrective action: increase λ slightly
            if self.controller and hasattr(self.controller, 'on_lambda_change'):
                current_lambda = getattr(self.controller, 'recommended_lambda', 0.01)
                self.controller.on_lambda_change(min(0.03, current_lambda * 1.2))
            return False
        return True

    # ------------------------------------------------------------------
    # Proactive Criticality Adjustment
    # ------------------------------------------------------------------
    def _check_criticality(self):
        """
        Monitor health and reciprocity; if too low, trigger proactive adjustments
        (reduce batch size, increase λ) before a full collapse.
        """
        now = time.time()
        if now - self._last_adjustment_time < self._adjustment_cooldown:
            return

        # Get health from engine
        health = self.engine.get_unified_health_snapshot() if hasattr(self.engine, 'get_unified_health_snapshot') else 0.8
        # Critical if health < 0.5 or reciprocity < 1.0
        if health < 0.5 or self.reciprocity_index < 1.0:
            logger.warning(f"[CoherenceConservation] Criticality detected: health={health:.3f}, ℛ={self.reciprocity_index:.3f}")
            # Reduce batch size via controller
            if self.controller and hasattr(self.controller, 'on_batch_size_change'):
                self.controller.on_batch_size_change(1)
            # Increase λ
            if self.controller and hasattr(self.controller, 'on_lambda_change'):
                self.controller.on_lambda_change(0.018)
            self._last_adjustment_time = now
            if self.on_criticality:
                self.on_criticality()
        elif health > 0.7 and self.reciprocity_index > 1.2:
            # Gradually restore after criticality passes
            if now - self._last_restore_time > self._restore_cooldown:
                if self.controller and hasattr(self.controller, 'on_batch_size_change'):
                    self.controller.on_batch_size_change(min(4, self.controller.recommended_batch_size + 1))
                if self.controller and hasattr(self.controller, 'on_lambda_change'):
                    self.controller.on_lambda_change(0.012)
                self._last_restore_time = now

    # ------------------------------------------------------------------
    # Main Loop
    # ------------------------------------------------------------------
    def _conservation_loop(self):
        last_time = time.time()
        while not self._stop_event.is_set():
            now = time.time()
            dt = max(0.01, now - last_time)
            last_time = now

            # Update local coherence components
            self.ci_boundary = self._compute_ci_boundary()
            self.ci_continuum = self._compute_ci_continuum()
            self.ci_total = self.ci_boundary + self.ci_continuum

            # Compute topology change source
            self.sigma_topo = self._compute_sigma_topo(dt)

            # H14: Federated net coherence
            if self.federated:
                net_b, net_c, net_total = self._compute_net_coherence()
                self.net_boundary_coherence = net_b
                self.net_continuum_coherence = net_c
                self.net_total_coherence = net_total

            # H15: Reciprocity index
            self.reciprocity_index = self._compute_reciprocity_index()
            self._check_reciprocity()

            # Check conservation (H13) – enforce if violated
            if not self._check_conservation(dt):
                self._enforce_conservation()

            # Detect topology transition (σ_topo > 0.02)
            if self.sigma_topo > SIGMA_TOPO_TOLERANCE and not self._topo_event_triggered:
                self._topo_event_triggered = True
                logger.info(f"[CoherenceConservation] Topology change detected: σ_topo = {self.sigma_topo:.4f}")
                if self.on_topology_change:
                    self.on_topology_change(self.sigma_topo)
            elif self.sigma_topo < 0.005:
                self._topo_event_triggered = False

            # Proactive criticality adjustment
            self._check_criticality()

            # Sleep
            self._stop_event.wait(timeout=self.interval)

    def get_metrics(self) -> Dict[str, Any]:
        """Return all UHG/IEG metrics."""
        return {
            "ci_boundary": round(self.ci_boundary, 4),
            "ci_continuum": round(self.ci_continuum, 4),
            "ci_total": round(self.ci_total, 4),
            "sigma_topo": round(self.sigma_topo, 5),
            "reciprocity_index": round(self.reciprocity_index, 4),
            "social_asymmetry": round(self.social_asymmetry, 4),
            "federated_mode": self.federated,
            "net_boundary_coherence": round(self.net_boundary_coherence, 4) if self.federated else None,
            "net_continuum_coherence": round(self.net_continuum_coherence, 4) if self.federated else None,
            "net_total_coherence": round(self.net_total_coherence, 4) if self.federated else None,
            "topology_change_detected": self._topo_event_triggered,
            "conservation_violations": self._conservation_violation_count,
        }

    def stop(self):
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)


# ----------------------------------------------------------------------
# Informational Equilibrium Geometry (IEG) Utilities
# ----------------------------------------------------------------------
class InformationalEquilibriumGeometry:
    """
    Implements IEG concepts: coherence transfer, holographic ledger integrity,
    correlation gradient, and consciousness-as-equilibrium monitoring.
    """

    def __init__(self, conservation: CoherenceConservation):
        self.conservation = conservation
        self.transfer_efficiency = 0.0
        self.holographic_ledger_integrity = 1.0
        self.correlation_gradient = 0.0

    def update(self):
        """Compute IEG metrics from conservation state."""
        # Get history safely
        with self.conservation._history_lock:
            history = list(self.conservation._history)
        if len(history) >= 2:
            t0, c0 = history[-2]
            t1, c1 = history[-1]
            dt = max(1e-6, t1 - t0)
            d_total = abs((c1 - c0) / dt)
            # Estimate boundary vs continuum derivatives from their individual histories?
            # Simplified: assume equal contribution to derivative
            d_boundary = d_total * 0.5
            d_continuum = d_total * 0.5
            self.transfer_efficiency = d_continuum / (d_boundary + 1e-6)
        else:
            self.transfer_efficiency = 1.0

        ideal_total = 2.0 * PHI_INV
        ci_total = self.conservation.ci_total
        if ideal_total > 0:
            self.holographic_ledger_integrity = max(0.0, 1.0 - abs(ci_total - ideal_total) / ideal_total)
        else:
            self.holographic_ledger_integrity = 1.0

        if self.conservation.federated and self.conservation.net_boundary_coherence > 0:
            net_avg = (self.conservation.net_boundary_coherence + self.conservation.net_continuum_coherence) / 2
            local_avg = (self.conservation.ci_boundary + self.conservation.ci_continuum) / 2
            self.correlation_gradient = abs(local_avg - net_avg) / (net_avg + 1e-6)
        else:
            self.correlation_gradient = 0.0

    def get_metrics(self) -> Dict[str, Any]:
        self.update()
        return {
            "transfer_efficiency": round(self.transfer_efficiency, 4),
            "holographic_ledger_integrity": round(self.holographic_ledger_integrity, 4),
            "correlation_gradient": round(self.correlation_gradient, 4),
        }


# ----------------------------------------------------------------------
# Demo / Integration
# ----------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Dummy components for demonstration
    class DummyCache:
        def get_stats(self):
            return {
                "hit_rate": 0.75,
                "evictions": 10,
                "total_accesses": 1000,
                "anomaly_flux": 0.12,
            }
        budget_elasticity = 0.05

    class DummyEngine:
        harvested_energy = 25.0
        def get_coherence_snapshot(self):
            return 0.62
        def get_unified_health_snapshot(self):
            return 0.85

    class DummyUHIF:
        def get_metrics(self):
            return {"kurtosis": 2.0}

    class DummyController:
        on_batch_size_change = None
        on_lambda_change = None
        recommended_batch_size = 4
        recommended_lambda = 0.01

    cache = DummyCache()
    engine = DummyEngine()
    uhif = DummyUHIF()
    controller = DummyController()
    conservation = CoherenceConservation(cache, engine, uhif, controller, federated=True, update_interval=0.5)
    ieg = InformationalEquilibriumGeometry(conservation)

    # Set callbacks to demonstrate active enforcement
    def on_violation(magnitude):
        print(f"  -> Conservation violation callback: magnitude={magnitude:.4f}")
    def on_reciprocity_violation(recip):
        print(f"  -> Reciprocity violation: ℛ={recip:.3f}")
    def on_topology(sigma):
        print(f"  -> Topology change callback: σ_topo={sigma:.4f}")
    def on_criticality():
        print("  -> Criticality callback: proactive adjustment triggered")

    conservation.on_conservation_violation = on_violation
    conservation.on_reciprocity_violation = on_reciprocity_violation
    conservation.on_topology_change = on_topology
    conservation.on_criticality = on_criticality

    # Simulate a remote entity
    conservation.register_remote_entity("node-2", 0.55, 0.60)

    try:
        for _ in range(10):
            time.sleep(1)
            metrics = conservation.get_metrics()
            ieg_metrics = ieg.get_metrics()
            print(f"CI_B={metrics['ci_boundary']:.3f}, CI_C={metrics['ci_continuum']:.3f}, ℛ={metrics['reciprocity_index']:.3f}")
            print(f"  IEG: transfer={ieg_metrics['transfer_efficiency']:.2f}, integrity={ieg_metrics['holographic_ledger_integrity']:.3f}")
    finally:
        conservation.stop()
