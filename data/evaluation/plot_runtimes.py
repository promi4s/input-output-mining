import matplotlib.pyplot as plt
import numpy as np

# Example runtimes (in seconds) for 5 runs, each with 3 spans
runs = ["Hinge production", "Container logistics", "Procure-to-pay", "Order management"]
spans = ["Reading and filtering log", "Calculating role functions", "Input-output-miner"]

data_everything = np.array([
    # Hinge production
    [1.338, 45.207, 0.497],

    # Container logistics
    [0.796, 5.713, 0.348],

    # Procure-to-pay
    [0.753, 2.089, 0.198],

    # Order management
    [0.864, 13.134, 1.246],
])


data_optimal = np.array([
    # Hinge production
    [1.329, 6.557, 0.518, 0.261],

    # Container logistics
    [0.863, 4.127, 0, 0.232],

    # Procure-to-pay
    [0.774, 2.06, 0, 0.132],

    # Order management
    [0.861, 3.128, 0, 0.24],
])

data = data_everything
print(data)

fig, ax = plt.subplots(figsize=(8, 5))
colors = ["#ff7f0e",    "#1f77b4", "#d62728"]  # blue, orange, green, red

# Stacked bar chart
bottom = np.zeros(len(runs))
for i, span in enumerate(spans):
    ax.bar(runs, data[:, i], width=0.6, label=span, bottom=bottom, color=colors[i])
    bottom += data[:, i]

# Add total runtime labels on top of bars
for i, total in enumerate(bottom):
    ax.text(i, total + 0.01, f"{total:.3f}", ha='center', va='bottom')

ax.set_xlabel("OCEL")
ax.set_ylabel("Runtime in seconds")
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles[::-1], labels[::-1])

# Remove top and right spines (box lines)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.show()
