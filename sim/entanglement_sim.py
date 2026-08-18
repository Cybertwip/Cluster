#!/usr/bin/env python3
"""Deterministic event-driven model of the circuit abstraction."""

from __future__ import annotations

import argparse
import heapq
import json
import math
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_NETLIST = Path(__file__).resolve().parents[1] / "kicad" / "entanglement.cir"


@dataclass(frozen=True)
class NetComponent:
    reference: str
    nodes: tuple[str, ...]
    value: str


class SpiceNetlist:
    """Small parser used to keep the Python model tied to the reference netlist."""

    def __init__(self, components: Sequence[NetComponent]) -> None:
        self.components = tuple(components)

    @classmethod
    def load(cls, path: Path) -> "SpiceNetlist":
        components: list[NetComponent] = []
        in_control_block = False
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line.lower() == ".control":
                in_control_block = True
                continue
            if line.lower() == ".endc":
                in_control_block = False
                continue
            if in_control_block or not line or line.startswith("*") or line.startswith("."):
                continue
            if line.lower().startswith(("set ", "tran ", "write ")):
                continue
            fields = line.split()
            if len(fields) < 4:
                continue
            reference = fields[0]
            if reference.upper().startswith("B_"):
                nodes = tuple(fields[1:3])
                value = " ".join(fields[3:])
            else:
                nodes = tuple(fields[1:3])
                value = " ".join(fields[3:])
            components.append(NetComponent(reference, nodes, value))
        return cls(components)

    @property
    def references(self) -> set[str]:
        return {component.reference for component in self.components}

    @property
    def nodes(self) -> set[str]:
        return {node for component in self.components for node in component.nodes}

    def summary(self) -> dict[str, object]:
        return {
            "component_count": len(self.components),
            "behavioral_sources": sorted(
                component.reference
                for component in self.components
                if component.reference.upper().startswith("B_")
            ),
            "nodes": sorted(self.nodes),
        }

    def validate(self) -> None:
        required_nodes = {
            "vcc",
            "0",
            "ent_a",
            "ent_b",
            "superposition",
            "sample_hold",
            "measured",
        }
        missing_nodes = sorted(required_nodes - self.nodes)
        if missing_nodes:
            raise ValueError(f"reference netlist is missing nodes: {', '.join(missing_nodes)}")


@dataclass(frozen=True)
class InputEvent:
    time_s: float
    token_id: int
    priority: int = 0
    source: str = "host"


def clamp(value: float, lower: float = 0.0, upper: float = 5.0) -> float:
    return max(lower, min(upper, value))


def byte_bits(byte_value: int) -> tuple[int, ...]:
    normalized = byte_value & 0xFF
    return tuple((normalized >> bit_index) & 1 for bit_index in range(8))


class EntanglementSimulator:
    """A clocked behavioral simulator with prioritized input preemption."""

    def __init__(
        self,
        netlist: SpiceNetlist,
        clock_hz: float = 8_000.0,
        supply_v: float = 5.0,
    ) -> None:
        netlist.validate()
        if clock_hz <= 0:
            raise ValueError("clock_hz must be positive")
        self.netlist = netlist
        self.clock_hz = clock_hz
        self.clock_period_s = 1.0 / clock_hz
        self.supply_v = supply_v
        self._event_queue: list[tuple[float, int, int, InputEvent]] = []
        self._event_serial = 0
        self._active_event = InputEvent(0.0, 0, source="reset")

    def schedule(
        self,
        token_id: int,
        time_s: float,
        *,
        preempt: bool = False,
        source: str = "host",
    ) -> None:
        if time_s < 0:
            raise ValueError("event time cannot be negative")
        priority = 100 if preempt else 0
        event = InputEvent(time_s, int(token_id), priority, source)
        heapq.heappush(
            self._event_queue,
            (event.time_s, event.priority, self._event_serial, event),
        )
        self._event_serial += 1

    def preempt(self, token_id: int, time_s: float, source: str = "interrupt") -> None:
        self.schedule(token_id, time_s, preempt=True, source=source)

    def _consume_events(self, time_s: float) -> bool:
        preempted = False
        while self._event_queue and self._event_queue[0][0] <= time_s + 1e-15:
            _, _, _, event = heapq.heappop(self._event_queue)
            preempted = preempted or event.priority > 0
            self._active_event = event
        return preempted

    def _evaluate(self, time_s: float, preempted: bool) -> dict[str, object]:
        byte_value = self._active_event.token_id & 0xFF
        bits = byte_bits(byte_value)
        signed_bits = tuple((2 * bit_value) - 1 for bit_value in bits)
        weighted_signal = sum(
            signed_value * (1.0 + (bit_index % 3) * 0.07)
            for bit_index, signed_value in enumerate(signed_bits)
        ) / 8.56
        phase_a = math.sin(2.0 * math.pi * 8_000.0 * time_s)
        phase_b = math.sin(2.0 * math.pi * 8_200.0 * time_s + math.pi / 5.0)
        coupling = math.tanh(0.78 * weighted_signal + 0.22 * phase_a * phase_b)
        entanglement_a = clamp(2.5 + 2.0 * math.tanh(coupling + 0.18 * phase_a))
        entanglement_b = clamp(2.5 + 2.0 * math.tanh(coupling + 0.18 * phase_b))
        superposition = clamp(0.5 * (entanglement_a + entanglement_b))
        collapse = 1.0 if superposition >= 2.5 else 0.0
        feature_values = tuple(
            clamp(
                2.5
                + 1.65 * signed_value
                + 0.24 * (entanglement_a - 2.5)
                + 0.18 * (entanglement_b - 2.5)
                + 0.08 * math.sin(time_s * 2.0 * math.pi * (bit_index + 1) * 1000.0)
            )
            for bit_index, signed_value in enumerate(signed_bits)
        )
        output_byte = sum(
            (1 << bit_index)
            for bit_index, feature_value in enumerate(feature_values)
            if feature_value >= 2.5
        )
        return {
            "time_s": round(time_s, 12),
            "token_id": self._active_event.token_id,
            "input_byte": byte_value,
            "input_bits": list(bits),
            "entanglement_a": round(entanglement_a, 6),
            "entanglement_b": round(entanglement_b, 6),
            "superposition": round(superposition, 6),
            "collapse": int(collapse),
            "feature_voltages": [round(feature_value, 6) for feature_value in feature_values],
            "output_byte": output_byte,
            "output_bits": list(byte_bits(output_byte)),
            "preempted": preempted,
            "source": self._active_event.source,
        }

    def run(self, sample_count: int) -> list[dict[str, object]]:
        if sample_count < 0:
            raise ValueError("sample_count cannot be negative")
        trace: list[dict[str, object]] = []
        for sample_index in range(sample_count):
            time_s = sample_index * self.clock_period_s
            preempted = self._consume_events(time_s)
            trace.append(self._evaluate(time_s, preempted))
        return trace

    def run_token_stream(
        self,
        token_ids: Iterable[int],
        *,
        preemptions: dict[int, int] | None = None,
    ) -> list[dict[str, object]]:
        token_list = [int(token_id) for token_id in token_ids]
        preemptions = preemptions or {}
        for token_index, token_id in enumerate(token_list):
            self.schedule(token_id, token_index * self.clock_period_s, source="model")
        for token_index, token_id in preemptions.items():
            if token_index < 0 or token_index >= len(token_list):
                raise ValueError(f"preemption index {token_index} is outside the token stream")
            self.preempt(token_id, token_index * self.clock_period_s)
        return self.run(len(token_list))


class OptimizedEntanglementSimulator:
    """Reduced-component lookup model for the 600 MHz RF/latch reference path."""

    def __init__(
        self,
        netlist: SpiceNetlist,
        oscillator_hz: float = 600_000_000.0,
        supply_v: float = 5.0,
    ) -> None:
        netlist.validate()
        if oscillator_hz <= 0:
            raise ValueError("oscillator_hz must be positive")
        self.netlist = netlist
        self.oscillator_hz = oscillator_hz
        self.clock_period_s = 1.0 / oscillator_hz
        self.supply_v = supply_v
        self._lookup = tuple(self._compile_state(byte_value) for byte_value in range(256))

    def _compile_state(self, byte_value: int) -> tuple[float, float, float, int, tuple[float, ...], int]:
        bits = byte_bits(byte_value)
        signed_bits = tuple((2 * bit_value) - 1 for bit_value in bits)
        weighted_signal = sum(
            signed_value * (1.0 + (bit_index % 3) * 0.07)
            for bit_index, signed_value in enumerate(signed_bits)
        ) / 8.56
        coupling = math.tanh(0.78 * weighted_signal)
        entanglement_a = clamp(2.5 + 2.0 * coupling)
        entanglement_b = clamp(2.5 + 2.0 * math.tanh(coupling * 1.04))
        superposition = clamp(0.5 * (entanglement_a + entanglement_b))
        collapse = int(superposition >= 2.5)
        feature_values = tuple(
            clamp(
                2.5
                + 1.65 * signed_value
                + 0.24 * (entanglement_a - 2.5)
                + 0.18 * (entanglement_b - 2.5)
            )
            for signed_value in signed_bits
        )
        output_byte = sum(
            (1 << bit_index)
            for bit_index, feature_value in enumerate(feature_values)
            if feature_value >= 2.5
        )
        return entanglement_a, entanglement_b, superposition, collapse, feature_values, output_byte

    def _record(
        self,
        token_id: int,
        sample_index: int,
        preempted: bool,
        source: str,
    ) -> dict[str, object]:
        byte_value = token_id & 0xFF
        entanglement_a, entanglement_b, superposition, collapse, feature_values, output_byte = self._lookup[
            byte_value
        ]
        return {
            "time_s": round(sample_index * self.clock_period_s, 15),
            "token_id": token_id,
            "input_byte": byte_value,
            "input_bits": list(byte_bits(byte_value)),
            "entanglement_a": round(entanglement_a, 6),
            "entanglement_b": round(entanglement_b, 6),
            "superposition": round(superposition, 6),
            "collapse": collapse,
            "feature_voltages": [round(value, 6) for value in feature_values],
            "output_byte": output_byte,
            "output_bits": list(byte_bits(output_byte)),
            "preempted": preempted,
            "source": source,
        }

    def run_token_stream(
        self,
        token_ids: Iterable[int],
        *,
        preemptions: dict[int, int] | None = None,
    ) -> list[dict[str, object]]:
        token_list = [int(token_id) for token_id in token_ids]
        preemptions = preemptions or {}
        trace: list[dict[str, object]] = []
        for token_index, token_id in enumerate(token_list):
            if token_index in preemptions:
                token_id = int(preemptions[token_index])
                trace.append(self._record(token_id, token_index, True, "interrupt"))
            else:
                trace.append(self._record(token_id, token_index, False, "model"))
        return trace

    def benchmark(self, token_ids: Sequence[int], sample_count: int = 100_000) -> dict[str, object]:
        if not token_ids:
            raise ValueError("optimized benchmark needs at least one token")
        if sample_count <= 0:
            raise ValueError("sample_count must be positive")
        started_at = time.perf_counter()
        accumulator = 0
        for sample_index in range(sample_count):
            state = self._lookup[token_ids[sample_index % len(token_ids)] & 0xFF]
            accumulator = (accumulator + state[5] + state[3]) & 0xFFFFFFFF
        elapsed_s = time.perf_counter() - started_at
        return {
            "oscillator_hz": self.oscillator_hz,
            "sample_count": sample_count,
            "elapsed_s": elapsed_s,
            "tokens_per_s": sample_count / elapsed_s if elapsed_s > 0 else None,
            "checksum": accumulator,
        }


def read_events(path: Path) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON on line {line_number}: {exc}") from exc
        if "token_id" not in event:
            raise ValueError(f"event on line {line_number} has no token_id")
        events.append(event)
    return events


def run_event_file(simulator: EntanglementSimulator, events: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    if not events:
        return []
    for event in events:
        time_s = float(event.get("time_s", 0.0))
        token_id = int(event["token_id"])
        simulator.schedule(
            token_id,
            time_s,
            preempt=bool(event.get("preempt", False)),
            source=str(event.get("source", "host")),
        )
    last_time_s = max(float(event.get("time_s", 0.0)) for event in events)
    sample_count = math.floor(last_time_s / simulator.clock_period_s) + 1
    return simulator.run(sample_count)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, default=DEFAULT_NETLIST)
    parser.add_argument("--text", help="Encode UTF-8 bytes as input events")
    parser.add_argument("--token-id", type=int, action="append", default=[])
    parser.add_argument("--events", type=Path)
    parser.add_argument("--steps", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--clock-hz", type=float, default=8_000.0)
    return parser.parse_args()


def write_jsonl(path: Path, trace: Sequence[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(sample, sort_keys=True) + "\n" for sample in trace),
        encoding="utf-8",
    )


def main() -> int:
    arguments = parse_args()
    netlist = SpiceNetlist.load(arguments.netlist)
    simulator = EntanglementSimulator(netlist, clock_hz=arguments.clock_hz)
    if arguments.events:
        trace = run_event_file(simulator, read_events(arguments.events))
    else:
        token_ids = list(arguments.token_id)
        if arguments.text is not None:
            token_ids.extend(arguments.text.encode("utf-8"))
        if not token_ids:
            token_ids = [0]
        sample_count = arguments.steps if arguments.steps is not None else len(token_ids)
        if sample_count < 0:
            raise ValueError("--steps cannot be negative")
        trace = simulator.run_token_stream(token_ids[:sample_count])
    if arguments.output:
        write_jsonl(arguments.output, trace)
    print(json.dumps({"netlist": netlist.summary(), "samples": len(trace), "trace": trace}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
