#!/usr/bin/env python3
"""Download a small safetensors LLM and feed its token stream to the circuit model."""

from __future__ import annotations

import argparse
import json
import os
import re
import resource
import sys
import time
from pathlib import Path
from typing import Any

from huggingface_hub import snapshot_download

from entanglement_sim import (
    DEFAULT_NETLIST,
    EntanglementSimulator,
    OptimizedEntanglementSimulator,
    SpiceNetlist,
)


DEFAULT_MODEL_ID = "HuggingFaceTB/SmolLM2-135M-Instruct"
DEFAULT_BASELINES = Path(__file__).resolve().parent / "mcu_baselines.json"
DEFAULT_OPTIMIZED_NETLIST = Path(__file__).resolve().parents[1] / "kicad" / "entanglement_optimized.cir"


def download_safetensors_model(model_id: str, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    model_path = Path(
        snapshot_download(
            repo_id=model_id,
            cache_dir=str(cache_dir),
            allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt", "*.vocab", "*.merges"],
            ignore_patterns=["*.bin", "*.pt", "*.pth", "*.onnx"],
        )
    )
    safe_files = sorted(model_path.glob("*.safetensors"))
    if not safe_files:
        raise RuntimeError(f"{model_id} did not provide a top-level safetensors file")
    try:
        from safetensors import safe_open
    except ImportError as exc:
        raise RuntimeError("install safetensors before downloading model weights") from exc
    for safe_file in safe_files:
        with safe_open(str(safe_file), framework="np", device="cpu") as handle:
            if not list(handle.keys()):
                raise RuntimeError(f"safetensors file is empty: {safe_file}")
    return model_path


def load_tokenizer(model_path: Path) -> Any:
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise RuntimeError("install transformers to tokenize model input") from exc
    return AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)


def encode_prompt(tokenizer: Any, prompt: str, max_input_tokens: int) -> list[int]:
    encoded = tokenizer(prompt, add_special_tokens=True, return_attention_mask=False)
    token_ids = [int(token_id) for token_id in encoded["input_ids"]]
    return token_ids[-max_input_tokens:]


def generation_unavailable_reason() -> str | None:
    try:
        import torch
    except ImportError:
        return "PyTorch is not installed"
    try:
        import transformers
    except ImportError:
        return "transformers is not installed"
    torch_version_match = re.match(r"(\d+)\.(\d+)", torch.__version__)
    transformers_version_match = re.match(r"(\d+)", transformers.__version__)
    if torch_version_match is None or transformers_version_match is None:
        return "could not determine the installed torch/transformers versions"
    torch_version = tuple(int(value) for value in torch_version_match.groups())
    transformers_major = int(transformers_version_match.group(1))
    if transformers_major >= 5 and torch_version < (2, 5):
        return (
            f"Transformers {transformers.__version__} requires PyTorch >= 2.5, "
            f"but PyTorch {torch.__version__} is installed"
        )
    return None


def generate_tokens(
    model_path: Path,
    prompt: str,
    max_input_tokens: int,
    max_new_tokens: int,
) -> tuple[Any, list[int], str, dict[str, object]]:
    unavailable_reason = generation_unavailable_reason()
    if unavailable_reason:
        raise RuntimeError(unavailable_reason)
    try:
        import torch
        from transformers import AutoModelForCausalLM
    except ImportError as exc:
        raise RuntimeError(
            "generation needs PyTorch and transformers; use --download-only for a downloader smoke test"
        ) from exc
    tokenizer_started_at = time.perf_counter()
    tokenizer = load_tokenizer(model_path)
    tokenizer_load_s = time.perf_counter() - tokenizer_started_at
    encoding_started_at = time.perf_counter()
    encoded = tokenizer(
        prompt,
        add_special_tokens=True,
        return_tensors="pt",
        truncation=True,
        max_length=max_input_tokens,
    )
    encoding_s = time.perf_counter() - encoding_started_at
    prompt_token_count = int(encoded["input_ids"].shape[-1])
    model_load_started_at = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(
        str(model_path),
        local_files_only=True,
        dtype="auto",
    )
    model_load_s = time.perf_counter() - model_load_started_at
    model.eval()
    generation_started_at = time.perf_counter()
    with torch.no_grad():
        generated = model.generate(
            **encoded,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    generation_s = time.perf_counter() - generation_started_at
    token_ids = [int(token_id) for token_id in generated[0].tolist()]
    generated_text = tokenizer.decode(generated[0], skip_special_tokens=True)
    generation_metrics = {
        "tokenizer_load_s": tokenizer_load_s,
        "prompt_encoding_s": encoding_s,
        "model_load_s": model_load_s,
        "generation_s": generation_s,
        "prompt_token_count": prompt_token_count,
        "new_token_count": max(0, len(token_ids) - prompt_token_count),
    }
    return tokenizer, token_ids, generated_text, generation_metrics


def process_usage() -> resource.struct_rusage:
    return resource.getrusage(resource.RUSAGE_SELF)


def peak_rss_mb(usage: resource.struct_rusage) -> float:
    divisor = 1024 * 1024 if sys.platform == "darwin" else 1024
    return usage.ru_maxrss / divisor


def build_profile(
    *,
    process_started_at: float,
    process_usage_before: resource.struct_rusage,
    download_s: float,
    generation_metrics: dict[str, object],
    simulation_s: float,
    token_count: int,
    power_watts: float | None,
    electricity_usd_per_kwh: float | None,
) -> dict[str, object]:
    process_usage_after = process_usage()
    total_wall_s = time.perf_counter() - process_started_at
    generation_s = float(generation_metrics.get("generation_s", 0.0))
    new_token_count = int(generation_metrics.get("new_token_count", 0))
    profile: dict[str, object] = {
        "timing_s": {
            "download": download_s,
            "tokenizer_load": float(generation_metrics.get("tokenizer_load_s", 0.0)),
            "prompt_encoding": float(generation_metrics.get("prompt_encoding_s", 0.0)),
            "model_load": float(generation_metrics.get("model_load_s", 0.0)),
            "generation": generation_s,
            "circuit_simulation": simulation_s,
            "total_wall": total_wall_s,
        },
        "cpu_time_s": {
            "user": process_usage_after.ru_utime - process_usage_before.ru_utime,
            "system": process_usage_after.ru_stime - process_usage_before.ru_stime,
        },
        "peak_rss_mb": peak_rss_mb(process_usage_after),
        "throughput": {
            "model_new_tokens_per_s": (
                new_token_count / generation_s if generation_s > 0 and new_token_count else None
            ),
            "circuit_tokens_per_s": token_count / simulation_s if simulation_s > 0 else None,
            "end_to_end_tokens_per_s": token_count / total_wall_s if total_wall_s > 0 else None,
        },
        "token_counts": {
            "prompt": int(generation_metrics.get("prompt_token_count", 0)),
            "new": new_token_count,
            "simulated": token_count,
        },
    }
    if power_watts is not None:
        energy_joules = total_wall_s * power_watts
        energy_wh = energy_joules / 3600.0
        energy_report: dict[str, object] = {
            "method": "average_power_times_wall_time",
            "assumed_average_power_watts": power_watts,
            "total_joules": energy_joules,
            "total_watt_hours": energy_wh,
            "generation_joules": generation_s * power_watts,
            "circuit_simulation_joules": simulation_s * power_watts,
        }
        if electricity_usd_per_kwh is not None:
            energy_report["electricity_cost_usd"] = energy_wh / 1000.0 * electricity_usd_per_kwh
            energy_report["electricity_usd_per_kwh"] = electricity_usd_per_kwh
        profile["energy_estimate"] = energy_report
    else:
        profile["energy_estimate"] = None
    return profile


def load_mcu_baselines(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    baselines = data.get("baselines") if isinstance(data, dict) else data
    if not isinstance(baselines, list) or not baselines:
        raise ValueError(f"baseline file must contain a non-empty baselines list: {path}")
    for baseline in baselines:
        if not isinstance(baseline, dict):
            raise ValueError(f"each MCU baseline must be an object: {path}")
        for field in ("name", "clock_hz", "cycles_per_token", "power_watts"):
            if field not in baseline:
                raise ValueError(f"MCU baseline is missing {field}: {path}")
    return baselines


def create_performance_graph(
    profile: dict[str, object],
    output_path: Path,
    baseline_path: Path,
) -> dict[str, object]:
    matplotlib_cache = Path(".cache/matplotlib").resolve()
    matplotlib_cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_cache))
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("--graph requires matplotlib; install it with pip install matplotlib") from exc
    baselines = load_mcu_baselines(baseline_path)
    throughput = profile["throughput"]
    reference_tokens_per_s = throughput.get("circuit_tokens_per_s")
    if not reference_tokens_per_s:
        raise ValueError("circuit throughput is unavailable; run a non-empty token stream")
    energy_estimate = profile.get("energy_estimate")
    reference_power_watts = (
        float(energy_estimate["assumed_average_power_watts"])
        if isinstance(energy_estimate, dict)
        else None
    )
    optimized_circuit = profile.get("optimized_circuit")
    names = ["Original circuit\n(Python host)"]
    throughput_values = [float(reference_tokens_per_s)]
    energy_values = [
        reference_power_watts / float(reference_tokens_per_s) * 1_000_000.0
        if reference_power_watts is not None
        else float("nan")
    ]
    colors = ["#1769aa"]
    if isinstance(optimized_circuit, dict):
        optimized_tokens_per_s = float(optimized_circuit["tokens_per_s"])
        names.extend(["Optimized lookup\n(Python)", "600 MHz circuit\n(ideal ceiling)"])
        throughput_values.extend([optimized_tokens_per_s, float(optimized_circuit["oscillator_hz"])])
        energy_values.extend(
            [
                reference_power_watts / optimized_tokens_per_s * 1_000_000.0
                if reference_power_watts is not None
                else float("nan"),
                float("nan"),
            ]
        )
        colors.extend(["#188038", "#e67e22"])
    for baseline in baselines:
        baseline_throughput = float(baseline["clock_hz"]) / float(baseline["cycles_per_token"])
        names.append(str(baseline["name"]))
        throughput_values.append(baseline_throughput)
        energy_values.append(float(baseline["power_watts"]) / baseline_throughput * 1_000_000.0)
    colors.extend(["#9e9e9e"] * len(baselines))
    figure, axes = plt.subplots(1, 2, figsize=(14, 7))
    positions = list(range(len(names)))
    axes[0].bar(positions, throughput_values, color=colors)
    axes[0].set_yscale("log")
    axes[0].set_ylabel("8-bit circuit evaluations / second")
    axes[0].set_title("Throughput")
    axes[0].grid(axis="y", which="both", alpha=0.25)
    axes[1].bar(positions, energy_values, color=colors)
    axes[1].set_yscale("log")
    axes[1].set_ylabel("Estimated energy / evaluation (µJ)")
    axes[1].set_title("Energy estimate")
    axes[1].grid(axis="y", which="both", alpha=0.25)
    for axis in axes:
        axis.set_xticks(positions)
        axis.set_xticklabels(names, rotation=35, ha="right")
    figure.suptitle("Entanglement circuit workload comparison")
    figure.text(
        0.5,
        0.01,
        "Original/optimized bars are measured Python models; 600 MHz is an ideal hardware clock ceiling. MCU bars use clock_hz / cycles_per_token estimates; replace with board measurements.",
        ha="center",
        fontsize=8,
    )
    figure.tight_layout(rect=(0, 0.07, 1, 0.95))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160)
    plt.close(figure)
    return {
        "output": str(output_path),
        "baseline_file": str(baseline_path),
        "reference_circuit_tokens_per_s": reference_tokens_per_s,
        "optimized_circuit_tokens_per_s": (
            optimized_circuit.get("tokens_per_s") if isinstance(optimized_circuit, dict) else None
        ),
        "energy_panel_has_reference_measurement": reference_power_watts is not None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache/huggingface"))
    parser.add_argument("--prompt", default="Describe the signal path in one sentence.")
    parser.add_argument("--max-input-tokens", type=int, default=64)
    parser.add_argument("--max-new-tokens", type=int, default=16)
    parser.add_argument("--download-only", action="store_true")
    parser.add_argument("--require-generation", action="store_true")
    parser.add_argument(
        "--power-watts",
        type=float,
        help="Average measured system power used for an energy estimate",
    )
    parser.add_argument(
        "--electricity-usd-per-kwh",
        type=float,
        help="Optional electricity price for an estimated run cost",
    )
    parser.add_argument("--graph", action="store_true", help="Write a matplotlib MCU comparison graph")
    parser.add_argument(
        "--graph-output",
        type=Path,
        default=Path("results/entanglement-performance.png"),
    )
    parser.add_argument("--baseline-file", type=Path, default=DEFAULT_BASELINES)
    parser.add_argument("--graph-samples", type=int, default=100_000)
    parser.add_argument(
        "--optimized-circuit",
        action="store_true",
        help="Use the reduced-component lookup/latch circuit for the trace",
    )
    parser.add_argument("--oscillator-hz", type=float, default=600_000_000.0)
    parser.add_argument("--preempt-index", type=int)
    parser.add_argument("--preempt-token-id", type=int)
    parser.add_argument("--netlist", type=Path, default=DEFAULT_NETLIST)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    process_started_at = time.perf_counter()
    process_usage_before = process_usage()
    download_started_at = time.perf_counter()
    model_path = download_safetensors_model(arguments.model_id, arguments.cache_dir)
    download_s = time.perf_counter() - download_started_at
    safe_files = sorted(model_path.glob("*.safetensors"))
    report: dict[str, object] = {
        "model_id": arguments.model_id,
        "model_path": str(model_path),
        "safetensors": [str(path) for path in safe_files],
    }
    if arguments.download_only:
        if arguments.graph:
            raise ValueError("--graph requires model/circuit execution, not --download-only")
        report["profile"] = build_profile(
            process_started_at=process_started_at,
            process_usage_before=process_usage_before,
            download_s=download_s,
            generation_metrics={},
            simulation_s=0.0,
            token_count=0,
            power_watts=arguments.power_watts,
            electricity_usd_per_kwh=arguments.electricity_usd_per_kwh,
        )
        print(json.dumps(report, indent=2))
        return 0
    if arguments.max_new_tokens < 0:
        raise ValueError("--max-new-tokens cannot be negative")
    generation_backend = "transformers"
    generation_error = None
    generation_metrics: dict[str, object] = {}
    try:
        tokenizer, token_ids, generated_text, generation_metrics = generate_tokens(
            model_path,
            arguments.prompt,
            arguments.max_input_tokens,
            arguments.max_new_tokens,
        )
    except RuntimeError as exc:
        if arguments.require_generation:
            raise
        tokenizer_started_at = time.perf_counter()
        tokenizer = load_tokenizer(model_path)
        tokenizer_load_s = time.perf_counter() - tokenizer_started_at
        encoding_started_at = time.perf_counter()
        token_ids = encode_prompt(tokenizer, arguments.prompt, arguments.max_input_tokens)
        encoding_s = time.perf_counter() - encoding_started_at
        generated_text = tokenizer.decode(token_ids, skip_special_tokens=True)
        generation_backend = "tokenizer-only"
        generation_error = str(exc)
        generation_metrics = {
            "tokenizer_load_s": tokenizer_load_s,
            "prompt_encoding_s": encoding_s,
            "model_load_s": 0.0,
            "generation_s": 0.0,
            "prompt_token_count": len(token_ids),
            "new_token_count": 0,
        }
        print(f"warning: {exc}; running tokenizer-only circuit bridge", file=sys.stderr)
    if arguments.preempt_index is not None and arguments.preempt_token_id is None:
        raise ValueError("--preempt-index requires --preempt-token-id")
    preemptions = {}
    if arguments.preempt_index is not None:
        preemptions[arguments.preempt_index] = arguments.preempt_token_id
    selected_netlist = arguments.netlist
    if arguments.optimized_circuit and selected_netlist == DEFAULT_NETLIST:
        selected_netlist = DEFAULT_OPTIMIZED_NETLIST
    loaded_netlist = SpiceNetlist.load(selected_netlist)
    if arguments.optimized_circuit:
        simulator = OptimizedEntanglementSimulator(
            loaded_netlist,
            oscillator_hz=arguments.oscillator_hz,
        )
    else:
        simulator = EntanglementSimulator(loaded_netlist)
    simulation_started_at = time.perf_counter()
    trace = simulator.run_token_stream(token_ids, preemptions=preemptions)
    simulation_s = time.perf_counter() - simulation_started_at
    profile = build_profile(
        process_started_at=process_started_at,
        process_usage_before=process_usage_before,
        download_s=download_s,
        generation_metrics=generation_metrics,
        simulation_s=simulation_s,
        token_count=len(token_ids),
        power_watts=arguments.power_watts,
        electricity_usd_per_kwh=arguments.electricity_usd_per_kwh,
    )
    if arguments.graph:
        optimized_simulator = OptimizedEntanglementSimulator(
            SpiceNetlist.load(DEFAULT_OPTIMIZED_NETLIST),
            oscillator_hz=arguments.oscillator_hz,
        )
        profile["optimized_circuit"] = optimized_simulator.benchmark(
            token_ids,
            sample_count=arguments.graph_samples,
        )
    report.update(
        {
            "prompt": arguments.prompt,
            "generated_text": generated_text,
            "token_ids": token_ids,
            "token_count": len(token_ids),
            "trace": trace,
            "tokenizer": tokenizer.__class__.__name__,
            "generation_backend": generation_backend,
            "profile": profile,
        }
    )
    if generation_error:
        report["generation_error"] = generation_error
    if arguments.graph:
        report["graph"] = create_performance_graph(
            profile,
            arguments.graph_output,
            arguments.baseline_file,
        )
    output = json.dumps(report, indent=2)
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
