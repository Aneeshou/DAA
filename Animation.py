
from __future__ import annotations

import argparse
import math
from pathlib import Path

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Master's Theorem animation")
    parser.add_argument(
        "--save-gif",
        nargs="?",
        const="master_theorem_animation.gif",
        default=None,
        help="export an animated GIF (optional output path; default: master_theorem_animation.gif)",
    )
    parser.add_argument("--fps", type=float, default=1.4, help="GIF playback speed (default: 1.4 fps)")
    parser.add_argument("--dpi", type=int, default=105, help="GIF resolution (default: 105 dpi)")
    return parser.parse_args()


ARGS = _parse_args()
if ARGS.save_gif:
    import matplotlib
    matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
from matplotlib.widgets import Button, Slider

# A restrained palette, matching the navy/blue styling used in the written report.
NAVY = "#1F3864"
BLUE = "#4472C4"
LIGHT_BLUE = "#D9EAF7"
TEAL = "#2A9D8F"
ORANGE = "#E9A23B"
RED = "#C84C4C"
GREY = "#667085"
LIGHT_GREY = "#E6EAF0"
DARK = "#202938"
WHITE = "#FFFFFF"


def classify(a: int, b: int, d: float) -> tuple[int, float, str, str]:
    """Return case number, p=log_b(a), result expression, and short reasoning."""
    p = math.log(a, b)
    tolerance = 1e-8
    if d < p - tolerance:
        return 1, p, rf"$\Theta(n^{{{p:.3g}}})$", "f(n) grows polynomially slower than n^p; leaf/recursive work dominates."
    if abs(d - p) <= tolerance:
        return 2, p, rf"$\Theta(n^{{{p:.3g}}}\log n)$", "Each recursion-tree level contributes the same asymptotic amount."
    return 3, p, rf"$\Theta(n^{{{d:.3g}}})$", "The top-level non-recursive work dominates (regularity condition assumed)."


def case_colour(case: int) -> str:
    return {1: BLUE, 2: TEAL, 3: ORANGE}[case]


def recurrence_text(a: int, b: int, d: float) -> str:
    ds = int(d) if float(d).is_integer() else d
    return rf"$T(n)={a}T(n/{b})+\Theta(n^{{{ds}}})$"


def draw_panels(fig, axes, a: int, b: int, d: float, h: int, visible_levels: int,
                demo_name: str | None = None) -> None:
    """Draw all four panels for one state."""
    ax_tree, ax_levels, ax_growth, ax_info = axes
    for ax in axes:
        ax.clear()
    case, p, result, reasoning = classify(a, b, d)
    colour = case_colour(case)
    n = b ** h
    visible_levels = max(1, min(int(visible_levels), h + 1))
    levels = np.arange(h + 1)
    level_work = np.array([(a ** int(i)) * ((n / (b ** int(i))) ** d) for i in levels], dtype=float)
    # Avoid unusable log-axis values for unusual edge cases.
    level_work = np.maximum(level_work, 1e-10)

    # ---------------- Recursion tree panel ----------------
    ax_tree.set_title("Recursion tree (schematic)", color=NAVY, fontsize=12, fontweight="bold", pad=9)
    ax_tree.set_xlim(-1.05, 1.05)
    ax_tree.set_ylim(-1.08, max(h, 4) + 0.6)
    ax_tree.axis("off")

    shown = min(visible_levels, h + 1)
    # Each row summarizes an entire level while drawing a manageable sample of nodes.
    for level in range(shown):
        y = h - level
        count = a ** level
        sample_n = min(count, 9)
        xs = np.linspace(-0.8, 0.8, sample_n) if sample_n > 1 else np.array([0.0])
        radius = 0.055 if sample_n >= 7 else 0.073
        # Connect sampled nodes in neighbouring levels. This is intentionally schematic:
        # exact node counts are written beside each row.
        if level > 0:
            prev_count = a ** (level - 1)
            prev_sample_n = min(prev_count, 9)
            prev_xs = np.linspace(-0.8, 0.8, prev_sample_n) if prev_sample_n > 1 else np.array([0.0])
            for j, x0 in enumerate(prev_xs):
                # Draw up to three representative branches from each shown parent.
                if prev_sample_n == 1:
                    candidates = range(min(sample_n, min(a, 3)))
                else:
                    center = int(round(j * (sample_n - 1) / max(1, prev_sample_n - 1)))
                    spread = max(1, min(3, a))
                    lo = max(0, center - spread // 2)
                    hi = min(sample_n, lo + spread)
                    candidates = range(lo, hi)
                for k in candidates:
                    ax_tree.add_patch(FancyArrowPatch(
                        (x0, y + 1 - 0.12), (xs[k], y + 0.15),
                        arrowstyle="-", linewidth=0.7, color=LIGHT_GREY,
                        connectionstyle="arc3,rad=0.0", zorder=1))

        # Scatter markers keep nodes circular regardless of the panel's aspect ratio.
        ax_tree.scatter(xs, np.full_like(xs, y, dtype=float), s=170 if sample_n < 7 else 120,
                        facecolors=LIGHT_BLUE, edgecolors=BLUE, linewidths=1.0, zorder=3)
        if count > sample_n:
            # Extra dots communicate that the row has many more nodes than are drawn.
            ax_tree.text(0.93, y, "…", ha="center", va="center", fontsize=17, color=GREY)
        subproblem = "n" if level == 0 else (rf"$n/{b}^{level}$" if level > 1 else rf"$n/{b}$")
        ax_tree.text(-1.02, y, f"L{level}", ha="right", va="center", fontsize=8.5, color=NAVY)
        ax_tree.text(0.0, y + 0.19, subproblem, ha="center", va="bottom", fontsize=8.3, color=DARK)
        ax_tree.text(0.0, y - 0.18, f"{count:,} node{'s' if count != 1 else ''}",
                     ha="center", va="top", fontsize=7.8, color=GREY)

    if shown < h + 1:
        ax_tree.text(0, h - shown - 0.1, "⋮", ha="center", va="center", fontsize=22, color=GREY)
        ax_tree.text(0, h - shown - 0.38, f"{h + 1 - shown} more level(s)",
                     ha="center", va="center", fontsize=8.5, color=GREY)
    ax_tree.text(0.0, -0.88, f"Level i contains a^i subproblems; n = b^h = {n:,}",
                 ha="center", va="center", fontsize=8.2, color=DARK)

    # ---------------- Work per level panel ----------------
    ax_levels.set_title("Work contributed by each level", color=NAVY, fontsize=12,
                        fontweight="bold", pad=9)
    visible_idx = np.arange(visible_levels)
    vals = level_work[visible_idx]
    ax_levels.bar(visible_idx, vals, color=[colour if i < h else NAVY for i in visible_idx],
                  width=0.7, edgecolor=WHITE, linewidth=0.7)
    ax_levels.set_xlabel("Recursion level i", fontsize=9)
    ax_levels.set_ylabel("Work at level i (log scale)", fontsize=9)
    ax_levels.set_yscale("log")
    ax_levels.set_xticks(visible_idx)
    ax_levels.tick_params(labelsize=8)
    ax_levels.grid(axis="y", which="both", color=LIGHT_GREY, linewidth=0.65)
    ax_levels.set_axisbelow(True)
    for i, value in zip(visible_idx, vals):
        ax_levels.text(i, value * 1.13, f"{value:.2g}", ha="center", va="bottom", fontsize=7.6, color=DARK)
    if case == 1:
        trend = "Level cost grows toward the leaves"
    elif case == 2:
        trend = "Level costs are asymptotically equal"
    else:
        trend = "Level cost shrinks toward the leaves"
    ax_levels.text(0.5, 0.96, trend, transform=ax_levels.transAxes, ha="center", va="top",
                   fontsize=8.5, color=colour, fontweight="bold")

    # ---------------- Growth comparison panel ----------------
    ax_growth.set_title("Compare f(n) with the critical term nᵖ", color=NAVY,
                        fontsize=12, fontweight="bold", pad=9)
    powers = np.arange(1, max(h, 4) + 2)
    ns = np.array([b ** int(q) for q in powers], dtype=float)
    critical = ns ** p
    nonrecursive = ns ** d
    ax_growth.loglog(ns, critical, marker="o", markersize=3.6, linewidth=2,
                     color=BLUE, label=rf"$n^p$, $p=\log_{{{b}}}{a}={p:.2f}$")
    ax_growth.loglog(ns, nonrecursive, marker="s", markersize=3.2, linewidth=2,
                     color=colour, label=rf"$f(n)=n^{d:g}$")
    ax_growth.set_xlabel("Input size n (log scale)", fontsize=9)
    ax_growth.set_ylabel("Growth (log scale)", fontsize=9)
    ax_growth.tick_params(labelsize=8)
    ax_growth.grid(True, which="both", color=LIGHT_GREY, linewidth=0.6)
    ax_growth.legend(loc="upper left", fontsize=8, frameon=True, framealpha=0.9)

    # ---------------- Result / equation panel ----------------
    ax_info.axis("off")
    ax_info.set_title("Master Theorem decision", color=NAVY, fontsize=12,
                      fontweight="bold", pad=9)
    ax_info.text(0.02, 0.92, recurrence_text(a, b, d), transform=ax_info.transAxes,
                 fontsize=15, color=NAVY, va="top")
    ax_info.text(0.02, 0.79, rf"Critical exponent: $p=\log_{{{b}}}{a}={p:.4f}$",
                 transform=ax_info.transAxes, fontsize=11, color=DARK, va="top")
    ax_info.text(0.02, 0.66, rf"Compare: $f(n)=\Theta(n^{{{d:g}}})$ with $n^p$",
                 transform=ax_info.transAxes, fontsize=10.2, color=DARK, va="top")

    case_name = {1: "CASE 1 — RECURSIVE WORK DOMINATES",
                 2: "CASE 2 — BALANCED CONTRIBUTIONS",
                 3: "CASE 3 — NON-RECURSIVE WORK DOMINATES"}[case]
    result_box = FancyBboxPatch((0.015, 0.28), 0.96, 0.22,
                                boxstyle="round,pad=0.012,rounding_size=0.015",
                                transform=ax_info.transAxes, facecolor=colour,
                                edgecolor=colour, alpha=0.13, linewidth=1.3)
    ax_info.add_patch(result_box)
    ax_info.text(0.04, 0.45, case_name, transform=ax_info.transAxes,
                 fontsize=9, color=colour, fontweight="bold", va="center")
    ax_info.text(0.04, 0.345, "Result: " + result, transform=ax_info.transAxes,
                 fontsize=13, color=NAVY, va="center")
    ax_info.text(0.02, 0.20, reasoning, transform=ax_info.transAxes,
                 fontsize=9.2, color=DARK, va="top", wrap=True)
    if case == 3:
        ax_info.text(0.02, 0.055, r"Check regularity:  a f(n/b) ≤ c f(n), for some c < 1.",
                     transform=ax_info.transAxes, fontsize=8.4, color=RED, va="bottom")
    else:
        ax_info.text(0.02, 0.055, f"Shown recursion levels: {visible_levels} of {h + 1}",
                     transform=ax_info.transAxes, fontsize=8.4, color=GREY, va="bottom")

    state_name = f" — {demo_name}" if demo_name else ""
    fig.suptitle(f"MASTER'S THEOREM EXPLORER{state_name}  |  n = bʰ = {n:,}",
                 fontsize=15, color=NAVY, fontweight="bold", y=0.965)


def render_frame(a: int, b: int, d: int, h: int, visible_levels: int,
                 demo_name: str | None = None, dpi: int = 105):
    """Render and return a single animation frame as an RGB numpy array."""
    fig = plt.figure(figsize=(12.6, 7.6), dpi=dpi, facecolor=WHITE)
    grid = fig.add_gridspec(2, 2, left=0.065, right=0.97, top=0.89, bottom=0.07,
                            wspace=0.27, hspace=0.36)
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1]),
            fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])]
    draw_panels(fig, axes, a, b, d, h, visible_levels, demo_name)
    fig.canvas.draw()
    frame = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
    plt.close(fig)
    return frame


def save_gif(path: str, fps: float, dpi: int) -> None:
    """Export a teaching GIF that demonstrates all three cases in sequence."""
    from PIL import Image

    demonstrations = [
        # Case 1: Strassen's recurrence;  n^2 grows slower than n^(log_2 7).
        (7, 2, 2, 4, "Case 1 — Strassen's recurrence"),
        # Case 2: Merge Sort; all levels contribute linear work.
        (2, 2, 1, 5, "Case 2 — Merge Sort"),
        # Case 3: the combine work n^2 dominates a recursion with two half-size calls.
        (2, 2, 2, 5, "Case 3 — Non-recursive work dominates"),
    ]
    frames = []
    for a, b, d, h, title in demonstrations:
        for visible in range(1, h + 2):
            frame = render_frame(a, b, d, h, visible, title, dpi=dpi)
            frames.append(Image.fromarray(frame))

    # Hold the last frame briefly so that viewers can read the final takeaway.
    if frames:
        frames.extend([frames[-1].copy()] * max(1, int(fps * 2)))
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    duration_ms = max(100, round(1000 / max(0.2, fps)))
    frames[0].save(destination, save_all=True, append_images=frames[1:],
                   duration=duration_ms, loop=0, optimize=True)
    print(f"Saved animated GIF: {destination}")
    print(f"Frames: {len(frames)} | Playback: {fps:g} fps | Size: {frames[0].size[0]}x{frames[0].size[1]}")


class InteractiveExplorer:
    def __init__(self) -> None:
        self.a, self.b, self.d, self.h = 2, 2, 1, 5
        self.visible_levels = 1
        self.playing = False
        self._in_update = False

        self.fig = plt.figure(figsize=(13.5, 9.5), facecolor=WHITE)
        grid = self.fig.add_gridspec(2, 2, left=0.065, right=0.97, top=0.88, bottom=0.29,
                                     wspace=0.27, hspace=0.35)
        self.axes = [self.fig.add_subplot(grid[0, 0]), self.fig.add_subplot(grid[0, 1]),
                     self.fig.add_subplot(grid[1, 0]), self.fig.add_subplot(grid[1, 1])]

        # Slider row 1
        ax_a = self.fig.add_axes([0.12, 0.205, 0.31, 0.025], facecolor="#F3F5F8")
        ax_b = self.fig.add_axes([0.60, 0.205, 0.28, 0.025], facecolor="#F3F5F8")
        # Slider row 2
        ax_d = self.fig.add_axes([0.12, 0.145, 0.31, 0.025], facecolor="#F3F5F8")
        ax_h = self.fig.add_axes([0.60, 0.145, 0.28, 0.025], facecolor="#F3F5F8")
        self.slider_a = Slider(ax_a, "a: subproblems", 1, 8, valinit=self.a, valstep=1, color=BLUE)
        self.slider_b = Slider(ax_b, "b: shrink factor", 2, 4, valinit=self.b, valstep=1, color=BLUE)
        self.slider_d = Slider(ax_d, "d: exponent in nᵈ", 0, 4, valinit=self.d, valstep=1, color=TEAL)
        self.slider_h = Slider(ax_h, "h: recursion depth", 2, 6, valinit=self.h, valstep=1, color=TEAL)
        for slider in (self.slider_a, self.slider_b, self.slider_d, self.slider_h):
            slider.label.set_color(NAVY)
            slider.label.set_fontsize(9)
            slider.valtext.set_color(NAVY)
            slider.valtext.set_fontsize(9)
            slider.on_changed(self._on_slider)

        # Buttons
        button_specs = [
            (0.12, 0.055, 0.13, 0.052, "◀ Previous", self.previous),
            (0.27, 0.055, 0.13, 0.052, "Next level ▶", self.next_level),
            (0.42, 0.055, 0.12, 0.052, "Reset", self.reset),
            (0.56, 0.055, 0.15, 0.052, "▶ Play / Pause", self.toggle_play),
            (0.73, 0.055, 0.15, 0.052, "Use Merge Sort", self.load_mergesort),
        ]
        self.buttons = []
        for x, y, w, h, label, callback in button_specs:
            ax = self.fig.add_axes([x, y, w, h])
            btn = Button(ax, label, color="#F3F5F8", hovercolor=LIGHT_BLUE)
            btn.label.set_color(NAVY)
            btn.label.set_fontsize(8.5)
            btn.on_clicked(callback)
            self.buttons.append(btn)
        self.play_button = self.buttons[3]
        self.timer = self.fig.canvas.new_timer(interval=850)
        self.timer.add_callback(self._timer_tick)

        self.fig.text(0.5, 0.012,
                      "Change a, b, d and h to explore the cases. For polynomial f(n)=nᵈ, Case 3 assumes regularity.",
                      ha="center", va="bottom", color=GREY, fontsize=8.5)
        self._redraw()

    def _redraw(self) -> None:
        draw_panels(self.fig, self.axes, self.a, self.b, self.d, self.h, self.visible_levels)
        self.fig.canvas.draw_idle()

    def _on_slider(self, _value) -> None:
        if self._in_update:
            return
        self.a = int(self.slider_a.val)
        self.b = int(self.slider_b.val)
        self.d = int(self.slider_d.val)
        self.h = int(self.slider_h.val)
        self.visible_levels = min(self.visible_levels, self.h + 1)
        self._redraw()

    def previous(self, _event=None) -> None:
        self.visible_levels = max(1, self.visible_levels - 1)
        self._redraw()

    def next_level(self, _event=None) -> None:
        self.visible_levels = min(self.h + 1, self.visible_levels + 1)
        self._redraw()

    def reset(self, _event=None) -> None:
        self.visible_levels = 1
        self._redraw()

    def _timer_tick(self) -> None:
        if not self.playing:
            return
        if self.visible_levels >= self.h + 1:
            self.visible_levels = 1
        else:
            self.visible_levels += 1
        self._redraw()

    def toggle_play(self, _event=None) -> None:
        self.playing = not self.playing
        if self.playing:
            self.play_button.label.set_text("Ⅱ Pause")
            self.timer.start()
        else:
            self.timer.stop()
            self.play_button.label.set_text("▶ Play / Pause")
        self.fig.canvas.draw_idle()

    def load_mergesort(self, _event=None) -> None:
        self._in_update = True
        self.slider_a.set_val(2)
        self.slider_b.set_val(2)
        self.slider_d.set_val(1)
        self.slider_h.set_val(5)
        self._in_update = False
        self.a, self.b, self.d, self.h = 2, 2, 1, 5
        self.visible_levels = 1
        self._redraw()

    def show(self) -> None:
        plt.show()


def main() -> None:
    if ARGS.save_gif:
        save_gif(ARGS.save_gif, ARGS.fps, ARGS.dpi)
    else:
        InteractiveExplorer().show()


if __name__ == "__main__":
    main()

