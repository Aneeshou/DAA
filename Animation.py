"""Balanced, beginner-friendly Master's Theorem animation.

Run interactively:
    python master_theorem_animation_balanced.py

Export a GIF:
    python master_theorem_animation_balanced.py --save-gif master_theorem_animation_balanced.gif

The program uses three fixed, classroom-friendly examples and only four controls.
"""

from __future__ import annotations
import argparse
import math
from pathlib import Path

parser = argparse.ArgumentParser(description="Balanced Master's Theorem animation")
parser.add_argument("--save-gif", nargs="?", const="master_theorem_animation_balanced.gif",
                    default=None, help="Export a GIF instead of opening the interactive window.")
parser.add_argument("--fps", type=float, default=1.3, help="GIF playback speed.")
parser.add_argument("--dpi", type=int, default=80, help="GIF resolution.")
ARGS = parser.parse_args()

if ARGS.save_gif:
    import matplotlib
    matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch
from matplotlib.widgets import Button

NAVY = "#1F3864"
BLUE = "#4472C4"
TEAL = "#2A9D8F"
ORANGE = "#E9A23B"
PALE_BLUE = "#D9EAF7"
PALE_GREY = "#EEF1F5"
GREY = "#667085"
DARK = "#202938"
WHITE = "#FFFFFF"
RED = "#C84C4C"

EXAMPLES = [
    {
        "name": "Case 1 — Recursive work dominates",
        "short": "Strassen's algorithm",
        "a": 7, "b": 2, "d": 2, "h": 4,
        "recurrence": r"$T(n)=7T(n/2)+n^2$",
        "result": r"$\Theta(n^{\log_2 7})$",
        "colour": BLUE,
        "takeaway": "Work per level grows toward the leaves, so recursive work dominates.",
        "comparison": r"$d=2 < p=\log_2 7\approx2.807$",
    },
    {
        "name": "Case 2 — Equal work at every level",
        "short": "Merge Sort",
        "a": 2, "b": 2, "d": 1, "h": 5,
        "recurrence": r"$T(n)=2T(n/2)+n$",
        "result": r"$\Theta(n\log n)$",
        "colour": TEAL,
        "takeaway": "Every level contributes about the same total work.",
        "comparison": r"$d=1 = p=\log_2 2=1$",
    },
    {
        "name": "Case 3 — Outside work dominates",
        "short": "Quadratic combine work",
        "a": 2, "b": 2, "d": 2, "h": 5,
        "recurrence": r"$T(n)=2T(n/2)+n^2$",
        "result": r"$\Theta(n^2)$",
        "colour": ORANGE,
        "takeaway": "The top level contributes the most; lower-level work shrinks.",
        "comparison": r"$d=2 > p=\log_2 2=1$",
        "regularity": "Regularity holds: 2(n/2)² = n²/2.",
    },
]


def case_data(example):
    a, b, d, h = example["a"], example["b"], example["d"], example["h"]
    n = b ** h
    p = math.log(a, b)
    work = [a ** i * (n / (b ** i)) ** d for i in range(h + 1)]
    return n, p, work


def draw_dashboard(fig, axes, example, visible_levels):
    ax_tree, ax_bars, ax_info = axes
    for ax in axes:
        ax.clear()

    a, b, d, h = example["a"], example["b"], example["d"], example["h"]
    n, p, work = case_data(example)
    shown = max(1, min(visible_levels, h + 1))
    colour = example["colour"]

    # Left: a schematic recursion tree. Node counts are exact; only a small
    # sample of circles is drawn so the diagram remains readable.
    ax_tree.set_title("1. Recursion tree", loc="left", color=NAVY,
                      fontsize=12, fontweight="bold", pad=8)
    ax_tree.set_xlim(-1.28, 1.32)
    ax_tree.set_ylim(-0.55, h + 0.65)
    ax_tree.axis("off")
    sample_limit = 7
    prior_xs = None
    prior_y = None

    for level in range(shown):
        y = h - level
        count = a ** level
        samples = min(count, sample_limit)
        xs = np.linspace(-0.80, 0.80, samples) if samples > 1 else np.array([0.0])

        if prior_xs is not None:
            for j, x0 in enumerate(prior_xs):
                if len(prior_xs) == 1:
                    targets = range(min(len(xs), min(a, 3)))
                else:
                    center = int(round(j * (len(xs) - 1) / max(1, len(prior_xs) - 1)))
                    lo = max(0, center - 1)
                    hi = min(len(xs), center + 2)
                    targets = range(lo, hi)
                for k in targets:
                    ax_tree.plot([x0, xs[k]], [prior_y - 0.08, y + 0.08],
                                 color="#C9D2DF", linewidth=0.9, zorder=1)

        ax_tree.scatter(xs, np.full(samples, y), s=145 if samples <= 4 else 105,
                        facecolor=PALE_BLUE if level < shown - 1 else colour,
                        edgecolor=colour, linewidth=1.2, zorder=3)
        ax_tree.text(-1.02, y, f"L{level}", ha="right", va="center",
                     fontsize=8.5, color=NAVY)
        subproblem = "n" if level == 0 else (rf"$n/{b}^{level}$")
        ax_tree.text(0, y + 0.15, subproblem, ha="center", va="bottom",
                     fontsize=8.5, color=DARK)
        count_text = f"{count:,} node" + ("" if count == 1 else "s")
        if count > samples:
            count_text += "  …"
        ax_tree.text(0, y - 0.15, count_text, ha="center", va="top",
                     fontsize=7.8, color=GREY)
        prior_xs, prior_y = xs, y

    if shown < h + 1:
        ax_tree.text(0, h - shown + 0.25, "⋮", ha="center", va="center",
                     fontsize=19, color=GREY)
        ax_tree.text(0, -0.38, f"Showing {shown} of {h+1} levels",
                     ha="center", va="center", fontsize=8.5, color=GREY)
    else:
        ax_tree.text(0, -0.38, f"Input size n = {n}",
                     ha="center", va="center", fontsize=8.5, color=GREY)

    # Right: total work done by each level. Upcoming levels are faded;
    # each newly revealed level is highlighted.
    ax_bars.set_title("2. Work at each level", loc="left", color=NAVY,
                      fontsize=12, fontweight="bold", pad=8)
    x = np.arange(h + 1)
    colors = []
    for i in range(h + 1):
        if i >= shown:
            colors.append(PALE_GREY)
        elif i == shown - 1:
            colors.append(colour)
        else:
            colors.append("#8FA5C8" if colour == BLUE else
                          "#8BCBC2" if colour == TEAL else "#F2C577")
    bars = ax_bars.bar(x, work, color=colors, edgecolor=WHITE, linewidth=0.8, width=0.68)
    ax_bars.set_xticks(x, [f"L{i}" for i in x])
    ax_bars.set_xlabel("Recursion level", fontsize=9)
    ax_bars.set_ylabel("Work (relative units)", fontsize=9)
    ax_bars.tick_params(axis="both", labelsize=8)
    ax_bars.grid(axis="y", color="#E6EAF0", linewidth=0.7)
    ax_bars.set_axisbelow(True)
    ymax = max(work) * 1.28 if max(work) > 0 else 1
    ax_bars.set_ylim(0, ymax)
    for i, (bar, value) in enumerate(zip(bars, work)):
        if i < shown:
            label = f"{value:,.0f}" if value >= 10 else f"{value:.1f}".rstrip("0").rstrip(".")
            ax_bars.text(bar.get_x() + bar.get_width()/2, bar.get_height() + ymax*0.025,
                         label, ha="center", va="bottom", fontsize=7.5, color=DARK)
    trend = ("Work rises toward leaves" if a / (b ** d) > 1 + 1e-8 else
             "Work is equal at every level" if math.isclose(a, b ** d) else
             "Work shrinks toward leaves")
    ax_bars.text(0.5, 0.96, trend, transform=ax_bars.transAxes, ha="center",
                 va="top", fontsize=9, color=colour, fontweight="bold")

    # Bottom: only the key comparison and answer, without extra parameters.
    ax_info.axis("off")
    ax_info.set_title("3. Apply the Master Theorem", loc="left", color=NAVY,
                      fontsize=12, fontweight="bold", pad=5)
    # Subtle panel with an easy left-to-right reading order.
    box = FancyBboxPatch((0.005, 0.05), 0.99, 0.80,
                         boxstyle="round,pad=0.012,rounding_size=0.018",
                         transform=ax_info.transAxes, facecolor="#F7F9FC",
                         edgecolor="#D8DEE8", linewidth=1.0)
    ax_info.add_patch(box)
    ax_info.text(0.03, 0.73, "Recurrence", transform=ax_info.transAxes,
                 fontsize=9, color=GREY, fontweight="bold")
    ax_info.text(0.03, 0.57, example["recurrence"], transform=ax_info.transAxes,
                 fontsize=15, color=NAVY)
    ax_info.text(0.32, 0.73, "Critical exponent", transform=ax_info.transAxes,
                 fontsize=9, color=GREY, fontweight="bold")
    ax_info.text(0.32, 0.57, rf"$p=\log_{{{b}}}{a}\approx {p:.3f}$",
                 transform=ax_info.transAxes, fontsize=14, color=NAVY)
    ax_info.text(0.58, 0.73, "Compare exponents", transform=ax_info.transAxes,
                 fontsize=9, color=GREY, fontweight="bold")
    ax_info.text(0.58, 0.57, example["comparison"], transform=ax_info.transAxes,
                 fontsize=12, color=NAVY)

    ax_info.text(0.03, 0.31, example["name"].upper(), transform=ax_info.transAxes,
                 fontsize=10, color=colour, fontweight="bold")
    ax_info.text(0.03, 0.15, "Answer: " + example["result"],
                 transform=ax_info.transAxes, fontsize=15, color=NAVY,
                 fontweight="bold")
    ax_info.text(0.53, 0.28, example["takeaway"], transform=ax_info.transAxes,
                 fontsize=9.3, color=DARK, va="center", wrap=True)
    if "regularity" in example:
        ax_info.text(0.53, 0.12, example["regularity"], transform=ax_info.transAxes,
                     fontsize=8.5, color=RED, va="center")

    fig.suptitle(f"MASTER'S THEOREM EXPLORER  •  {example['short']}  •  Step {shown}/{h+1}",
                 fontsize=15, color=NAVY, fontweight="bold", y=0.975)


def make_axes(fig):
    grid = fig.add_gridspec(2, 2, left=0.065, right=0.97, top=0.89, bottom=0.19,
                            wspace=0.27, hspace=0.35, height_ratios=[1.65, 1.0])
    ax_tree = fig.add_subplot(grid[0, 0])
    ax_bars = fig.add_subplot(grid[0, 1])
    ax_info = fig.add_subplot(grid[1, :])
    return [ax_tree, ax_bars, ax_info]


class Explorer:
    def __init__(self):
        self.example_index = 0
        self.visible_levels = 1
        self.playing = False
        self.fig = plt.figure(figsize=(13, 8.2), facecolor=WHITE)
        self.axes = make_axes(self.fig)

        # Four simple controls: move between levels, play/pause, switch example.
        button_specs = [
            (0.10, 0.065, 0.16, 0.065, "◀ Previous level", self.previous),
            (0.30, 0.065, 0.15, 0.065, "▶ Play / Pause", self.toggle_play),
            (0.49, 0.065, 0.16, 0.065, "Next level ▶", self.next_level),
            (0.70, 0.065, 0.20, 0.065, "Next example", self.next_example),
        ]
        self.buttons = []
        for x0, y0, width, height, label, callback in button_specs:
            button_ax = self.fig.add_axes([x0, y0, width, height])
            button = Button(button_ax, label, color="#F3F5F8", hovercolor=PALE_BLUE)
            button.label.set_color(NAVY)
            button.label.set_fontsize(9)
            button.on_clicked(callback)
            self.buttons.append(button)

        self.play_button = self.buttons[1]
        self.timer = self.fig.canvas.new_timer(interval=1000)
        self.timer.add_callback(self._tick)
        self._draw()

    @property
    def example(self):
        return EXAMPLES[self.example_index]

    def _draw(self):
        draw_dashboard(self.fig, self.axes, self.example, self.visible_levels)
        self.fig.canvas.draw_idle()

    def previous(self, _event=None):
        self.visible_levels = max(1, self.visible_levels - 1)
        self._draw()

    def next_level(self, _event=None):
        self.visible_levels = min(self.example["h"] + 1, self.visible_levels + 1)
        self._draw()

    def next_example(self, _event=None):
        self.example_index = (self.example_index + 1) % len(EXAMPLES)
        self.visible_levels = 1
        self._draw()

    def toggle_play(self, _event=None):
        self.playing = not self.playing
        if self.playing:
            self.play_button.label.set_text("Ⅱ Pause")
            self.timer.start()
        else:
            self.play_button.label.set_text("▶ Play / Pause")
            self.timer.stop()
        self.fig.canvas.draw_idle()

    def _tick(self):
        if self.playing:
            if self.visible_levels >= self.example["h"] + 1:
                self.visible_levels = 1
            else:
                self.visible_levels += 1
            self._draw()

    def show(self):
        plt.show()


def save_gif(path: str, fps: float, dpi: int):
    from PIL import Image
    frames = []
    # Show each case one level at a time, then hold on its final conclusion.
    for index, example in enumerate(EXAMPLES):
        for visible in range(1, example["h"] + 2):
            fig = plt.figure(figsize=(12, 7.6), dpi=dpi, facecolor=WHITE)
            axes = make_axes(fig)
            draw_dashboard(fig, axes, example, visible)
            fig.canvas.draw()
            rgba = np.asarray(fig.canvas.buffer_rgba())
            frame = Image.fromarray(rgba[:, :, :3].copy()).convert("P", palette=Image.Palette.ADAPTIVE)
            frames.append(frame)
            plt.close(fig)
        frames.extend([frames[-1].copy()] * max(1, int(fps * 1.5)))

    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    duration = max(150, round(1000 / max(0.2, fps)))
    frames[0].save(destination, save_all=True, append_images=frames[1:],
                   duration=duration, loop=0, optimize=True)
    print(f"Saved {destination} ({len(frames)} frames, {frames[0].size[0]}×{frames[0].size[1]})")


def main():
    if ARGS.save_gif:
        save_gif(ARGS.save_gif, ARGS.fps, ARGS.dpi)
    else:
        Explorer().show()


if __name__ == "__main__":
    main()
