# Entanglement / superposition circuit model

This project turns the schematic in `/Users/cybertwip/Desktop/entanglement.pdf` into a usable KiCad and simulation artifact.

The source PDF contains a low-resolution picture of an illustrative analog circuit. Component values and several reference designators cannot be recovered reliably from that image, so this project uses a documented functional abstraction rather than presenting guessed values as an exact reverse-engineering result.

The abstraction keeps the visible structure:

- 5 V supply and oscillator/coupling front end
- Two coupled signal paths for the entanglement unit
- Op-amp averaging/superposition stage
- Thresholded sample-and-collapse stage
- Eight LED output channels
- External token input, strobe, and high-priority preemption control

This is a classical analog-inspired signal processor. It does not create quantum entanglement and it is not an LLM accelerator. The LLM integration is an experiment that encodes model token IDs into an 8-bit input bus, runs the deterministic circuit abstraction, and records the resulting analog features and collapsed byte.

## Files

- `kicad/entanglement.kicad_sch` — KiCad 9 native signal-flow schematic and named-net block diagram.
- `kicad/entanglement.sch` — detailed legacy component drawing retained for older KiCad import workflows.
- `kicad/entanglement.cir` — matching ngspice behavioral netlist.
- `kicad/entanglement_optimized.kicad_sch` / `kicad/entanglement_optimized.cir` — reduced-component 600 MHz RF/latch reference path.
- `sim/entanglement_sim.py` — pure-Python netlist reader and event-driven circuit model.
- `sim/run_llm.py` — safetensors-only model downloader and token-to-circuit bridge.
- `tests/test_simulator.py` — simulator and preemption tests.

## Run the circuit simulation

The simulator has no mandatory third-party dependency:

```bash
python3 sim/entanglement_sim.py --text "hello" --output results/chip.jsonl
python3 -m unittest discover -s tests -v
```

Inject events from JSONL. `preempt: true` gives an event priority over a regular event at the same clock edge:

```json
{"time_s": 0.0, "token_id": 72}
{"time_s": 0.000125, "token_id": 101, "preempt": true, "source": "interrupt"}
```

```bash
python3 sim/entanglement_sim.py --events events.jsonl --output results/events.jsonl
```

## Check the ngspice netlist

```bash
ngspice -b -o results/ngspice.log kicad/entanglement.cir
```

The netlist is intentionally behavioral. It is suitable for checking the signal-level idea and the output timing, not for selecting production components or validating a PCB.

## Download and exercise a small LLM

The default is `HuggingFaceTB/SmolLM2-135M-Instruct`, which is small enough for a local smoke test and publishes a `model.safetensors` file. The bridge filters out pickle/PyTorch binary weight formats and verifies the downloaded safetensors files before loading them.

Install the optional model runtime in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If an existing environment already has Transformers 5.x, repair it with:

```bash
python -m pip install --upgrade "transformers>=4.46,<5" "torch>=2.2,<2.5"
```

Download the model and tokenizer without running generation:

```bash
python sim/run_llm.py --download-only
```

Generate a short continuation, feed every generated token through the circuit model, and save the trace:

```bash
python sim/run_llm.py \
  --prompt "Explain what this circuit measures." \
  --max-new-tokens 16 \
  --preempt-index 4 \
  --preempt-token-id 32 \
  --output results/smollm-chip.json
```

Create a matplotlib performance graph and include a configurable energy estimate:

```bash
python sim/run_llm.py \
  --graph \
  --power-watts 15 \
  --graph-output results/entanglement-performance.png \
  --output results/smollm-chip-profile.json
```

The graph compares the measured Python circuit throughput with the illustrative profiles in `sim/mcu_baselines.json`. Those MCU bars use `clock_hz / cycles_per_token`; replace that file with measurements from real boards before drawing hardware conclusions. `--power-watts` must be an average measured power value if you want meaningful joules or electricity cost.

With `--graph`, the plot also includes the reduced lookup/latch model and a 600 MHz ideal hardware-clock ceiling. The optimized Python bar is a software benchmark; it is not a claim that Python or the original 555/LM358 circuit operates at 600 MHz.

To run the reduced path for the trace, use `--optimized-circuit`. Its component reduction assumes an RF oscillator/PLL, RF mixer or comparator, latch, and digital output interface rather than discrete low-frequency timer/op-amp stages.

Generation requires a PyTorch build compatible with the host. On Apple Silicon, an MLX backend can be added later, but the simulator and downloader do not depend on MLX.

When generation dependencies are unavailable, `run_llm.py` now falls back to tokenizing the prompt and still sends those token IDs through the circuit. Pass `--require-generation` when a hard failure is preferred.

## Interpreting results

The JSON report includes `entanglement_a`, `entanglement_b`, `superposition`, `collapse`, `output_byte`, and `preempted` for each clock. Useful experiments are:

1. Run a token trace with no preemption.
2. Repeat with one preemption at a clock edge.
3. Compare output bytes and collapse transitions.
4. Compare the model's generated text; the circuit features are diagnostics, not replacement logits.

The report profile includes model load/generation time, circuit simulation time, CPU time, peak RSS, throughput, and optional energy estimates. The energy estimate is `average power × wall time`; it is not a direct power measurement.
