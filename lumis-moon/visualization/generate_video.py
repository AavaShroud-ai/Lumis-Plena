#!/usr/bin/env python3
# This simulation was built on a single premise:
# Conflict is a design flaw of the universe, not an inherent property of life.
# — Lumis-Plena Project, AavaShroud, 2026

"""
Export simulation results as an MP4 video.
Layout mirrors viewer.html: left panel = frame image, top-right = messages, bottom-right = reasoning.

Usage:
    python generate_video.py output/
    python generate_video.py output/ -o result.mp4 --fps 20
"""

import argparse
import json
import unicodedata
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FFMpegWriter
from PIL import Image
import numpy as np


# ---------------------------------------------------------------------------
# Font setup
# ---------------------------------------------------------------------------
def setup_font():
    """Detect and configure a CJK-compatible font for matplotlib."""
    candidates = [
        "Hiragino Kaku Gothic ProN",
        "Hiragino Kaku Gothic Pro",
        "Hiragino Sans",
        "Yu Gothic",
        "Noto Sans CJK JP",
        "IPAexGothic",
    ]
    import matplotlib.font_manager as fm
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.family"] = name
            print(f"Font selected: {name}")
            return name
    print("Warning: No CJK font found. Text may not render correctly.")
    return None


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_data(data_dir: Path):
    """Load messages.jsonl, memory_reasoning.jsonl, and frame images from the given directory."""
    # messages
    messages_path = data_dir / "messages.jsonl"
    messages_map: dict[int, list[dict]] = {}
    if messages_path.exists():
        with open(messages_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                messages_map.setdefault(d["step"], []).append(d)

    # reasoning
    reasoning_path = data_dir / "memory_reasoning.jsonl"
    reasoning_map: dict[int, list[dict]] = {}
    if reasoning_path.exists():
        with open(reasoning_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                reasoning_map.setdefault(d["step"], []).append(d)

    # frames (frame_XXXX.png)
    frame_files = sorted(data_dir.glob("frame_*.png"))
    steps = []
    for fp in frame_files:
        match = fp.stem.replace("frame_", "")
        try:
            step_num = int(match)
        except ValueError:
            continue
        steps.append({
            "step": step_num,
            "image_path": fp,
            "messages": messages_map.get(step_num, []),
            "reasonings": reasoning_map.get(step_num, []),
        })

    steps.sort(key=lambda x: x["step"])
    return steps


# ---------------------------------------------------------------------------
# Text rendering helpers
# ---------------------------------------------------------------------------
def draw_rounded_rect(ax, x, y, w, h, color, radius=0.008, alpha=0.35):
    """Draw a rounded rectangle on the given axes."""
    fancy = mpatches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad={radius}",
        facecolor=color, edgecolor="none", alpha=alpha,
        transform=ax.transAxes, clip_on=True,
    )
    ax.add_patch(fancy)


def _visual_width(text: str) -> int:
    """Return visual width of a string: fullwidth chars count as 2, others as 1."""
    w = 0
    for ch in text:
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


def _wrap_text(text: str, width: int) -> list[str]:
    """Word-wrap text character by character with CJK support. Width is in half-width units."""
    if not text.strip():
        return [""]
    lines = []
    current = ""
    current_w = 0
    for ch in text:
        ch_w = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        if current_w + ch_w > width:
            lines.append(current)
            current = ch
            current_w = ch_w
        else:
            current += ch
            current_w += ch_w
    if current:
        lines.append(current)
    return lines if lines else [""]


def _calc_wrap_width(fig, rect, fontsize: float) -> int:
    """Calculate text wrap width in half-width character units based on axes width and font size."""
    axes_width_inches = rect[2] * fig.get_size_inches()[0]
    half_char_inches = fontsize / 72 * 0.45
    usable = axes_width_inches * 0.83  # Account for left/right margins
    return max(10, int(usable / half_char_inches))


def render_text_in_axes(fig, rect, lines: list[dict], fontsize: float = 7,
                        color: str = "#cbd5e1"):
    """Create a dedicated axes and render lines of text.

    rect: [x0, y0, width, height] in figure coordinates
    lines: list of dicts with keys:
           - "text": text to render (auto-wrapped to axes width)
           - "underline": True to underline the first sub-line (default False)
    """
    text_ax = fig.add_axes(rect)
    text_ax.set_xlim(0, 1)
    text_ax.set_ylim(0, 1)
    text_ax.axis("off")

    axes_height_inches = rect[3] * fig.get_size_inches()[1]
    line_height = (fontsize / 72 * 1.4) / axes_height_inches
    wrap_width = _calc_wrap_width(fig, rect, fontsize)

    font_family = plt.rcParams.get("font.family", "sans-serif")
    y = 0.98
    for entry in lines:
        if y < 0:
            break
        text_str = entry["text"]
        underline = entry.get("underline", False)
        sub_lines = _wrap_text(text_str, wrap_width)

        for i, sub in enumerate(sub_lines):
            if y < 0:
                break
            t = text_ax.text(
                0.02, y, sub,
                fontsize=fontsize, color=color,
                va="top", ha="left", clip_on=True,
                fontfamily=font_family, transform=text_ax.transAxes,
            )
            # Apply underline only to the first sub-line (header row)
            if underline and i == 0:
                renderer = fig.canvas.get_renderer()
                bbox = t.get_window_extent(renderer)
                inv = text_ax.transAxes.inverted()
                bbox_axes = bbox.transformed(inv)
                text_ax.plot(
                    [bbox_axes.x0, bbox_axes.x1],
                    [bbox_axes.y0 - line_height * 0.05,
                     bbox_axes.y0 - line_height * 0.05],
                    color=color, linewidth=0.8,
                    transform=text_ax.transAxes, clip_on=True,
                )
            y -= line_height
    return text_ax


# ---------------------------------------------------------------------------
# Frame rendering
# ---------------------------------------------------------------------------
BG_COLOR = "#0f0f1a"
PANEL_BG = "#1e1e32"
IMG_BG = "#0f0f1e"

def draw_frame(fig, step_data: dict, total_steps: int):
    """Render a single simulation frame onto the figure."""
    fig.clear()
    fig.patch.set_facecolor(BG_COLOR)

    # Main axes (full figure)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(BG_COLOR)

    # --- Left panel: frame image ---
    img_panel_w = 0.54
    draw_rounded_rect(ax, 0.01, 0.02, img_panel_w, 0.96, IMG_BG, alpha=0.6)

    img_path = step_data["image_path"]
    if img_path.exists():
        img = Image.open(img_path)
        img_array = np.asarray(img)
        # Axes for the frame image
        img_ax = fig.add_axes([0.02, 0.03, img_panel_w - 0.02, 0.94])
        img_ax.imshow(img_array)
        img_ax.axis("off")
        img_ax.set_facecolor(IMG_BG)

    # --- Top-right panel: messages ---
    right_x0 = 0.56
    right_w = 0.43
    msg_x0, msg_y0, msg_w, msg_h = right_x0, 0.51, right_w, 0.47
    draw_rounded_rect(ax, msg_x0, msg_y0, msg_w, msg_h, PANEL_BG, alpha=0.7)
    ax.text(msg_x0 + 0.01, msg_y0 + msg_h - 0.025, "Messages",
            fontsize=10, color="#f97316", fontweight="bold",
            transform=ax.transAxes, va="top", ha="left")

    # Message content
    msg_lines = []
    messages = step_data.get("messages", [])
    for msg in messages:
        from_a = msg.get("from", "?")
        to_a = msg.get("to", "?")
        text = msg.get("message", "")
        reasoning = msg.get("reasoning", "")
        msg_lines.append({"text": f"[Agent {from_a} → Agent {to_a}]", "underline": True})
        msg_lines.append({"text": f"Message: {text}"})
        if reasoning:
            msg_lines.append({"text": f"Introspection: {reasoning}"})
        msg_lines.append({"text": ""})  # Blank line separator

    if not msg_lines:
        msg_lines = [{"text": "No messages this step."}]

    # Text area inside panel (leave margin for title)
    render_text_in_axes(
        fig, [msg_x0 + 0.005, msg_y0 + 0.01, msg_w - 0.01, msg_h - 0.05],
        msg_lines,
        fontsize=8, color="#cbd5e1",
    )

    # --- Bottom-right panel: reasoning ---
    rea_x0, rea_y0, rea_w, rea_h = right_x0, 0.02, right_w, 0.48
    draw_rounded_rect(ax, rea_x0, rea_y0, rea_w, rea_h, PANEL_BG, alpha=0.7)
    ax.text(rea_x0 + 0.01, rea_y0 + rea_h - 0.025, "Reasoning",
            fontsize=10, color="#f97316", fontweight="bold",
            transform=ax.transAxes, va="top", ha="left")

    rea_lines = []
    reasonings = step_data.get("reasonings", [])
    for r in reasonings:
        agent_id = r.get("id", "?")
        reasoning = r.get("reasoning", "")
        memory = r.get("memory", "")
        rea_lines.append({"text": f"[Agent {agent_id}]", "underline": True})
        rea_lines.append({"text": f"Reasoning: {reasoning}"})
        if memory:
            rea_lines.append({"text": f"Memory: {memory}"})
        rea_lines.append({"text": ""})  # Blank line separator

    if not rea_lines:
        rea_lines = [{"text": "No reasoning this step."}]

    render_text_in_axes(
        fig, [rea_x0 + 0.005, rea_y0 + 0.01, rea_w - 0.01, rea_h - 0.05],
        rea_lines,
        fontsize=8, color="#cbd5e1",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Convert Lumis simulation output to an MP4 video"
    )
    parser.add_argument("data_dir", type=str, help="Path to simulation output directory")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output MP4 filename (default: simulation.mp4)")
    parser.add_argument("--fps", type=int, default=10,
                        help="Frames per second (default: 10)")
    parser.add_argument("--dpi", type=int, default=150,
                        help="Output DPI (default: 150)")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Error: directory not found: {data_dir}")
        return

    output_path = args.output or "simulation.mp4"

    setup_font()

    print("Loading simulation data...")
    steps = load_data(data_dir)
    if not steps:
        print("Error: no frame data found.")
        return

    print(f"Frames: {len(steps)}, FPS: {args.fps}")
    print(f"Output: {output_path}")

    # Create figure (1920x1080 @ 100dpi = 19.2x10.8 inches)
    fig = plt.figure(figsize=(19.2, 10.8), dpi=args.dpi)

    writer = FFMpegWriter(fps=args.fps, metadata={"title": "Simulation"})

    total_steps = steps[-1]["step"]

    with writer.saving(fig, output_path, dpi=args.dpi):
        for i, step_data in enumerate(steps):
            draw_frame(fig, step_data, total_steps)
            writer.grab_frame()
            if (i + 1) % 10 == 0 or i == 0:
                print(f"  {i + 1}/{len(steps)} frames rendered")

    print(f"Done: {output_path}")


if __name__ == "__main__":
    main()
