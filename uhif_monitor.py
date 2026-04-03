#!/usr/bin/env python3
"""
coherence_controller.py – Scientific‑Grade Golden Attractor & Sophia Point Lock (Revised)
Implements core equations from the 48+ novel transcendental frameworks with active control.

- Master coherence evolution: ∂G/∂t = D∇²G + αG(1 - G/K) + β sin(2πG/φ) + γΣΩ_i(G) + ξ(t)
- Innovation score: I = 0.3N + 0.25A + 0.2Π + 0.15(1-C) + 0.1(E_p/300)
- Phase transition detection: |C-0.618|<0.02 AND Π>1.8 → trigger callbacks
- Prefetch horizon: H = ceil(φ * log₂(harvested_energy + 2)) – actively applied
- Adaptive λ and rank target via emergency callbacks
- H13 conservation enforcement (via callbacks to CoherenceConservation)
- H14/H15 federation and reciprocity callbacks wired

All quantities derived from cache manager and transcendental engine.
"""

import math
import threading
import time
from typing import Dict, Any, Optional, Callable
from collections import deque
import numpy as np

# ----------------------------------------------------------------------
# Constants from the Sophia‑Gnostic framework
# ----------------------------------------------------------------------
PHI = (1 + 5**0.5) / 2
SOPHIA_POINT = 1 / PHI
PHI_SQ = PHI * PHI
PHI_4 = PHI ** 4

# Phase transition thresholds
SOPHIA_TOLERANCE = 0.02
PARADOX_THRESHOLD = 1.8

# Innovation score weights
WEIGHT_NOVELTY = 0.3
WEIGHT_ALIENNESS = 0.25
WEIGHT_PARADOX = 0.2
WEIGHT_COHERENCE = 0.15
WEIGHT_ENTROPIC = 0.1

# Master equation parameters
D_DIFFUSION = 0.1
ALPHA_GROWTH = 0.12
BETA_DRIVING = 0.3
GAMMA_COUPLING = 0.47


class CoherenceController:
    """
    High‑level controller that drives the system toward the Sophia point (C = φ⁻¹)
    by adjusting:
        - Prefetch horizon (H) – actively applied via callback
        - Cache budget elasticity (λ proxy) – via callback
        - Batch size – via callback
    It also enforces H13–H15 conservation via callbacks to CoherenceConservation.
    """

    def __init__(
        self,
        transcendental_engine,          # TranscendentalEngine instance
        cache_manager,                  # HORExpertCacheManager instance
        update_interval: float = 1.0,
        enable_autotuning: bool = True,
    ):
        self.engine = transcendental_engine
        self.cache = cache_manager
        self.interval = update_interval
        self.autotune = enable_autotuning

        # State variables
        self.innovation_score = 0.0
        self.paradox_intensity = 1.0
        self.novelty = 0.5
        self.alienness = 5.0
        self.entropic_potential = 250.0

        # Control outputs (actively applied via callbacks)
        self.prefetch_horizon = 2          # Eq 39 – will be updated and applied
        self.recommended_batch_size = 1
        self.recommended_elasticity = 0.0
        self.recommended_lambda = 0.01     # for UHIF/emergency protocols
        self.recommended_rank_target = 30.0  # r target (0.93 * d_s)

        # Phase transition and lock flags
        self.phase_transition_occurred = False
        self.sophia_locked = False

        # History for smoothing
        self.coherence_history = deque(maxlen=10)
        self._last_emergency_time = 0
        self._emergency_cooldown = 5.0   # seconds

        # Callbacks for external systems (must be set by the integrator)
        self.on_prefetch_horizon_change: Optional[Callable[[int], None]] = None
        self.on_batch_size_change: Optional[Callable[[int], None]] = None
        self.on_elasticity_change: Optional[Callable[[float], None]] = None
        self.on_lambda_change: Optional[Callable[[float], None]] = None
        self.on_rank_target_change: Optional[Callable[[float], None]] = None

        # Conservation callbacks (for H13–H15)
        self.on_conservation_violation: Optional[Callable[[], None]] = None
        self.on_reciprocity_violation: Optional[Callable[[float], None]] = None

        # Background thread
        self.running = True
        self._thread = threading.Thread(target=self._control_loop, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    # Core equations implementation
    # ------------------------------------------------------------------
    def _compute_paradox_intensity(self, cache_stats: Dict) -> float:
        """Π from anomaly flux and hit rate (range 1.0–3.0)."""
        anomaly_flux = cache_stats.get("anomaly_flux", 0.0)
        hit_rate = cache_stats.get("hit_rate", 0.5)
        paradox = 1.0 + 5.0 * anomaly_flux
        if hit_rate < 0.4:
            paradox += 0.5
        return min(3.0, max(1.0, paradox))

    def _compute_novelty(self, cache_stats: Dict) -> float:
        """Novelty N from eviction rate."""
        evictions = cache_stats.get("evictions", 0)
        total_accesses = cache_stats.get("total_accesses", 1)
        eviction_rate = evictions / max(1, total_accesses)
        return min(1.5, max(0.0, eviction_rate * 10.0))

    def _compute_alienness(self, cache_stats: Dict) -> float:
        """Alienness A from anomaly flux."""
        anomaly_flux = cache_stats.get("anomaly_flux", 0.0)
        return 5.0 + 10.0 * anomaly_flux

    def _compute_entropic_potential(self, cache_stats: Dict) -> float:
        """Entropic potential E_p from used GB and hit rate."""
        used_gb = cache_stats.get("used_gb", 0.0)
        hit_rate = cache_stats.get("hit_rate", 0.5)
        return 200.0 + used_gb * 20.0 * (1.0 - abs(hit_rate - 0.5) * 2)

    def _compute_innovation_score(self, cache_stats: Dict) -> float:
        """I = 0.3N + 0.25A + 0.2Π + 0.15(1-C) + 0.1(E_p/300)"""
        N = self._compute_novelty(cache_stats)
        A = self._compute_alienness(cache_stats)
        Pi = self._compute_paradox_intensity(cache_stats)
        C = self.engine.coherence
        Ep = self._compute_entropic_potential(cache_stats)
        I = (WEIGHT_NOVELTY * N +
             WEIGHT_ALIENNESS * (A / 10.0) +
             WEIGHT_PARADOX * ((Pi - 1.0) / 2.0) +
             WEIGHT_COHERENCE * (1.0 - C) +
             WEIGHT_ENTROPIC * (Ep / 300.0))
        return max(0.0, min(1.0, I))

    def _master_coherence_prediction(self, dt: float) -> float:
        """
        Master equation prediction (not applied, just for logging/diagnostics).
        dC/dt = D∇²C + αC(1 - C/K) + β sin(2πC/φ) + γ·I + ξ
        """
        C = self.engine.coherence
        K = 1.0 / SOPHIA_POINT   # ~1.618
        laplacian = (SOPHIA_POINT - C) * 0.1
        logistic = ALPHA_GROWTH * C * (1 - C / K)
        periodic = BETA_DRIVING * math.sin(2 * math.pi * C / PHI)
        coupling = GAMMA_COUPLING * self.innovation_score
        noise = np.random.normal(0, 0.01)
        dC_dt = D_DIFFUSION * laplacian + logistic + periodic + coupling + noise
        return C + dC_dt * dt

    def _detect_phase_transition(self, cache_stats: Dict) -> bool:
        """Phase transition when |C - 0.618| < 0.02 AND Π > 1.8."""
        C = self.engine.coherence
        Pi = self._compute_paradox_intensity(cache_stats)
        near_sophia = abs(C - SOPHIA_POINT) < SOPHIA_TOLERANCE
        high_paradox = Pi > PARADOX_THRESHOLD
        if near_sophia and high_paradox and not self.sophia_locked:
            self.sophia_locked = True
            self.phase_transition_occurred = True
            return True
        if abs(C - SOPHIA_POINT) > 0.05:
            self.sophia_locked = False
        return False

    def _update_prefetch_horizon(self):
        """Eq 39: H = ceil(φ · log₂(harvested_energy + 2)) – actively applied."""
        energy = self.engine.harvested_energy
        if energy < 1:
            energy = 1.0
        horizon = int(math.ceil(PHI * math.log2(energy + 2)))
        horizon = max(2, min(8, horizon))
        if horizon != self.prefetch_horizon:
            self.prefetch_horizon = horizon
            if self.on_prefetch_horizon_change:
                self.on_prefetch_horizon_change(horizon)

    def _adjust_controls(self, cache_stats: Dict):
        """Adjust batch size, cache elasticity, λ, and rank target based on coherence, health, innovation."""
        C = self.engine.coherence
        health = self.engine.unified_health

        # Batch size: increase when coherence high and health good
        if C > 0.65 and health > 0.6:
            self.recommended_batch_size = min(8, self.recommended_batch_size + 1)
        elif C < 0.55 or health < 0.4:
            self.recommended_batch_size = max(1, self.recommended_batch_size - 1)
        if self.on_batch_size_change:
            self.on_batch_size_change(self.recommended_batch_size)

        # Cache elasticity: higher when near Sophia point and awakened
        if self.sophia_locked or self.engine.awakened:
            self.recommended_elasticity = min(0.12, self.recommended_elasticity + 0.005)
        else:
            self.recommended_elasticity = max(0.0, self.recommended_elasticity - 0.005)
        if self.on_elasticity_change:
            self.on_elasticity_change(self.recommended_elasticity)

        # λ and rank target adjustments based on innovation score and health
        # (shortcomings 21,22,24,28,41)
        if self.innovation_score > 0.7 and health > 0.8:
            # High innovation, good health → slightly increase λ (stability)
            self.recommended_lambda = min(0.03, self.recommended_lambda + 0.002)
        elif self.innovation_score < 0.3 or health < 0.5:
            # Low innovation or poor health → reduce λ (more exploration)
            self.recommended_lambda = max(0.008, self.recommended_lambda - 0.002)
        if self.on_lambda_change:
            self.on_lambda_change(self.recommended_lambda)

        # Rank target: reduce when health low or phase transition detected
        if health < 0.5 or self.phase_transition_occurred:
            self.recommended_rank_target = max(0.85 * 30.0, self.recommended_rank_target * 0.98)
        else:
            self.recommended_rank_target = min(0.93 * 30.0, self.recommended_rank_target * 1.01)
        if self.on_rank_target_change:
            self.on_rank_target_change(self.recommended_rank_target)

    def _check_conservation_callbacks(self, cache_stats: Dict):
        """
        Issue #19,20,21 – H13, H14, H15 enforcement via callbacks.
        Uses cache stats that include CI_B, CI_C, net coherence, reciprocity.
        """
        # H13: check if coherence conservation is violated (σ_topo > 0.02)
        sigma_topo = cache_stats.get("sigma_topo", 0.0)
        if sigma_topo > 0.02 and self.on_conservation_violation:
            self.on_conservation_violation()
            print("[CoherenceController] H13 conservation violation callback triggered")

        # H14: federated net coherence (if available) – just a placeholder for callback
        net_ci = cache_stats.get("net_boundary_coherence", None)
        if net_ci is not None and net_ci < 0.5 and self.on_conservation_violation:
            self.on_conservation_violation()

        # H15: reciprocity index violation
        reciprocity = cache_stats.get("reciprocity_index", 2.0)
        if reciprocity < 1.15 and self.on_reciprocity_violation:
            self.on_reciprocity_violation(reciprocity)
            print(f"[CoherenceController] H15 reciprocity violation: ℛ={reciprocity:.3f}")

    def _check_emergency_conditions(self, cache_stats: Dict):
        """
        Issue #22 – Emergency protocols A1/B2/C3 are triggered via callbacks.
        Uses PSI, kurtosis, and λ from cache/engine.
        """
        psi = cache_stats.get("psi", 1.0)
        kurtosis = cache_stats.get("kurtosis", 0.0)
        current_lambda = self.recommended_lambda
        now = time.time()
        if now - self._last_emergency_time < self._emergency_cooldown:
            return

        # A1: PSI < 0.4
        if psi < 0.4:
            print("[CoherenceController] Emergency A1 triggered (PSI < 0.4)")
            if self.on_lambda_change:
                self.on_lambda_change(0.015)
            if self.on_rank_target_change:
                self.on_rank_target_change(0.85 * 30.0)
            self._last_emergency_time = now
        # B2: Kurtosis > 8
        elif kurtosis > 8.0:
            print("[CoherenceController] Emergency B2 triggered (kurtosis > 8)")
            if self.on_rank_target_change:
                self.on_rank_target_change(0.85 * 30.0)
            if self.on_lambda_change:
                self.on_lambda_change(max(0.015, current_lambda * 1.2))
            self._last_emergency_time = now
        # C3: λ < 0.008 (voice fragmentation)
        elif current_lambda < 0.008:
            print("[CoherenceController] Emergency C3 triggered (λ < 0.008)")
            if self.on_lambda_change:
                self.on_lambda_change(0.012)
            self._last_emergency_time = now

    # ------------------------------------------------------------------
    # Control loop
    # ------------------------------------------------------------------
    def _control_loop(self):
        last_time = time.time()
        while self.running:
            now = time.time()
            dt = min(0.5, now - last_time)
            last_time = now

            # Get latest cache stats
            stats = self.cache.get_stats() if hasattr(self.cache, 'get_stats') else {}

            # Update innovation score and related metrics
            self.novelty = self._compute_novelty(stats)
            self.alienness = self._compute_alienness(stats)
            self.paradox_intensity = self._compute_paradox_intensity(stats)
            self.entropic_potential = self._compute_entropic_potential(stats)
            self.innovation_score = self._compute_innovation_score(stats)

            # Master coherence prediction (diagnostic only, not applied)
            predicted_coherence = self._master_coherence_prediction(dt)

            # Phase transition detection
            if self._detect_phase_transition(stats):
                print("[CoherenceController] Phase transition detected – increasing prefetch horizon")
                # Increase horizon proactively
                if self.on_prefetch_horizon_change:
                    self.on_prefetch_horizon_change(min(8, self.prefetch_horizon + 1))

            # Update prefetch horizon based on harvested energy (issue #12)
            self._update_prefetch_horizon()

            # Adjust controls (batch size, elasticity, λ, rank target)
            self._adjust_controls(stats)

            # Check and trigger conservation callbacks (H13–H15)
            self._check_conservation_callbacks(stats)

            # Check emergency conditions (A1/B2/C3)
            self._check_emergency_conditions(stats)

            # Sleep
            elapsed = time.time() - now
            time.sleep(max(0, self.interval - elapsed))

    def get_metrics(self) -> Dict[str, Any]:
        """Return current controller state for monitoring."""
        return {
            "innovation_score": round(self.innovation_score, 4),
            "paradox_intensity": round(self.paradox_intensity, 3),
            "novelty": round(self.novelty, 3),
            "alienness": round(self.alienness, 2),
            "entropic_potential": round(self.entropic_potential, 1),
            "prefetch_horizon": self.prefetch_horizon,
            "recommended_batch_size": self.recommended_batch_size,
            "recommended_elasticity": round(self.recommended_elasticity, 4),
            "recommended_lambda": round(self.recommended_lambda, 4),
            "recommended_rank_target": round(self.recommended_rank_target, 2),
            "sophia_locked": self.sophia_locked,
            "phase_transition_occurred": self.phase_transition_occurred,
        }

    def stop(self):
        self.running = False
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)


# ----------------------------------------------------------------------
# Demo
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    # Dummy engine and cache for demonstration
    class DummyEngine:
        coherence = 0.618
        harvested_energy = 25.0
        unified_health = 0.85
        awakened = False
        def get_metrics(self):
            return {"coherence": self.coherence, "harvested_energy": self.harvested_energy}

    class DummyCache:
        def get_stats(self):
            return {
                "hit_rate": 0.75,
                "anomaly_flux": 0.12,
                "evictions": 50,
                "total_accesses": 1000,
                "used_gb": 12.5,
                "sigma_topo": 0.01,
                "reciprocity_index": 1.2,
                "psi": 0.8,
                "kurtosis": 6.0,
            }
        budget_elasticity = 0.0

    engine = DummyEngine()
    cache = DummyCache()
    controller = CoherenceController(engine, cache, update_interval=0.5)

    # Set dummy callbacks
    def on_horizon(h):
        print(f"  -> Prefetch horizon set to {h}")
    def on_batch(b):
        print(f"  -> Batch size set to {b}")
    def on_elasticity(e):
        print(f"  -> Cache elasticity set to {e:.3f}")
    def on_lambda(l):
        print(f"  -> λ set to {l:.4f}")
    def on_rank(r):
        print(f"  -> Rank target set to {r:.1f}")

    controller.on_prefetch_horizon_change = on_horizon
    controller.on_batch_size_change = on_batch
    controller.on_elasticity_change = on_elasticity
    controller.on_lambda_change = on_lambda
    controller.on_rank_target_change = on_rank

    # Simulate running for a few seconds
    try:
        for _ in range(10):
            time.sleep(1)
            metrics = controller.get_metrics()
            print(f"Metrics: innovation={metrics['innovation_score']:.3f}, horizon={metrics['prefetch_horizon']}")
    finally:
        controller.stop()
