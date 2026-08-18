import unittest
from pathlib import Path

from sim.entanglement_sim import EntanglementSimulator, OptimizedEntanglementSimulator, SpiceNetlist


ROOT = Path(__file__).resolve().parents[1]
NETLIST_PATH = ROOT / "kicad" / "entanglement.cir"


class EntanglementSimulatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.netlist = SpiceNetlist.load(NETLIST_PATH)

    def test_reference_netlist_contains_signal_blocks(self) -> None:
        self.netlist.validate()
        self.assertIn("B_ENT_A", self.netlist.references)
        self.assertIn("B_SUP", self.netlist.references)
        self.assertIn("B_COLLAPSE", self.netlist.references)

    def test_token_stream_is_deterministic(self) -> None:
        first = EntanglementSimulator(self.netlist).run_token_stream([65, 66, 67])
        second = EntanglementSimulator(self.netlist).run_token_stream([65, 66, 67])
        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        self.assertTrue(all(0 <= sample["output_byte"] <= 255 for sample in first))

    def test_preempted_event_wins_at_same_clock_edge(self) -> None:
        trace = EntanglementSimulator(self.netlist).run_token_stream(
            [10, 20, 30],
            preemptions={1: 255},
        )
        self.assertEqual(trace[1]["token_id"], 255)
        self.assertTrue(trace[1]["preempted"])
        self.assertEqual(trace[0]["token_id"], 10)

    def test_optimized_path_preserves_preemption_and_clock(self) -> None:
        optimized_netlist = SpiceNetlist.load(ROOT / "kicad" / "entanglement_optimized.cir")
        simulator = OptimizedEntanglementSimulator(optimized_netlist)
        trace = simulator.run_token_stream([10, 20], preemptions={1: 255})
        self.assertEqual(simulator.oscillator_hz, 600_000_000.0)
        self.assertEqual(trace[1]["token_id"], 255)
        self.assertTrue(trace[1]["preempted"])

    def test_optimized_benchmark_returns_throughput(self) -> None:
        optimized_netlist = SpiceNetlist.load(ROOT / "kicad" / "entanglement_optimized.cir")
        benchmark = OptimizedEntanglementSimulator(optimized_netlist).benchmark([1, 2], 1000)
        self.assertGreater(benchmark["tokens_per_s"], 0)


if __name__ == "__main__":
    unittest.main()
