import matplotlib.pyplot as plt
import numpy as np




# Parameters
wheel_diameter_m = 0.7  # meters
wheel_radius_m = wheel_diameter_m / 2
rpm_min, rpm_max = 60, 120
speed_min, speed_max = 7, 85  # km/h
optimal_rpm = 90



# Example gear ratios
ratios_1 = [4.727272727,
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
    1.2]

ratios_2 = [5,
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
    1.136363636,
]

ratios_3 = [5,
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
    1.086956522,
]

ratios_4 = [5,
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
]


ratios_1 = ratios_1[::-1]
name_1 = "Shimano 11-30/52-36"

ratios_2 = ratios_2[::-1]
name_2 = "Ekar GT 10-44/50"

ratios_3 = ratios_3[::-1]
name_3 = "SRAM XPLR 10-46/50"

ratios_4 = ratios_4[::-1]
name_4 = "Ekar 10-44/50"




def compute_cutoffs(gear_ratios):
    gears = len(gear_ratios)
    # Optimal speed for each gear at optimal RPM
    v_opt = [optimal_rpm * (2 * np.pi * wheel_radius_m / 60) * g * 3.6 for g in gear_ratios]

    v_start = []
    v_cutoff = []

    for i in range(gears):
        # Start speed
        if i == 0:
            start = rpm_min * (2 * np.pi * wheel_radius_m / 60) * gear_ratios[i] * 3.6
        else:
            start = v_cutoff[i - 1]
        v_start.append(start)

        # Cutoff speed
        if i < gears - 1:
            cutoff = (v_opt[i] + v_opt[i + 1]) / 2
        else:
            cutoff = speed_max
        v_cutoff.append(cutoff)

    return v_start, v_cutoff, v_opt


def compute_rpm_for_speed(v, gear):
    """Compute RPM for a given speed and gear ratio"""
    return v / 3.6 * 60 / (2 * np.pi * wheel_radius_m * gear)


rpm_array = np.linspace(rpm_min, rpm_max, 300)
plt.figure(figsize=(12, 7))


def plot_gear_set(gear_ratios, label, color, fill=True):
    """Plot one set of gear lines with optional fill between start/cutoff curves."""
    v_start, v_cutoff, v_opt = compute_cutoffs(gear_ratios)

    # Plot gear lines
    for i, ratio in enumerate(gear_ratios):
        speed_kmh = rpm_array * (2 * np.pi * wheel_radius_m / 60) * ratio * 3.6
        mask = (speed_kmh >= v_start[i]) & (speed_kmh <= v_cutoff[i])
        plt.plot(speed_kmh[mask], rpm_array[mask], alpha=0.4, color=color, label=label if i == 0 else "")

    # Compute start and cutoff curves
    rpm_start = [compute_rpm_for_speed(v, g) for v, g in zip(v_start, gear_ratios)]
    rpm_cutoff = [compute_rpm_for_speed(v, g) for v, g in zip(v_cutoff, gear_ratios)]

    if fill:
        # Fix fill region by extending start and cutoff endpoints
        v_start_ext = [v_start[0]] + v_cutoff  # prepend start point
        v_cutoff_ext = v_start + [v_cutoff[-1]]  # append cutoff end
        rpm_start_ext = [rpm_start[0]] + rpm_cutoff
        rpm_cutoff_ext = rpm_start + [rpm_cutoff[-1]]

        # Build smooth interpolation grid
        speed_fine = np.linspace(v_start_ext[0], v_cutoff_ext[-1], 500)
        rpm_start_interp = np.interp(speed_fine, v_start_ext, rpm_start_ext)
        rpm_cutoff_interp = np.interp(speed_fine, v_cutoff_ext, rpm_cutoff_ext)

        plt.fill_between(speed_fine, rpm_start_interp, rpm_cutoff_interp, color=color, alpha=0.2)
    else:
        # Plot start/cutoff as lines
        plt.plot(v_start, rpm_start, color=color, alpha=1)
        plt.plot(v_cutoff, rpm_cutoff, color=color, alpha=1)


# Plot both sets
plot_gear_set(ratios_1, name_1, 'blue', fill=True)
plot_gear_set(ratios_2, name_2, 'red', fill=False)
plot_gear_set(ratios_3, name_3, 'green', fill=False)
plot_gear_set(ratios_4, name_4, 'yellow', fill=False)

plt.xlabel('Speed (km/h)')
plt.ylabel('Pedal RPM')
plt.title('Comparison of Two Gear Sets with Filled Start-to-Cutoff Ranges')
plt.minorticks_on()
plt.grid(True, which='major', linestyle='-', alpha=0.9)
plt.grid(True, which='minor', linestyle=':', alpha=0.7)
plt.legend()
plt.show()