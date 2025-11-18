import sys
import numpy as np
import matplotlib
matplotlib.use("QtAgg")

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider,
    QLabel, QCheckBox, QGroupBox, QPushButton, QGridLayout,
    QLineEdit, QDialog, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import json, os

SAVE_FILE = "gear_sets.json"

# ------------------- Gear Ratio Computation -------------------
def compute_gear_ratios(front_teeth, rear_teeth, big_index=None, small_index=None):
    ratios = []

    rear_teeth_sorted = sorted(rear_teeth)  # ensure correct order (smallest → largest)
    n_rear = len(rear_teeth_sorted)

    # Single chainring
    if len(front_teeth) == 1:
        f = front_teeth[0]
        ratios = [f / r for r in rear_teeth_sorted]

    # Double chainring
    elif len(front_teeth) >= 2:
        f_big, f_small = sorted(front_teeth, reverse=True)

        if big_index is None:
            big_index = n_rear - 1
        if small_index is None:
            small_index = 0

        # Big ring: smallest → big_index
        big_ratios = [f_big / r for r in rear_teeth_sorted[:big_index+1]]

        # Small ring: small_index → largest
        small_ratios = [f_small / r for r in rear_teeth_sorted[small_index:]]

        ratios = big_ratios + small_ratios

    return sorted(ratios)

# ------------------- Add Gear Set Dialog -------------------
class AddGearSetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Gear Set (Drivetrain)")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Gear set name")
        layout.addWidget(QLabel("Gear Set Name:"))
        layout.addWidget(self.name_input)

        # Front chainrings
        self.front_input = QLineEdit()
        self.front_input.setPlaceholderText("Front chainrings, e.g., 52,36")
        layout.addWidget(QLabel("Front chainrings:"))
        layout.addWidget(self.front_input)

        # Rear cassette
        self.rear_input = QLineEdit()
        self.rear_input.setPlaceholderText("Rear sprockets, e.g., 11,13,15,...")
        layout.addWidget(QLabel("Rear cassette:"))
        layout.addWidget(self.rear_input)

        # Preview
        self.preview_label = QLabel("Preview ratio: -")
        layout.addWidget(self.preview_label)

        # Sliders for big/small rear selection
        slider_layout = QHBoxLayout()
        self.big_slider = QSlider(Qt.Orientation.Horizontal)
        self.small_slider = QSlider(Qt.Orientation.Horizontal)
        slider_layout.addWidget(QLabel("Big ring rear:"))
        slider_layout.addWidget(self.big_slider)
        slider_layout.addWidget(QLabel("Small ring rear:"))
        slider_layout.addWidget(self.small_slider)
        layout.addLayout(slider_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Connections
        self.front_input.textChanged.connect(self.update_rear_slider_range)
        self.rear_input.textChanged.connect(self.update_rear_slider_range)
        self.big_slider.valueChanged.connect(self.update_preview)
        self.small_slider.valueChanged.connect(self.update_preview)

        self.rear_teeth_list = []

    def update_rear_slider_range(self):
        # parse rear
        try:
            self.rear_teeth_list = [int(x.strip()) for x in self.rear_input.text().split(",") if x.strip()]
            if not self.rear_teeth_list:
                return
            max_index = len(self.rear_teeth_list) - 1
            self.big_slider.setMinimum(0)
            self.big_slider.setMaximum(max_index)
            self.small_slider.setMinimum(0)
            self.small_slider.setMaximum(max_index)
            # default positions
            self.big_slider.setValue(max_index)
            self.small_slider.setValue(0)
            self.update_preview()
        except:
            self.rear_teeth_list = []

    def update_preview(self):
        try:
            fronts = [int(x.strip()) for x in self.front_input.text().split(",") if x.strip()]
            rear = self.rear_teeth_list
            if not fronts or not rear:
                self.preview_label.setText("Preview ratio: -")
                return
            big_ratio = fronts[0] / rear[self.big_slider.value()] if len(fronts) > 0 else 0
            small_ratio = fronts[1] / rear[self.small_slider.value()] if len(fronts) > 1 else None
            preview_text = f"Preview ratio - Big: {big_ratio:.2f}"
            if small_ratio:
                preview_text += f", Small: {small_ratio:.2f}"
            self.preview_label.setText(preview_text)
        except:
            self.preview_label.setText("Preview ratio: -")

    def get_data(self):
        name = self.name_input.text().strip()
        if not name or not self.rear_teeth_list:
            return None, []
        fronts = [int(x.strip()) for x in self.front_input.text().split(",") if x.strip()]
        ratios = compute_gear_ratios(
            fronts, self.rear_teeth_list,
            big_index=self.big_slider.value(),
            small_index=self.small_slider.value() if len(fronts) > 1 else None
        )
        return name, ratios

# ------------------- Main GUI -------------------
class GearingChart(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gearing Speed Chart")
        self.resize(1400, 800)

        # Parameters
        self.wheel_diameter_m = 0.7
        self.wheel_radius_m = self.wheel_diameter_m / 2
        self.rpm_min, self.rpm_max = 60, 120
        self.speed_max = 85
        self.optimal_rpm = 90

        self.gear_sets = {
            "Shimano 11-30/52-36": [
                                       4.727272727,
                                       4.333333333,
                                       4,
                                       3.714285714,
                                       3.466666667,
                                       3.058823529,
                                       2.736842105,
                                       2.476190476,
                                       2.166666667,
                                       1.894736842,
                                       1.714285714,
                                       1.5,
                                       1.333333333,
                                       1.2][::-1],

            "Ekar GT 10-44/50": [
                                    5,
                                    4.545454545,
                                    4.166666667,
                                    3.846153846,
                                    3.571428571,
                                    3.125,
                                    2.777777778,
                                    2.380952381,
                                    2.083333333,
                                    1.785714286,
                                    1.515151515,
                                    1.315789474,
                                    1.136363636
                                ][::-1],

            "SRAM XPLR 10-46/50": [
                                      5,
                                      4.545454545,
                                      4.166666667,
                                      3.846153846,
                                      3.333333333,
                                      2.941176471,
                                      2.631578947,
                                      2.380952381,
                                      2.083333333,
                                      1.785714286,
                                      1.5625,
                                      1.315789474,
                                      1.086956522
                                  ][::-1],

            "Ekar 10-44/50": [
                                 5,
                                 4.545454545,
                                 4.166666667,
                                 3.846153846,
                                 3.571428571,
                                 3.333333333,
                                 2.941176471,
                                 2.5,
                                 2.173913043,
                                 1.851851852,
                                 1.5625,
                                 1.315789474,
                                 1.136363636,
                             ][::-1]}
        self.colors = ["blue", "red", "green", "orange", "purple", "brown"]
        self.rpm_array = np.linspace(self.rpm_min, self.rpm_max, 300)

        # Layout
        layout = QHBoxLayout(self)

        # Plot
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas, stretch=4)

        # Slider
        rpm_layout = QVBoxLayout()
        self.slider_label = QLabel(f"Optimal RPM: {self.optimal_rpm}")
        self.slider_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setRange(60, 120)
        self.slider.setValue(self.optimal_rpm)
        self.slider.setTickInterval(5)
        self.slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.slider.valueChanged.connect(self.on_slider_change)
        rpm_layout.addWidget(self.slider_label)
        rpm_layout.addWidget(self.slider, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addLayout(rpm_layout, stretch=0)

        # Right panel
        self.control_panel = QVBoxLayout()
        self.checkboxes = {}
        self.build_gear_controls()
        layout.addLayout(self.control_panel, stretch=1)
        self.load_gear_sets()

        self.update_plot()

    # ------------------- Core Computation -------------------
    def compute_cutoffs(self, gear_ratios):
        gears = len(gear_ratios)
        v_opt = [self.optimal_rpm * (2 * np.pi * self.wheel_radius_m / 60) * g * 3.6 for g in gear_ratios]
        v_start, v_cutoff = [], []

        for i in range(gears):
            if i == 0:
                start = self.rpm_min * (2 * np.pi * self.wheel_radius_m / 60) * gear_ratios[i] * 3.6
            else:
                start = v_cutoff[i - 1]
            v_start.append(start)

            if i < gears - 1:
                cutoff = (v_opt[i] + v_opt[i + 1]) / 2
            else:
                cutoff = self.speed_max
            v_cutoff.append(cutoff)
        return v_start, v_cutoff, v_opt

    def compute_rpm_for_speed(self, v, gear):
        return v / 3.6 * 60 / (2 * np.pi * self.wheel_radius_m * gear)

    # ------------------- UI Controls -------------------
    def build_gear_controls(self):
        while self.control_panel.count():
            item = self.control_panel.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.checkboxes.clear()
        color_cycle = iter(self.colors)
        for name in self.gear_sets.keys():
            color = next(color_cycle, "gray")
            group = QGroupBox(name)
            grid = QGridLayout()

            chk_show = QCheckBox("Show")
            chk_show.setChecked(True)
            chk_fill = QCheckBox("Fill")
            chk_fill.setChecked(True)

            self.checkboxes[name] = {"show": chk_show, "fill": chk_fill, "color": color}
            chk_show.stateChanged.connect(self.update_plot)
            chk_fill.stateChanged.connect(self.update_plot)

            lbl_color = QLabel()
            lbl_color.setStyleSheet(f"background-color: {color}; min-width: 20px; min-height: 20px; border: 1px solid gray;")
            grid.addWidget(lbl_color, 0, 0)
            grid.addWidget(chk_show, 0, 1)
            grid.addWidget(chk_fill, 0, 2)

            btn_delete = QPushButton("🗑️ Delete")
            btn_delete.clicked.connect(lambda _, n=name: self.delete_gear_set(n))
            grid.addWidget(btn_delete, 0, 3)

            group.setLayout(grid)
            self.control_panel.addWidget(group)

        # Add gear set button
        self.add_button = QPushButton("➕ Add Gear Set")
        self.add_button.clicked.connect(self.add_gear_set_dialog)

        btn_save = QPushButton("💾 Save Gear Sets")
        btn_save.clicked.connect(self.save_gear_sets)
        self.control_panel.addWidget(btn_save)

        btn_load = QPushButton("📂 Load Gear Sets")
        btn_load.clicked.connect(self.load_gear_sets)
        self.control_panel.addWidget(btn_load)

        self.control_panel.addWidget(self.add_button)
        self.control_panel.addStretch()

    def add_gear_set_dialog(self):
        dialog = AddGearSetDialog(self)
        dialog.exec()
        name, ratios = dialog.get_data()
        if not ratios:
            return
        if name in self.gear_sets:
            QMessageBox.warning(self, "Duplicate Name", f"A gear set named '{name}' already exists.")
            return
        self.gear_sets[name] = ratios
        self.build_gear_controls()
        self.update_plot()
        self.save_gear_sets()

    def delete_gear_set(self, name):
        if name in self.gear_sets:
            del self.gear_sets[name]
        if name in self.checkboxes:
            del self.checkboxes[name]
        self.build_gear_controls()
        self.update_plot()
        self.save_gear_sets()

    # ------------------- Plot -------------------
    def update_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_xlabel("Speed (km/h)")
        ax.set_ylabel("Pedal RPM")
        ax.set_title("Gearing Speed Chart")
        ax.grid(True, which="major", linestyle="-", alpha=0.7)
        ax.grid(True, which="minor", linestyle=":", alpha=0.4)
        ax.minorticks_on()

        for name, ratios in self.gear_sets.items():
            if name not in self.checkboxes:
                continue
            show = self.checkboxes[name]["show"].isChecked()
            fill_enabled = self.checkboxes[name]["fill"].isChecked()
            color = self.checkboxes[name]["color"]
            if not show:
                continue

            v_start, v_cutoff, _ = self.compute_cutoffs(ratios)
            for i, ratio in enumerate(ratios):
                speed_kmh = self.rpm_array * (2 * np.pi * self.wheel_radius_m / 60) * ratio * 3.6
                mask = (speed_kmh >= v_start[i]) & (speed_kmh <= v_cutoff[i])
                ax.plot(speed_kmh[mask], self.rpm_array[mask], color=color, label=name if i == 0 else "")

            rpm_start = [self.compute_rpm_for_speed(v, g) for v, g in zip(v_start, ratios)]
            rpm_cutoff = [self.compute_rpm_for_speed(v, g) for v, g in zip(v_cutoff, ratios)]

            if fill_enabled:
                v_start_ext = [v_start[0]] + v_cutoff
                v_cutoff_ext = v_start + [v_cutoff[-1]]
                rpm_start_ext = [rpm_start[0]] + rpm_cutoff
                rpm_cutoff_ext = rpm_start + [rpm_cutoff[-1]]
                speed_fine = np.linspace(v_start_ext[0], v_cutoff_ext[-1], 500)
                rpm_start_interp = np.interp(speed_fine, v_start_ext, rpm_start_ext)
                rpm_cutoff_interp = np.interp(speed_fine, v_cutoff_ext, rpm_cutoff_ext)
                ax.fill_between(speed_fine, rpm_start_interp, rpm_cutoff_interp, color=color, alpha=0.2)
            else:
                ax.plot(v_start, rpm_start, color=color, linestyle="--", alpha=0.5)
                ax.plot(v_cutoff, rpm_cutoff, color=color, linestyle="-.", alpha=0.5)

        ax.axhline(self.optimal_rpm, color="gray", linestyle="--", alpha=0.6, label="Optimal RPM")
        ax.legend()
        self.canvas.draw_idle()

    # ------------------- Slider -------------------
    def on_slider_change(self, value):
        self.optimal_rpm = value
        self.slider_label.setText(f"Optimal RPM: {value}")
        self.update_plot()

    def save_gear_sets(self):
        data = []
        for name, ratios in self.gear_sets.items():
            info = self.checkboxes[name]
            data.append({
                "name": name,
                "ratios": ratios,
                "show": info["show"].isChecked(),
                "fill": info["fill"].isChecked(),
                "color": info["color"]
            })

        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ Saved {len(data)} gear sets to {SAVE_FILE}")

    def load_gear_sets(self):
        if not os.path.exists(SAVE_FILE):
            return
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)

        for d in data:
            self.gear_sets[d["name"]] = d["ratios"]
        self.build_gear_controls()
        self.update_plot()
        print(f"📂 Loaded {len(data)} gear sets from {SAVE_FILE}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GearingChart()
    window.show()
    sys.exit(app.exec())
