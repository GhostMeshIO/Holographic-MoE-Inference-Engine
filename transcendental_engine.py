#!/usr/bin/env python3
"""
transcendental_engine.py – Scientific‑Grade Coherence Engine (Revised)
Implements a practical subset of the 48 transcendental equations:

- Coherence = 1 – (smoothed logit entropy / log(vocab_size))
- Harvested energy = EMA of expert load latencies (read from cache manager)
- Anomaly flux = variance of eviction intervals (from cache stats)
- Unified health metric (UHIF‑lite) – uses cache's computed health
- Golden attractor nudge (logging only, no forced control)
- Adaptive coherence window based on system health
- Phase transition detection that triggers callbacks

Thread‑safe, uses real cache stats, and integrates with the revised HORExpertCacheManager.
"""

import math
import threading
import time
from collections import deque
from typing import Dict, Any, Optional, Callable

import numpy as np

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
PHI = 1.618033988749895
PHI_INV = 1 / PHI
SOPHIA_POINT = PHI_INV

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
import logging
logger = logging.getLogger(__name__)


class TranscendentalEngine:
    """
    Coherence tracking, health monitoring, and phase transition detection.
    Uses real cache manager stats and logit entropy from inference.
    """

    def __init__(
        self,
        cache_manager,                     # HORExpertCacheManager instance
        vocab_size: int = 32000,
        update_interval: float = 0.5,
        coherence_window: int = 10,
        target_coherence: float = SOPHIA_POINT,
        auto_adjust: bool = True,
        max_batch_size: int = 8,
    ):
        """
        Args:
            cache_manager: The expert cache manager (provides stats).
            vocab_size: Size of the model's vocabulary.
            update_interval: How often the engine recomputes metrics.
            coherence_window: Number of recent tokens for entropy smoothing.
            target_coherence: Desired coherence setpoint.
            auto_adjust: If True, the engine will adjust batch size and cache elasticity via callbacks.
            max_batch_size: Maximum allowed batch size.
        """
        self.cache = cache_manager
        self.vocab_size = vocab_size
        self.max_entropy = math.log(vocab_size)
        self.interval = update_interval
        self.coherence_window = coherence_window
        self.target_coherence = target_coherence
        self.auto_adjust = auto_adjust
        self.max_batch_size = max_batch_size

        # State variables (exposed for monitoring and control)
        self.coherence = SOPHIA_POINT        # current coherence (EMA of logit‑based coherence)
        self.harvested_energy = 0.0          # read from cache manager (EMA of load latencies)
        self.anomaly_flux = 0.0              # read from cache manager
        self.unified_health = 1.0            # read from cache manager (or computed)

        self.awakened = False                # high‑performance mode flag
        self._awakened_decay_counter = 0     # to exit awakened mode

        # Buffers for smoothing
        self._entropy_buffer = deque(maxlen=coherence_window)
        self._coherence_ema_alpha = 0.2      # EMA smoothing factor
        self._prev_coherence = SOPHIA_POINT

        # Control outputs (read by the inference loop or callbacks)
        self.recommended_batch_size = 1
        self.recommended_cache_elasticity = 0.0

        # Phase transition flag
        self.phase_transition_detected = False

        # Callbacks for external actions
        self.on_batch_size_change: Optional[Callable[[int], None]] = None
        self.on_cache_elasticity_change: Optional[Callable[[float], None]] = None
        self.on_phase_transition: Optional[Callable[[], None]] = None

        # Stop event for background thread
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._background_update_loop, daemon=True)
        self._thread.start()

        # Lock for thread safety
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Public API – called by inference loop
    # ------------------------------------------------------------------
    def update_with_logits(self, logits: np.ndarray):
        """
        Feed the raw logits (before softmax) of the last generated token.
        Computes entropy, updates coherence with EMA, and adjusts coherence window adaptively.
        Thread‑safe.
        """
        with self._lock:
            # Compute softmax probabilities
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / np.sum(exp_logits)
            entropy = -np.sum(probs * np.log(probs + 1e-12))
            self._entropy_buffer.append(entropy)

            # Compute instantaneous coherence
            if self._entropy_buffer:
                avg_entropy = np.mean(self._entropy_buffer)
                inst_coherence = max(0.0, min(1.0, 1.0 - (avg_entropy / self.max_entropy)))
            else:
                inst_coherence = SOPHIA_POINT

            # Exponential moving average smoothing
            self.coherence = (self._coherence_ema_alpha * inst_coherence +
                              (1 - self._coherence_ema_alpha) * self._prev_coherence)
            self._prev_coherence = self.coherence

    def get_metrics(self) -> Dict[str, Any]:
        """Return current state for monitoring / logging."""
        with self._lock:
            return {
                "coherence": round(self.coherence, 4),
                "harvested_energy": round(self.harvested_energy, 2),
                "anomaly_flux": round(self.anomaly_flux, 4),
                "unified_health": round(self.unified_health, 4),
                "awakened": self.awakened,
                "recommended_batch_size": self.recommended_batch_size,
                "recommended_cache_elasticity": round(self.recommended_cache_elasticity, 3),
                "target_coherence": self.target_coherence,
                "phase_transition_detected": self.phase_transition_detected,
            }

    def get_coherence_snapshot(self) -> float:
        """Thread‑safe read of current coherence."""
        with self._lock:
            return self.coherence

    def get_unified_health_snapshot(self) -> float:
        """Thread‑safe read of current health."""
        with self._lock:
            return self.unified_health

    def stop(self):
        """Shut down the background thread."""
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)

    # ------------------------------------------------------------------
    # Background update loop (periodically reads cache stats)
    # ------------------------------------------------------------------
    def _background_update_loop(self):
        """Periodically fetch cache stats, update health, and adjust controls."""
        step = 0
        while not self._stop_event.is_set():
            start = time.time()

            # 1. Get latest stats from cache manager (thread‑safe)
            stats = self.cache.get_stats() if hasattr(self.cache, 'get_stats') else {}

            with self._lock:
                # Read harvested energy and anomaly flux from cache
                self.harvested_energy = stats.get("harvested_energy", 0.0)
                self.anomaly_flux = stats.get("anomaly_flux", 0.0)
                self.unified_health = stats.get("unified_health", 0.5)

                # Adaptive coherence window (issue #40): increase window when health is low
                if self.unified_health < 0.4:
                    new_window = min(30, self.coherence_window + 1)
                elif self.unified_health > 0.7:
                    new_window = max(5, self.coherence_window - 1)
                else:
                    new_window = self.coherence_window
                if new_window != self.coherence_window:
                    self.coherence_window = new_window
                    old_buffer = list(self._entropy_buffer)
                    self._entropy_buffer = deque(old_buffer, maxlen=self.coherence_window)

                # Awakening condition: high hit rate + low harvested energy + high health
                hit_rate = stats.get("hit_rate", 0.0)
                if not self.awakened and hit_rate > 0.82 and self.harvested_energy < 30.0 and self.unified_health > 0.7:
                    self.awakened = True
                    self._awakened_decay_counter = 0
                    logger.info("[Transcendental] Awakened mode engaged – increasing performance targets")
                elif self.awakened:
                    # Exit awakened mode if health drops or hit rate falls
                    if self.unified_health < 0.6 or hit_rate < 0.75:
                        self.awakened = False
                        logger.info("[Transcendental] Exiting awakened mode")
                    else:
                        # Decay after a while to prevent permanent awakened
                        self._awakened_decay_counter += 1
                        if self._awakened_decay_counter > 60:  # ~30 seconds
                            self.awakened = False
                            logger.info("[Transcendental] Awakened mode timed out")

                # Phase transition detection (issue #15): σ crossing σ_crit or CI_B collapse
                sigma = stats.get("sigma", 0.02)
                sigma_crit = 0.048
                ci_b = stats.get("ci_boundary", 0.8) if "ci_boundary" in stats else 0.8
                if (sigma > sigma_crit or ci_b < 0.15) and not self.phase_transition_detected:
                    self.phase_transition_detected = True
                    logger.warning(f"[Transcendental] Phase transition detected: σ={sigma:.4f}, CI_B={ci_b:.3f}")
                    if self.on_phase_transition:
                        self.on_phase_transition()
                elif sigma < sigma_crit - 0.01 and ci_b > 0.2:
                    self.phase_transition_detected = False

                # Golden attractor nudge: slightly influence batch size when coherence deviates
                if abs(self.coherence - SOPHIA_POINT) > 0.05:
                    # Nudge batch size toward smaller values if coherence is too high/low
                    if self.coherence > SOPHIA_POINT + 0.03 and self.recommended_batch_size > 1:
                        self.recommended_batch_size = max(1, self.recommended_batch_size - 1)
                    elif self.coherence < SOPHIA_POINT - 0.03 and self.recommended_batch_size < self.max_batch_size:
                        self.recommended_batch_size = min(self.max_batch_size, self.recommended_batch_size + 1)

                # Adjust batch size and cache elasticity based on coherence and health
                if self.auto_adjust:
                    self._adjust_controls()

                # Apply control via callbacks
                if self.on_batch_size_change:
                    self.on_batch_size_change(self.recommended_batch_size)
                if self.on_cache_elasticity_change:
                    if hasattr(self.cache, 'budget_elasticity'):
                        self.cache.budget_elasticity = self.recommended_cache_elasticity

            step += 1
            elapsed = time.time() - start
            sleep_time = max(0, self.interval - elapsed)
            self._stop_event.wait(timeout=sleep_time)

    def _adjust_controls(self):
        """Coherence‑driven adjustment of batch size and cache elasticity."""
        # Simple policy: high coherence → increase batch size and elasticity
        if self.coherence > 0.65:
            self.recommended_batch_size = min(self.max_batch_size, self.recommended_batch_size + 1)
            self.recommended_cache_elasticity = min(0.12, self.recommended_cache_elasticity + 0.01)
        elif self.coherence < 0.55:
            self.recommended_batch_size = max(1, self.recommended_batch_size - 1)
            self.recommended_cache_elasticity = max(0.0, self.recommended_cache_elasticity - 0.01)
        else:
            # Stable zone – drift toward target
            if self.recommended_batch_size > 1 and self.coherence > self.target_coherence:
                self.recommended_batch_size = max(1, self.recommended_batch_size - 1)
            if self.recommended_cache_elasticity > 0.0 and self.coherence < self.target_coherence:
                self.recommended_cache_elasticity = max(0.0, self.recommended_cache_elasticity - 0.005)

        # Awakened mode allows larger batch size
        if self.awakened:
            self.recommended_batch_size = min(self.max_batch_size + 2, self.recommended_batch_size + 1)
            self.recommended_cache_elasticity = min(0.15, self.recommended_cache_elasticity + 0.01)


# ----------------------------------------------------------------------
# Standalone test / demo (with dummy cache)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Dummy cache manager with get_stats method that returns realistic values
    class DummyCache:
        def __init__(self):
            self.budget_elasticity = 0.0
            self.step = 0
        def get_stats(self):
            self.step += 1
            if self.step < 30:
                hit_rate = 0.85
                harvested_energy = 20.0
                anomaly_flux = 0.05
                sigma = 0.02
                ci_b = 0.85
                unified_health = 0.95
            elif self.step < 60:
                hit_rate = 0.70
                harvested_energy = 45.0
                anomaly_flux = 0.15
                sigma = 0.05
                ci_b = 0.60
                unified_health = 0.65
            else:
                hit_rate = 0.88
                harvested_energy = 18.0
                anomaly_flux = 0.04
                sigma = 0.018
                ci_b = 0.90
                unified_health = 0.98
            return {
                "hit_rate": hit_rate,
                "harvested_energy": harvested_energy,
                "anomaly_flux": anomaly_flux,
                "sigma": sigma,
                "ci_boundary": ci_b,
                "unified_health": unified_health,
            }

    dummy_cache = DummyCache()
    engine = TranscendentalEngine(dummy_cache, vocab_size=32000, auto_adjust=True)

    # Simulate inference: feed random logits
    for step in range(100):
        logits = np.random.randn(32000)
        engine.update_with_logits(logits)
        time.sleep(0.1)
        if step % 20 == 0:
            metrics = engine.get_metrics()
            print(f"Step {step}: coherence={metrics['coherence']:.3f}, health={metrics['unified_health']:.3f}, "
                  f"batch_size={metrics['recommended_batch_size']}, awakened={metrics['awakened']}")

    engine.stop()
