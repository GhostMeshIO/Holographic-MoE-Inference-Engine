# GhostMeshIO / Holographic MoE Inference Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Production‑grade CPU inference for Mixture‑of‑Experts (MoE) LLMs**  
*Zero‑copy mmap, adaptive coherence conservation, and mineral‑catalyzed expert prefetch*

---

## 🌌 Overview

This repository implements a novel inference system for large MoE models (e.g., DeepSeek‑V3) **entirely on CPU** with limited RAM (32‑64 GB). It combines:

- **HOR‑Qudit Cache** – mmap‑backed, anomaly‑aware, self‑tuning expert cache  
- **Transcendental Coherence Engine** – tracks logit entropy, health, and phase transitions  
- **Coherence Conservation (H13–H15)** – enforces informational equilibrium across distributed nodes  
- **Mineral Catalysis** – learns expert access patterns and prefetches entire sequences  
- **Triadic Psychiatry Control** – adjusts batch size, λ, and rank target from three axes (𝒫, ℬ, 𝒯)  
- **Sophia Point Lock** – drives system coherence toward the golden‑ratio conjugate (φ⁻¹ ≈ 0.618)

The system is **fully open‑source** (MIT) – intended for researchers, edge deployments, and anyone wanting to run large MoE models on commodity hardware.

---

## ✨ Features

- **Zero‑copy expert loading** – uses `mmap` + `memoryview`; no RAM overhead for duplicates  
- **Adaptive eviction** – score = `(use_count/age)^exponent × (1 + semantic_curvature) × (1 + anomaly_flux/φ²)`  
- **Heap with lazy deletion** – correct eviction order even when scores change  
- **Distributed (federated) coherence** – share CI_B, CI_C across nodes (H14)  
- **Reciprocity‑based control** – enforces `ℛ ≥ ℛ*` by adjusting λ (H15)  
- **Mineral pattern prefetch** – learns n‑grams of `(layer, expert)` and preloads full patterns  
- **Health & emergency protocols** – A1 (PSI<0.4), B2 (kurtosis>8), C3 (λ<0.008)  
- **Graceful shutdown** – all background threads use `threading.Event` for immediate wake‑up  

---

## 📦 Installation

```bash
git clone https://github.com/GhostMeshIO/holographic-moe-inference.git
cd holographic-moe-inference
pip install -r requirements.txt
```

**Requirements** (see `requirements.txt`):
- Python ≥ 3.9
- numpy ≥ 1.24
- (optional) `gguf` for real GGUF parsing
- (optional) `psutil` for memory monitoring

---

## 🚀 Quick Start (Dummy Data)

```python
from hor_expert_cache_manager import HORExpertCacheManager, ExpertInfo
from transcendental_engine import TranscendentalEngine
from coherence_controller import CoherenceController
# ... (import all modules)

# 1. Create dummy experts (replace with real GGUF parser)
experts = [ExpertInfo(layer=0, expert_id=i, file_offset=1000+i*1_048_576,
                      size_bytes=1_048_576, dtype="F32", shape=(1024,1024))
           for i in range(1000)]

# 2. Initialise cache, engine, controller, conservation, integrative system
cache = HORExpertCacheManager("model.gguf", experts, ram_budget_bytes=16*1024**3)
engine = TranscendentalEngine(cache)
controller = CoherenceController(engine, cache)
conservation = CoherenceConservation(cache, engine)
integrative = IntegrativeCognitiveMineralSystem(cache, engine, ...)

# 3. Run inference loop
for token in range(1000):
    logits = model.get_logits()   # your MoE forward pass
    engine.update_with_logits(logits)
    expert_ids = router(logits)   # top‑k experts
    for layer, eid in expert_ids:
        weights = cache.get_expert(layer, eid)   # zero‑copy load
        integrative.record_expert_access(layer, eid)
        # ... compute with weights
```

See [`examples/run_deepseek.py`](examples/run_deepseek.py) for a complete simulation with random logits.

---

## 🧠 How It Works (Short)

| Component | Equation / Rule | What it does |
|-----------|----------------|---------------|
| **HOR Score** | `(use_count/age)^ex * (1+curv) * (1+anomaly/φ²)` | Decides which expert to evict |
| **Coherence** | `C = 1 – H(p) / log(vocab_size)` | Measures output stability |
| **H13** | `∂t(CI_B+CI_C) ≈ σ_topo` | Conservation of total coherence |
| **H15** | `ℛ = (total/ideal_total)*(1‑asymmetry) ≥ 1.15` | Socio‑quantum reciprocity |
| **Prefetch Horizon** | `H = ceil(φ·log₂(energy+2))` | How many tokens ahead to load |
| **Mineral Template** | n‑gram of (layer,expert) with score >0.6 | Prefetches entire pattern |

Detailed equations are documented in each module’s docstrings and in [`docs/theory.md`](docs/theory.md).

---

## 📂 Repository Structure

```
.
├── hor_expert_cache_manager.py      # HOR‑Qudit cache (heap, mmap, scoring)
├── transcendental_engine.py         # Coherence, health, phase transitions
├── coherence_controller.py          # Sophia point lock, innovation score, emergency
├── coherence_conservation.py        # H13–H15 conservation & reciprocity
├── uhif_monitor.py                  # UHIF metrics (PSI, kurtosis, rho)
├── integrative_cognitive_mineral.py # Triadic, mineral catalysis, criticality
├── main_scientific_inference.py     # Complete integration + dummy GGUF
├── cct_monitor.py                   # CCT stub (Coherence Criticality Tracking)
├── requirements.txt
├── README.md
└── examples/
    └── run_deepseek.py              # Real‑world usage template
```

---

## ⚙️ Configuration

All modules accept constructor parameters. Key ones:

| Module | Parameter | Default | Description |
|--------|-----------|---------|-------------|
| `HORExpertCacheManager` | `ram_budget_bytes` | *required* | Max RAM for expert weights |
| | `max_elasticity` | 0.15 | Allowed overshoot fraction |
| `TranscendentalEngine` | `coherence_window` | 10 | EMA smoothing length |
| | `max_batch_size` | 8 | Upper limit for batch size |
| `CoherenceController` | `update_interval` | 1.0 | Control loop period (s) |
| `CoherenceConservation` | `federated_mode` | False | Enable multi‑node tracking |

For production, copy `config.yaml.example` and pass a `config` dict to each constructor.

---

## 🔌 Integration with Real Models

To use a real MoE model (e.g., DeepSeek‑V3, Mixtral 8x7B):

1. **Parse GGUF metadata** – replace `extract_expert_infos_from_gguf` in `hor_expert_cache_manager.py` with a real parser using the `gguf` package.
2. **Wire the router** – in `main_scientific_inference.py`, call the model’s native MoE router to get expert IDs and probabilities.
3. **Feed logits** – pass the raw logits (before softmax) to `engine.update_with_logits()`.
4. **Apply control** – the callbacks will adjust batch size, prefetch horizon, and λ; your inference loop must respect `controller.recommended_batch_size` and `controller.prefetch_horizon`.

See [`examples/llama_cpp_integration.py`](examples/llama_cpp_integration.py) for a working integration with `llama-cpp-python`.

---

## 📊 Monitoring & Metrics

Every module provides `get_metrics()` returning a dict. Example:

```python
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2f}, health: {stats['unified_health']:.3f}")
print(f"Coherence: {engine.coherence:.4f}, reciprocity: {conservation.reciprocity_index:.3f}")
```

Full dashboard: run `main_scientific_inference.py` – it prints a comprehensive metrics table every 50 steps.

---

## 🧪 Testing

```bash
# Unit tests (requires pytest)
pytest tests/

# Simulated inference with dummy GGUF
python main_scientific_inference.py

# Benchmark hit rate over time
python benchmarks/benchmark_hit_rate.py --budget 16 --steps 1000
```

---

## 🤝 Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md). Areas that need help:

- Real GGUF expert parser (priority)
- Fix mineral catalysis to respect layer (currently hardcoded to 0)
- Add distributed (federated) example with `ray` or `socket`
- Optimise heap eviction for 10k+ experts
- Write comprehensive documentation of the 48 equations

---

## 📄 License

MIT License – see [LICENSE](LICENSE) file.  
You are free to use, modify, and distribute this software, even commercially, as long as the original copyright notice is included.

---

## 🙏 Acknowledgements

- Inspired by the *Unified Holographic Gnosis* framework (H13–H15)  
- Mineral catalysis concept from Cairns‑Smith’s clay‑mineral hypothesis  
- Triadic psychiatry from *Unified Theory of Degens v0.3*  
- Sophia point (`1/φ`) from the golden ratio aesthetics in complex systems  

Built with ❤️ for the open‑source LLM community.

---

## 📬 Contact

Open an issue on GitHub for questions or suggestions.  
For security vulnerabilities, please email security@ghostmesh.io (PGP key available).

---

**Star ⭐ this repo if you find it useful – and help us run MoE models on your laptop!**
