"""
Platform Leveling System - GUI Version
Easy-to-use interface with buttons - no keyboard commands needed!
"""

import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from imu_streamer_http import IMUData, IMUHTTPStreamer
from inverse_kinematics import PlatformConfig, StewartPlatformIK, TripodIK


class PlatformLevelingGUI:
    """
    GUI application for platform leveling visualization
    """

    def __init__(self):
        # Create main window
        self.root = tk.Tk()
        self.root.title("Platform Leveling System")
        self.root.geometry("1400x800")

        # Platform configuration
        self.config = PlatformConfig(
            length=1.83, width=1.22, min_height=0.3, max_height=0.7, actuator_stroke=0.4
        )

        # Initialize IK solvers
        self.tripod_solver = TripodIK(self.config)
        self.stewart_3dof_solver = StewartPlatformIK(self.config, dof_mode="3DOF")
        self.stewart_6dof_solver = StewartPlatformIK(self.config, dof_mode="6DOF")

        # Current configuration
        self.platform_type = "tripod"
        self.ik_solver = self.tripod_solver

        # IMU streamer
        self.imu_streamer = IMUHTTPStreamer()
        self.imu_streamer.start()

        # State
        self.leveling_enabled = False
        self.running = True
        self.view_elevation = 25
        self.view_azimuth = 45

        # Setup UI
        self._setup_ui()

        # Start update loop
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui(self):
        """Setup the user interface"""

        # Create main containers
        left_frame = ttk.Frame(self.root, padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        right_frame = ttk.Frame(self.root, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=2)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # --- LEFT SIDE: 3D Visualization ---
        viz_frame = ttk.LabelFrame(left_frame, text="3D Platform View", padding="10")
        viz_frame.pack(fill=tk.BOTH, expand=True)

        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax_3d = self.fig.add_subplot(111, projection="3d")

        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # View control buttons
        view_frame = ttk.Frame(viz_frame)
        view_frame.pack(pady=5)

        ttk.Label(view_frame, text="View:").pack(side=tk.LEFT, padx=5)
        ttk.Button(view_frame, text="↑", width=3, command=lambda: self._rotate_view("up")).pack(
            side=tk.LEFT
        )
        ttk.Button(view_frame, text="↓", width=3, command=lambda: self._rotate_view("down")).pack(
            side=tk.LEFT
        )
        ttk.Button(view_frame, text="←", width=3, command=lambda: self._rotate_view("left")).pack(
            side=tk.LEFT
        )
        ttk.Button(view_frame, text="→", width=3, command=lambda: self._rotate_view("right")).pack(
            side=tk.LEFT
        )
        ttk.Button(view_frame, text="Reset", command=self._reset_view).pack(side=tk.LEFT, padx=5)

        # --- RIGHT SIDE: Controls and Info ---

        # Connection Status
        status_frame = ttk.LabelFrame(right_frame, text="Connection Status", padding="10")
        status_frame.pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(
            status_frame, text="⚪ Waiting for iPhone...", font=("Arial", 10)
        )
        self.status_label.pack()

        # Get computer IP
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            computer_ip = s.getsockname()[0]
        except:
            computer_ip = "Unknown"
        finally:
            s.close()

        ttk.Label(
            status_frame, text=f"URL: http://{computer_ip}:8080/imu", font=("Courier", 9)
        ).pack()

        # IMU Data Display
        imu_frame = ttk.LabelFrame(right_frame, text="IMU Data", padding="10")
        imu_frame.pack(fill=tk.X, pady=5)

        self.roll_label = ttk.Label(imu_frame, text="Roll:  0.00°", font=("Courier", 10))
        self.roll_label.pack(anchor=tk.W)

        self.pitch_label = ttk.Label(imu_frame, text="Pitch: 0.00°", font=("Courier", 10))
        self.pitch_label.pack(anchor=tk.W)

        self.yaw_label = ttk.Label(imu_frame, text="Yaw:   0.00°", font=("Courier", 10))
        self.yaw_label.pack(anchor=tk.W)

        self.tilt_label = ttk.Label(imu_frame, text="Tilt:  0.00°", font=("Courier", 10))
        self.tilt_label.pack(anchor=tk.W)

        # Platform Configuration
        config_frame = ttk.LabelFrame(right_frame, text="Platform Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=5)

        self.config_var = tk.StringVar(value="tripod")

        ttk.Radiobutton(
            config_frame,
            text="Tripod (3 actuators, no yaw)",
            variable=self.config_var,
            value="tripod",
            command=self._change_platform_type,
        ).pack(anchor=tk.W)

        ttk.Radiobutton(
            config_frame,
            text="Stewart 3-DOF (6 actuators)",
            variable=self.config_var,
            value="stewart_3dof",
            command=self._change_platform_type,
        ).pack(anchor=tk.W)

        ttk.Radiobutton(
            config_frame,
            text="Stewart 6-DOF (6 actuators + yaw)",
            variable=self.config_var,
            value="stewart_6dof",
            command=self._change_platform_type,
        ).pack(anchor=tk.W)

        # Leveling Controls
        control_frame = ttk.LabelFrame(right_frame, text="Leveling Control", padding="10")
        control_frame.pack(fill=tk.X, pady=5)

        self.leveling_button = ttk.Button(
            control_frame, text="⚫ Enable Leveling", command=self._toggle_leveling
        )
        self.leveling_button.pack(fill=tk.X, pady=5)

        ttk.Button(control_frame, text="Calibrate IMU", command=self._calibrate_imu).pack(
            fill=tk.X, pady=5
        )

        # Actuator Status
        actuator_frame = ttk.LabelFrame(right_frame, text="Actuator Lengths", padding="10")
        actuator_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.actuator_labels = []
        for i in range(6):  # Max 6 for Stewart
            label = ttk.Label(actuator_frame, text=f"[{i+1}] ---.-mm", font=("Courier", 9))
            label.pack(anchor=tk.W)
            self.actuator_labels.append(label)

        # Instructions
        info_frame = ttk.LabelFrame(right_frame, text="Setup Instructions", padding="10")
        info_frame.pack(fill=tk.X, pady=5)

        instructions = """
1. Open Sensor Logger on iPhone
2. Settings → Push → HTTP Push
3. Enter URL shown above
4. Format: JSON, Method: POST
5. Start recording
6. Click 'Enable Leveling'
        """
        ttk.Label(info_frame, text=instructions, justify=tk.LEFT, font=("Arial", 9)).pack()

    def _rotate_view(self, direction):
        """Rotate the 3D view"""
        if direction == "up":
            self.view_elevation += 5
        elif direction == "down":
            self.view_elevation -= 5
        elif direction == "left":
            self.view_azimuth -= 10
        elif direction == "right":
            self.view_azimuth += 10

    def _reset_view(self):
        """Reset view to default"""
        self.view_elevation = 25
        self.view_azimuth = 45

    def _toggle_leveling(self):
        """Toggle leveling on/off"""
        self.leveling_enabled = not self.leveling_enabled
        if self.leveling_enabled:
            self.leveling_button.config(text="🟢 Leveling ENABLED")
        else:
            self.leveling_button.config(text="⚫ Enable Leveling")

    def _calibrate_imu(self):
        """Calibrate IMU"""
        self.imu_streamer.calibrate()
        messagebox.showinfo("Calibration", "IMU calibrated!\nCurrent position set as zero.")

    def _change_platform_type(self):
        """Change platform configuration"""
        new_type = self.config_var.get()
        self.platform_type = new_type

        if new_type == "tripod":
            self.ik_solver = self.tripod_solver
        elif new_type == "stewart_3dof":
            self.ik_solver = self.stewart_3dof_solver
        else:  # stewart_6dof
            self.ik_solver = self.stewart_6dof_solver

    def _draw_platform(self, roll, pitch, yaw, actuator_lengths):
        """Draw the 3D platform"""
        self.ax_3d.clear()

        # Set labels and limits
        self.ax_3d.set_xlabel("X (m)")
        self.ax_3d.set_ylabel("Y (m)")
        self.ax_3d.set_zlabel("Z (m)")
        self.ax_3d.set_title(f"{self.platform_type.upper()} Platform")

        max_dim = max(self.config.length, self.config.width) / 2 * 1.5
        self.ax_3d.set_xlim([-max_dim, max_dim])
        self.ax_3d.set_ylim([-max_dim, max_dim])
        self.ax_3d.set_zlim([0, self.config.max_height * 1.5])

        # Get rotation matrix
        R = self.ik_solver.rotation_matrix(roll, pitch, yaw)

        if self.leveling_enabled:
            R = self.ik_solver.rotation_matrix(
                -roll, -pitch, -yaw if self.platform_type == "stewart_6dof" else 0
            )

        # Get actuator points
        base_points, platform_points_init = self.ik_solver.get_actuator_positions()
        center = np.array([0, 0, self.config.min_height])

        # Rotate platform points
        platform_points = []
        for point in platform_points_init:
            local_point = point - center
            rotated_point = R @ local_point + center
            platform_points.append(rotated_point)
        platform_points = np.array(platform_points)

        # Draw base
        base_corners = np.array(
            [
                [-self.config.length / 2, -self.config.width / 2, 0],
                [self.config.length / 2, -self.config.width / 2, 0],
                [self.config.length / 2, self.config.width / 2, 0],
                [-self.config.length / 2, self.config.width / 2, 0],
            ]
        )

        base_poly = Poly3DCollection([base_corners], alpha=0.2, facecolor="gray", edgecolor="black")
        self.ax_3d.add_collection3d(base_poly)

        # Draw platform
        platform_corners = []
        for corner in base_corners:
            corner_local = corner - np.array([0, 0, self.config.min_height])
            corner_rotated = R @ corner_local + center
            platform_corners.append(corner_rotated)
        platform_corners = np.array(platform_corners)

        platform_poly = Poly3DCollection(
            [platform_corners], alpha=0.5, facecolor="lightblue", edgecolor="blue", linewidth=2
        )
        self.ax_3d.add_collection3d(platform_poly)

        # Draw actuators
        for i, (base_pt, plat_pt) in enumerate(zip(base_points, platform_points)):
            self.ax_3d.plot(
                [base_pt[0], plat_pt[0]],
                [base_pt[1], plat_pt[1]],
                [base_pt[2], plat_pt[2]],
                "r-",
                linewidth=3,
                alpha=0.7,
            )

            self.ax_3d.scatter(*base_pt, color="darkred", s=100, marker="o")
            self.ax_3d.scatter(*plat_pt, color="blue", s=100, marker="o")

        # Set view angle
        self.ax_3d.view_init(elev=self.view_elevation, azim=self.view_azimuth)

        self.canvas.draw()

    def _update_loop(self):
        """Main update loop"""
        while self.running:
            imu_data = self.imu_streamer.get_latest()

            if imu_data:
                # Update status
                self.status_label.config(text="🟢 Connected to iPhone")

                # Update IMU display
                self.roll_label.config(text=f"Roll:  {imu_data.roll:6.2f}°")
                self.pitch_label.config(text=f"Pitch: {imu_data.pitch:6.2f}°")

                if self.platform_type == "stewart_6dof":
                    self.yaw_label.config(text=f"Yaw:   {imu_data.yaw:6.2f}°")
                else:
                    self.yaw_label.config(text=f"Yaw:   {imu_data.yaw:6.2f}° (ignored)")

                tilt_mag = np.sqrt(imu_data.roll**2 + imu_data.pitch**2)
                self.tilt_label.config(text=f"Tilt:  {tilt_mag:6.2f}°")

                # Calculate actuator positions
                roll_rad = np.deg2rad(imu_data.roll)
                pitch_rad = np.deg2rad(imu_data.pitch)
                yaw_rad = np.deg2rad(imu_data.yaw)

                if self.leveling_enabled:
                    if self.platform_type == "tripod":
                        lengths, valid = self.ik_solver.level_platform(roll_rad, pitch_rad)
                    elif self.platform_type == "stewart_3dof":
                        lengths, valid = self.ik_solver.level_platform(roll_rad, pitch_rad, 0)
                    else:
                        lengths, valid = self.ik_solver.level_platform(roll_rad, pitch_rad, yaw_rad)

                    display_roll = 0
                    display_pitch = 0
                    display_yaw = 0
                else:
                    if self.platform_type == "tripod":
                        lengths, valid = self.ik_solver.solve(roll_rad, pitch_rad, 0)
                        display_roll, display_pitch, display_yaw = roll_rad, pitch_rad, 0
                    elif self.platform_type == "stewart_3dof":
                        lengths, valid = self.ik_solver.solve(roll_rad, pitch_rad, 0)
                        display_roll, display_pitch, display_yaw = roll_rad, pitch_rad, 0
                    else:
                        lengths, valid = self.ik_solver.solve(roll_rad, pitch_rad, yaw_rad)
                        display_roll, display_pitch, display_yaw = roll_rad, pitch_rad, yaw_rad

                # Update actuator display
                num_actuators = len(lengths)
                for i in range(6):
                    if i < num_actuators:
                        length_mm = lengths[i] * 1000
                        self.actuator_labels[i].config(text=f"[{i+1}] {length_mm:6.1f} mm ✓")
                    else:
                        self.actuator_labels[i].config(text=f"[{i+1}] ---.- mm")

                # Draw platform
                self._draw_platform(display_roll, display_pitch, display_yaw, lengths)

            time.sleep(0.05)  # 20 FPS

    def _on_closing(self):
        """Handle window close"""
        self.running = False
        self.imu_streamer.stop()
        self.root.destroy()

    def run(self):
        """Start the GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    app = PlatformLevelingGUI()
    app.run()
