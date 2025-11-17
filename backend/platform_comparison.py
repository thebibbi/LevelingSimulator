"""
Platform Comparison Demo
Demonstrates and compares both 3-actuator tripod and Stewart platform configurations
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from inverse_kinematics import PlatformConfig, StewartPlatformIK, TripodIK


class PlatformComparison:
    """
    Compare performance of different platform configurations
    """

    def __init__(self):
        # Standard platform configuration
        self.config = PlatformConfig(
            length=1.83, width=1.22, min_height=0.3, max_height=0.7, actuator_stroke=0.4
        )

        # Initialize both solvers
        self.tripod = TripodIK(self.config)
        self.stewart_3dof = StewartPlatformIK(self.config, dof_mode="3DOF")
        self.stewart_6dof = StewartPlatformIK(self.config, dof_mode="6DOF")

        # Test angles
        self.test_angles = [
            (0, 0, 0, "Level"),
            (5, 0, 0, "5° Roll"),
            (0, 5, 0, "5° Pitch"),
            (5, 5, 0, "5° Roll + 5° Pitch"),
            (10, 0, 0, "10° Roll"),
            (0, 10, 0, "10° Pitch"),
            (10, 10, 0, "10° Roll + 10° Pitch"),
            (15, 0, 0, "15° Roll (Max)"),
            (0, 15, 0, "15° Pitch (Max)"),
            (10, 10, 15, "10° Roll + 10° Pitch + 15° Yaw"),
        ]

    def run_comparison(self):
        """Run comparison tests"""
        print("=" * 80)
        print("PLATFORM CONFIGURATION COMPARISON")
        print("=" * 80)
        print(f"\nPlatform: {self.config.length*1000:.0f}mm × {self.config.width*1000:.0f}mm")
        print(
            f"Height range: {self.config.min_height*1000:.0f}mm - {self.config.max_height*1000:.0f}mm"
        )
        print(f"Actuator stroke: {self.config.actuator_stroke*1000:.0f}mm\n")

        results = {"tripod": [], "stewart_3dof": [], "stewart_6dof": []}

        # Test each configuration
        for roll_deg, pitch_deg, yaw_deg, desc in self.test_angles:
            print(f"\nTest: {desc}")
            print("-" * 60)

            roll = np.deg2rad(roll_deg)
            pitch = np.deg2rad(pitch_deg)
            yaw = np.deg2rad(yaw_deg)

            # Tripod (no yaw control)
            lengths_t, valid_t = self.tripod.solve(roll, pitch, 0)
            stroke_t = np.max(lengths_t) - np.min(lengths_t)
            results["tripod"].append(
                {
                    "desc": desc,
                    "valid": valid_t,
                    "lengths": lengths_t * 1000,  # Convert to mm
                    "stroke_range": stroke_t * 1000,
                    "max_extension": np.max(lengths_t) * 1000,
                    "angles": (roll_deg, pitch_deg, 0),
                }
            )

            print(f"  Tripod (3 actuators):")
            if valid_t:
                print(f"    Lengths: {lengths_t * 1000}")
                print(f"    Stroke range: {stroke_t * 1000:.1f}mm")
                print(f"    Max extension: {np.max(lengths_t) * 1000:.1f}mm")
            else:
                print(f"    ✗ INVALID - exceeds actuator limits")

            # Stewart 3-DOF
            lengths_s3, valid_s3 = self.stewart_3dof.solve(roll, pitch, 0)
            stroke_s3 = np.max(lengths_s3) - np.min(lengths_s3)
            results["stewart_3dof"].append(
                {
                    "desc": desc,
                    "valid": valid_s3,
                    "lengths": lengths_s3 * 1000,
                    "stroke_range": stroke_s3 * 1000,
                    "max_extension": np.max(lengths_s3) * 1000,
                    "angles": (roll_deg, pitch_deg, 0),
                }
            )

            print(f"  Stewart 3-DOF (6 actuators):")
            if valid_s3:
                print(f"    Lengths: {lengths_s3 * 1000}")
                print(f"    Stroke range: {stroke_s3 * 1000:.1f}mm")
                print(f"    Max extension: {np.max(lengths_s3) * 1000:.1f}mm")
            else:
                print(f"    ✗ INVALID - exceeds actuator limits")

            # Stewart 6-DOF (only if yaw != 0)
            if yaw_deg != 0:
                lengths_s6, valid_s6 = self.stewart_6dof.solve(roll, pitch, yaw)
                stroke_s6 = np.max(lengths_s6) - np.min(lengths_s6)
                results["stewart_6dof"].append(
                    {
                        "desc": desc,
                        "valid": valid_s6,
                        "lengths": lengths_s6 * 1000,
                        "stroke_range": stroke_s6 * 1000,
                        "max_extension": np.max(lengths_s6) * 1000,
                        "angles": (roll_deg, pitch_deg, yaw_deg),
                    }
                )

                print(f"  Stewart 6-DOF (6 actuators with yaw):")
                if valid_s6:
                    print(f"    Lengths: {lengths_s6 * 1000}")
                    print(f"    Stroke range: {stroke_s6 * 1000:.1f}mm")
                    print(f"    Max extension: {np.max(lengths_s6) * 1000:.1f}mm")
                else:
                    print(f"    ✗ INVALID - exceeds actuator limits")

        # Summary
        self._print_summary(results)

        # Generate comparison plots
        self._plot_comparison(results)

    def _print_summary(self, results):
        """Print comparison summary"""
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        # Count valid solutions
        tripod_valid = sum(1 for r in results["tripod"] if r["valid"])
        stewart_3_valid = sum(1 for r in results["stewart_3dof"] if r["valid"])

        print(f"\nValid Solutions (out of {len(results['tripod'])} tests):")
        print(f"  Tripod:        {tripod_valid}/{len(results['tripod'])}")
        print(f"  Stewart 3-DOF: {stewart_3_valid}/{len(results['stewart_3dof'])}")

        # Average stroke range for valid solutions
        tripod_avg_stroke = np.mean([r["stroke_range"] for r in results["tripod"] if r["valid"]])
        stewart_avg_stroke = np.mean(
            [r["stroke_range"] for r in results["stewart_3dof"] if r["valid"]]
        )

        print(f"\nAverage Stroke Range (for valid solutions):")
        print(f"  Tripod:        {tripod_avg_stroke:.1f}mm")
        print(f"  Stewart 3-DOF: {stewart_avg_stroke:.1f}mm")

        # Cost comparison
        print(f"\nEstimated Cost:")
        print(f"  Tripod:        $700-800 (3 actuators)")
        print(f"  Stewart 3-DOF: $1,150-1,300 (6 actuators)")
        print(f"  Stewart 6-DOF: $1,150-1,300 (6 actuators + yaw control)")

        # Recommendations
        print(f"\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)

        print("\nTRIPOD (3 actuators):")
        print("  ✓ Simpler design")
        print("  ✓ Lower cost (~$700)")
        print("  ✓ Fewer parts to fail")
        print("  ✓ Easier to install")
        print("  ✗ No yaw control")
        print("  → RECOMMENDED FOR MVP")

        print("\nSTEWART 3-DOF (6 actuators):")
        print("  ✓ More precise leveling")
        print("  ✓ Better load distribution")
        print("  ✓ Can upgrade to 6-DOF later")
        print("  ✗ Higher cost (~$1,150)")
        print("  ✗ More complex")
        print("  → RECOMMENDED FOR PRODUCTION")

        print("\nSTEWART 6-DOF (6 actuators + yaw):")
        print("  ✓ Full orientation control")
        print("  ✓ Can compensate for vehicle yaw")
        print("  ✓ Best performance")
        print("  ✗ Highest complexity")
        print("  ✗ May not be needed for tent leveling")
        print("  → OPTIONAL UPGRADE")

    def _plot_comparison(self, results):
        """Generate comparison plots"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # Extract data for tripod
        tripod_valid_idx = [i for i, r in enumerate(results["tripod"]) if r["valid"]]
        tripod_strokes = [results["tripod"][i]["stroke_range"] for i in tripod_valid_idx]
        tripod_labels = [results["tripod"][i]["desc"] for i in tripod_valid_idx]

        # Extract data for Stewart 3-DOF
        stewart_valid_idx = [i for i, r in enumerate(results["stewart_3dof"]) if r["valid"]]
        stewart_strokes = [results["stewart_3dof"][i]["stroke_range"] for i in stewart_valid_idx]
        stewart_labels = [results["stewart_3dof"][i]["desc"] for i in stewart_valid_idx]

        # Plot 1: Stroke range comparison
        ax = axes[0, 0]
        x = np.arange(len(tripod_valid_idx))
        width = 0.35
        ax.bar(x - width / 2, tripod_strokes, width, label="Tripod", alpha=0.8)
        ax.bar(x + width / 2, stewart_strokes, width, label="Stewart 3-DOF", alpha=0.8)
        ax.set_xlabel("Test Configuration")
        ax.set_ylabel("Stroke Range (mm)")
        ax.set_title("Actuator Stroke Range Comparison")
        ax.set_xticks(x)
        ax.set_xticklabels(tripod_labels, rotation=45, ha="right")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Plot 2: Max extension comparison
        ax = axes[0, 1]
        tripod_max = [results["tripod"][i]["max_extension"] for i in tripod_valid_idx]
        stewart_max = [results["stewart_3dof"][i]["max_extension"] for i in stewart_valid_idx]
        ax.bar(x - width / 2, tripod_max, width, label="Tripod", alpha=0.8)
        ax.bar(x + width / 2, stewart_max, width, label="Stewart 3-DOF", alpha=0.8)
        ax.axhline(
            y=self.config.max_height * 1000, color="r", linestyle="--", label="Max Limit", alpha=0.7
        )
        ax.set_xlabel("Test Configuration")
        ax.set_ylabel("Maximum Extension (mm)")
        ax.set_title("Maximum Actuator Extension")
        ax.set_xticks(x)
        ax.set_xticklabels(tripod_labels, rotation=45, ha="right")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Plot 3: Actuator length distribution (box plot)
        ax = axes[1, 0]
        tripod_all_lengths = []
        stewart_all_lengths = []
        for r in results["tripod"]:
            if r["valid"]:
                tripod_all_lengths.extend(r["lengths"])
        for r in results["stewart_3dof"]:
            if r["valid"]:
                stewart_all_lengths.extend(r["lengths"])

        ax.boxplot(
            [tripod_all_lengths, stewart_all_lengths],
            labels=["Tripod\n(3 actuators)", "Stewart 3-DOF\n(6 actuators)"],
        )
        ax.set_ylabel("Actuator Length (mm)")
        ax.set_title("Actuator Length Distribution")
        ax.grid(True, alpha=0.3)

        # Plot 4: Cost vs Performance
        ax = axes[1, 1]
        configs = ["Tripod", "Stewart\n3-DOF", "Stewart\n6-DOF"]
        costs = [750, 1225, 1225]  # Average costs
        performance = [85, 95, 100]  # Relative performance scores

        ax2 = ax.twinx()
        bars = ax.bar(configs, costs, alpha=0.7, color="steelblue", label="Cost")
        line = ax2.plot(
            configs, performance, "ro-", linewidth=2, markersize=10, label="Performance"
        )

        ax.set_ylabel("Cost ($)", color="steelblue")
        ax2.set_ylabel("Performance Score", color="red")
        ax.set_title("Cost vs Performance")
        ax.tick_params(axis="y", labelcolor="steelblue")
        ax2.tick_params(axis="y", labelcolor="red")
        ax.grid(True, alpha=0.3)

        # Add values on bars
        for i, (bar, cost) in enumerate(zip(bars, costs)):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0, height, f"${cost}", ha="center", va="bottom"
            )

        plt.tight_layout()
        plt.savefig("platform_comparison.png", dpi=150, bbox_inches="tight")
        print(f"\nComparison plot saved as 'platform_comparison.png'")
        plt.show()


if __name__ == "__main__":
    print("Starting platform comparison...")
    comparison = PlatformComparison()
    comparison.run_comparison()
