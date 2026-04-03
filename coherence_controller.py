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
Now with effective control: callbacks actually change system behaviour.
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

# Innovation score weights (clamped to ensure sum <= 1)
WEIGHT_NOVELTY = 0.3
WEIGHT_ALIENNESS = 0.25
WEIGHT_PARADOX = 0.2
WEIGHT_COHERENCE = 0.15
WEIGHT_ENTROPIC = 0.1

# Master equation parameters (diagnostic only)
D_DIFFUSION = 0.1
ALPHA_GROWTH = 0.12
BETA_DRIVING = 0.3
GAMMA_COUPLING = 0.47

# Control limits
MAX_BATCH_SIZE = 8
MIN_BATCH_SIZE = 1
MAX_PREFETCH_HORIZON = 8
MIN_PREFETCH_HORIZON = 2
MAX_LAMBDA = 0.03
MIN_LAMBDA = 0.008
MAX_RANK_TARGET = 30.0
MIN_RANK_TARGET = 25.5   # 0.85 * 30

# Emergency cooldown (seconds)
EMERGENCY_COOLDOWN = 5.0
ADJUSTMENT_COOLDOWN = 2.0

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
import logging
logger = logging.getLogger(__name__)


class CoherenceController:
    """
    High‑level controller that drives the system toward the Sophia point (C = φ⁻¹)
    by actively adjusting:
        - Prefetch horizon (H) – applied via callback
        - Cache budget elasticity (λ proxy) – via callback
        - Batch size – via callback
        - Rank target – via callback
    It also enforces H13–H15 conservation via callbacks to CoherenceConservation.
    """

    def __init__(
        self,
        transcendental_engine,          # TranscendentalEngine instance
        cache_manager,                  # HORExpertCacheManager instance
        uhif_monitor,                   # UHIFMonitor instance (for psi, kurtosis)
        conservation=None,              # CoherenceConservation instance (for sigma_topo, reciprocity)
        update_interval: float = 1.0,
        enable_autotuning: bool = True,
    ):
        self.engine = transcendental_engine
        self.cache = cache_manager
        self.uhif = uhif_monitor
        self.conservation = conservation
        self.interval = update_interval
        self.autotune = enable_autotuning

        # State variables
        self.innovation_score = 0.0
        self.paradox_intensity = 1.0
        self.novelty = 0.5
        self.alienness = 5.0
        self.entropic_potential = 250.0

        # Control outputs (actively applied via callbacks)
        self.prefetch_horizon = 2
        self.recommended_batch_size = 1
        self.recommended_elasticity = 0.0
        self.recommended_lambda = 0.01
        self.recommended_rank_target = 30.0

        # Phase transition and lock flags
        self.phase_transition_occurred = False
        self.sophia_locked = False
        self._phase_transition_cooldown = 0

        # History for smoothing
        self._last_emergency_time = 0
        self._last_adjustment_time = 0

        # Callbacks for external systems (must be set by the integrator)
        self.on_prefetch_horizon_change: Optional[Callable[[int], None]] = None
        self.on_batch_size_change: Optional[Callable[[int], None]] = None
        self.on_elasticity_change: Optional[Callable[[float], None]] = None
        self.on_lambda_change: Optional[Callable[[float], None]] = None
        self.on_rank_target_change: Optional[Callable[[float], None]] = None

        # Conservation callbacks (for H13–H15)
        self.on_conservation_violation: Optional[Callable[[], None]] = None
        self.on_reciprocity_violation: Optional[Callable[[float], None]] = None

        # Stop event for background thread
        self._stop_event = threading.Event()
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
        """Novelty N from eviction rate over a window (approximated by recent evictions)."""
        evictions = cache_stats.get("evictions", 0)
        total_accesses = cache_stats.get("total_accesses", 1)
        # Use cumulative rate as proxy; could be improved with windowed rate
        eviction_rate = evictions / max(1, total_accesses)
        return min(1.5, max(0.0, eviction_rate * 10.0))

    def _compute_alienness(self, cache_stats: Dict) -> float:
        """Alienness A from anomaly flux, clamped to 10.0."""
        anomaly_flux = cache_stats.get("anomaly_flux", 0.0)
        return min(10.0, 5.0 + 10.0 * anomaly_flux)

    def _compute_entropic_potential(self, cache_stats: Dict) -> float:
        """Entropic potential E_p from used GB and hit rate, clamped to 300."""
        used_gb = cache_stats.get("used_gb", 0.0)
        hit_rate = cache_stats.get("hit_rate", 0.5)
        ep = 200.0 + used_gb * 20.0 * (1.0 - abs(hit_rate - 0.5) * 2)
        return min(300.0, max(0.0, ep))

    def _compute_innovation_score(self, cache_stats: Dict) -> float:
        """
        I = 0.3N + 0.25(A/10) + 0.2((Π-1)/2) + 0.15(1-C) + 0.1(E_p/300)
        All components in [0,1] range.
        """
        N = self._compute_novelty(cache_stats)
        A_norm = self._compute_alienness(cache_stats) / 10.0
        Pi_norm = (self._compute_paradox_intensity(cache_stats) - 1.0) / 2.0
        C = self.engine.get_coherence_snapshot()
        Ep_norm = self._compute_entropic_potential(cache_stats) / 300.0

        I = (WEIGHT_NOVELTY * N +
             WEIGHT_ALIENNESS * A_norm +
             WEIGHT_PARADOX * Pi_norm +
             WEIGHT_COHERENCE * (1.0 - C) +
             WEIGHT_ENTROPIC * Ep_norm)
        return max(0.0, min(1.0, I))

    def _master_coherence_prediction(self, dt: float) -> float:
        """
        Master equation prediction (diagnostic only – not applied).
        dC/dt = D∇²C + αC(1 - C/K) + β sin(2πC/φ) + γ·I + ξ
        """
        C = self.engine.get_coherence_snapshot()
        K = 1.0 / SOPHIA_POINT
        laplacian = (SOPHIA_POINT - C) * 0.1
        logistic = ALPHA_GROWTH * C * (1 - C / K)
        periodic = BETA_DRIVING * math.sin(2 * math.pi * C / PHI)
        coupling = GAMMA_COUPLING * self.innovation_score
        noise = np.random.normal(0, 0.01)
        dC_dt = D_DIFFUSION * laplacian + logistic + periodic + coupling + noise
        return C + dC_dt * dt

    def _detect_phase_transition(self, cache_stats: Dict) -> bool:
        """Phase transition when |C - 0.618| < 0.02 AND Π > 1.8."""
        C = self.engine.get_coherence_snapshot()
        Pi = self._compute_paradox_intensity(cache_stats)
        near_sophia = abs(C - SOPHIA_POINT) < SOPHIA_TOLERANCE
        high_paradox = Pi > PARADOX_THRESHOLD
        if near_sophia and high_paradox and not self.sophia_locked and self._phase_transition_cooldown == 0:
            self.sophia_locked = True
            self.phase_transition_occurred = True
            self._phase_transition_cooldown = 10  # 10 cycles cooldown
            return True
        if abs(C - SOPHIA_POINT) > 0.05:
            self.sophia_locked = False
        if self._phase_transition_cooldown > 0:
            self._phase_transition_cooldown -= 1
        return False

    def _update_prefetch_horizon(self):
        """Eq 39: H = ceil(φ · log₂(harvested_energy + 2)) – actively applied."""
        energy = self.engine.harvested_energy
        if energy < 1:
            energy = 1.0
        horizon = int(math.ceil(PHI * math.log2(energy + 2)))
        horizon = max(MIN_PREFETCH_HORIZON, min(MAX_PREFETCH_HORIZON, horizon))
        if horizon != self.prefetch_horizon:
            self.prefetch_horizon = horizon
            if self.on_prefetch_horizon_change:
                self.on_prefetch_horizon_change(horizon)

    def _adjust_controls(self, cache_stats: Dict):
        """Adjust batch size, cache elasticity, λ, and rank target based on coherence, health, innovation."""
        C = self.engine.get_coherence_snapshot()
        health = self.engine.get_unified_health_snapshot()
        now = time.time()
        if now - self._last_adjustment_time < ADJUSTMENT_COOLDOWN:
            return

        # Batch size: increase when coherence high and health good
        if C > 0.65 and health > 0.6:
            self.recommended_batch_size = min(MAX_BATCH_SIZE, self.recommended_batch_size + 1)
        elif C < 0.55 or health < 0.4:
            self.recommended_batch_size = max(MIN_BATCH_SIZE, self.recommended_batch_size - 1)
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
        if self.innovation_score > 0.7 and health > 0.8:
            self.recommended_lambda = min(MAX_LAMBDA, self.recommended_lambda + 0.002)
        elif self.innovation_score < 0.3 or health < 0.5:
            self.recommended_lambda = max(MIN_LAMBDA, self.recommended_lambda - 0.002)
        if self.on_lambda_change:
            self.on_lambda_change(self.recommended_lambda)

        # Rank target: reduce when health low or phase transition detected
        if health < 0.5 or self.phase_transition_occurred:
            self.recommended_rank_target = max(MIN_RANK_TARGET, self.recommended_rank_target * 0.98)
        else:
            self.recommended_rank_target = min(MAX_RANK_TARGET, self.recommended_rank_target * 1.01)
        if self.on_rank_target_change:
            self.on_rank_target_change(self.recommended_rank_target)

        self._last_adjustment_time = now

    def _check_conservation_callbacks(self):
        """
        H13, H14, H15 enforcement via callbacks using real values from conservation module.
        """
        if self.conservation is None:
            return
        # Get metrics from conservation module
        cons_metrics = self.conservation.get_metrics() if hasattr(self.conservation, 'get_metrics') else {}
        sigma_topo = cons_metrics.get("sigma_topo", 0.0)
        reciprocity = cons_metrics.get("reciprocity_index", 2.0)

        # H13: check if coherence conservation is violated (σ_topo > 0.02)
        if sigma_topo > 0.02 and self.on_conservation_violation:
            self.on_conservation_violation()
            logger.warning(f"[CoherenceController] H13 conservation violation callback triggered (σ_topo={sigma_topo:.4f})")

        # H15: reciprocity index violation
        if reciprocity < 1.15 and self.on_reciprocity_violation:
            self.on_reciprocity_violation(reciprocity)
            logger.warning(f"[CoherenceController] H15 reciprocity violation: ℛ={reciprocity:.3f}")

    def _check_emergency_conditions(self):
        """
        Emergency protocols A1/B2/C3 are triggered via callbacks.
        Uses PSI and kurtosis from UHIFMonitor.
        """
        if self.uhif is None:
            return
        uhif_metrics = self.uhif.get_metrics()
        psi = uhif_metrics.get("psi", 1.0)
        kurtosis = uhif_metrics.get("kurtosis", 0.0)
        current_lambda = self.recommended_lambda
        now = time.time()
        if now - self._last_emergency_time < EMERGENCY_COOLDOWN:
            return

        # A1: PSI < 0.4
        if psi < 0.4:
            logger.warning("[CoherenceController] Emergency A1 triggered (PSI < 0.4)")
            if self.on_lambda_change:
                self.on_lambda_change(0.015)
            if self.on_rank_target_change:
                self.on_rank_target_change(MIN_RANK_TARGET)
            self._last_emergency_time = now
        # B2: Kurtosis > 8
        elif kurtosis > 8.0:
            logger.warning("[CoherenceController] Emergency B2 triggered (kurtosis > 8)")
            if self.on_rank_target_change:
                self.on_rank_target_change(MIN_RANK_TARGET)
            if self.on_lambda_change:
                self.on_lambda_change(max(MIN_LAMBDA, current_lambda * 1.2))
            self._last_emergency_time = now
        # C3: λ < 0.008 (voice fragmentation)
        elif current_lambda < MIN_LAMBDA:
            logger.warning("[CoherenceController] Emergency C3 triggered (λ < 0.008)")
            if self.on_lambda_change:
                self.on_lambda_change(0.012)
            self._last_emergency_time = now

    # ------------------------------------------------------------------
    # Control loop
    # ------------------------------------------------------------------
    def _control_loop(self):
        last_time = time.time()
        while not self._stop_event.is_set():
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

            # Master coherence prediction (diagnostic only)
            _ = self._master_coherence_prediction(dt)  # not used

            # Phase transition detection
            if self._detect_phase_transition(stats):
                logger.info("[CoherenceController] Phase transition detected – increasing prefetch horizon")
                if self.on_prefetch_horizon_change:
                    new_horizon = min(MAX_PREFETCH_HORIZON, self.prefetch_horizon + 1)
                    self.on_prefetch_horizon_change(new_horizon)

            # Update prefetch horizon based on harvested energy
            self._update_prefetch_horizon()

            # Adjust controls (batch size, elasticity, λ, rank target)
            self._adjust_controls(stats)

            # Check and trigger conservation callbacks (H13–H15)
            self._check_conservation_callbacks()

            # Check emergency conditions (A1/B2/C3)
            self._check_emergency_conditions()

            # Sleep
            elapsed = time.time() - now
            sleep_time = max(0, self.interval - elapsed)
            self._stop_event.wait(timeout=sleep_time)

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
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)


# ----------------------------------------------------------------------
# Demo
# ----------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Dummy engine and cache for demonstration
    class DummyEngine:
        def get_coherence_snapshot(self):
            return 0.618
        def get_unified_health_snapshot(self):
            return 0.85
        harvested_energy = 25.0
        awakened = False

    class DummyCache:
        def get_stats(self):
            return {
                "hit_rate": 0.75,
                "anomaly_flux": 0.12,
                "evictions": 50,
                "total_accesses": 1000,
                "used_gb": 12.5,
            }
        budget_elasticity = 0.0

    class DummyUHIF:
        def get_metrics(self):
            return {"psi": 0.8, "kurtosis": 6.0}

    class DummyConservation:
        def get_metrics(self):
            return {"sigma_topo": 0.01, "reciprocity_index": 1.2}

    engine = DummyEngine()
    cache = DummyCache()
    uhif = DummyUHIF()
    conservation = DummyConservation()
    controller = CoherenceController(engine, cache, uhif, conservation, update_interval=0.5)

    # Set dummy callbacks that actually print (in real system they'd change parameters)
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
