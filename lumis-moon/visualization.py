# This simulation was built on a single premise:
# Conflict is a design flaw of the universe, not an inherent property of life.
# — Lumis-Plena Project, AavaShroud, 2026

"""
Visualization for LLM Multi-Agent 2D Simulation
"""
import matplotlib
import os
import time
import logging
from typing import List, Dict, Tuple, Optional
from agent import lumis_name

# Set backend for compatibility (Mac, Linux, WSL)
GUI_BACKENDS = ['TkAgg', 'Qt5Agg', 'MacOSX', 'Qt4Agg']
NON_GUI_BACKENDS = ['agg', 'pdf', 'svg', 'ps']

# Visualization constants
FIGURE_SIZE = (10, 10)
STATS_FIGURE_SIZE = (12, 8)
DPI = 150
INITIAL_WINDOW_DELAY = 0.5
VISUALIZATION_PAUSE = 0.05
STATS_PAUSE = 0.1

# Agent visualization constants
AGENT_SIZE_IN_BAR = 100
AGENT_SIZE_OUTSIDE = 120
AGENT_ALPHA = 0.7
COMMUNICATION_LINK_ALPHA = 0.3

# Place visualization constants
BAR_LINEWIDTH = 2
BAR_ALPHA = 0.3

# Fire visualization constants
FIRE_MARKER_SIZE = 200
FIRE_CIRCLE_ALPHA = 0.15
FIRE_CIRCLE_LINEWIDTH = 2

# Statistics plot constants (will be made configurable)
DEFAULT_OCCUPANCY_THRESHOLD = 0.6
DEFAULT_AGENT_THRESHOLD = 12
MAX_AGENTS_DISPLAY = 20

# Set backend for compatibility (Mac, Linux, WSL)
backend_set = False

# Check if we're in WSL or headless environment
is_wsl = 'microsoft' in os.uname().release.lower() if hasattr(os, 'uname') else False
is_headless = not os.environ.get('DISPLAY') and not is_wsl

if is_wsl or is_headless:
    # Use non-GUI backend for WSL or headless environments
    try:
        matplotlib.use('Agg')
        backend_set = True
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Using Agg backend (non-GUI) for WSL/headless environment")
    except Exception:
        pass
else:
    # Try GUI backends for interactive environments
    for backend_name in GUI_BACKENDS:
        try:
            matplotlib.use(backend_name)
            backend_set = True
            break
        except (ImportError, ValueError):
            continue

if not backend_set:
    # Fallback to Agg backend (non-GUI, always available)
    try:
        matplotlib.use('Agg')
        backend_set = True
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("No GUI backend available. Using Agg backend (non-GUI). Visualization windows will not display.")
    except Exception:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Failed to set matplotlib backend. Visualization may not work.")

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors
import numpy as np

logger = logging.getLogger(__name__)


class Visualizer:
    """Visualization class for simulation"""

    def __init__(self, half_space_size: int, places: List[Dict], num_agents: int = None):
        self.half_space_size = half_space_size
        self.places = places
        self.num_agents = num_agents
        self.fig = None
        self.ax = None
        self.figure_initialized = False

    def setup_figure(self, reuse_existing: bool = False, is_night: bool = False):
        """Setup matplotlib figure"""
        if reuse_existing and self.fig is not None:
            # Clear existing figure instead of creating new one
            self.ax.clear()
        else:
            # Create new figure
            self.fig, self.ax = plt.subplots(figsize=FIGURE_SIZE)
            self.figure_initialized = True

        # Set up axes properties (lunar surface)
        self.ax.set_xlim(-self.half_space_size, self.half_space_size)
        self.ax.set_ylim(-self.half_space_size, self.half_space_size)
        self.ax.set_aspect('equal')

        if is_night:
            text_color = 'lightgray'
            grid_color = 'gray'
            spine_color = 'gray'
        else:
            text_color = '#222222'
            grid_color = 'rgba(0,0,0,0.15)'
            grid_color = '#888888'
            spine_color = '#888888'

        # Apply background image (switches between day and night)
        import os
        bg_img_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'bgimage-moon-nighttime.png' if is_night else 'bgimage-moon-daytime.png'
        )
        try:
            import matplotlib.image as mpimg
            bg_img = mpimg.imread(bg_img_path)
            self.ax.imshow(
                bg_img,
                extent=[-self.half_space_size, self.half_space_size,
                        -self.half_space_size, self.half_space_size],
                aspect='auto',
                zorder=0,
                alpha=0.85
            )
            self.fig.patch.set_facecolor('#000000' if is_night else '#d0ccc0')
        except Exception:
            # Fallback if background image is not found
            bg_color = '#0a0a1a' if is_night else '#f5f5f5'
            self.ax.set_facecolor(bg_color)
            self.fig.patch.set_facecolor(bg_color)

        self.ax.set_xlabel('X', color=text_color)
        self.ax.set_ylabel('Y', color=text_color)
        self.ax.grid(True, alpha=0.15, color=grid_color)
        self.ax.tick_params(colors=text_color)
        for spine in self.ax.spines.values():
            spine.set_edgecolor(spine_color)
        self.is_night = is_night
        self.label_color = 'cyan' if is_night else 'white'
        self.agent_label_color_large = 'white'
        self.agent_label_color_small = 'white'

    def draw_bars(self):
        """Draw all place areas (bars, cafes, libraries, etc.)"""
        # Color palette for different place types
        place_type_colors = {
            'bar': 'lightblue',
            'cafe': 'lightcoral',
            'library': 'lightgreen',
            'restaurant': 'lightyellow',
            'park': 'lightpink',
            'lunar_base': '#1a3a5c',  # Dark blue for lunar base
        }
        default_colors = ['lightblue', 'lightcoral', 'lightgreen', 'lightyellow', 'lightpink']
        
        for i, place in enumerate(self.places):
            half_size = place['half_size']
            center_x = place['center_x']
            center_y = place['center_y']
            if 'name' not in place:
                raise ValueError(f"Place at index {i} is missing required field: 'name'")
            place_name = place['name']
            place_type = place['type']
            
            # Choose color based on place type
            if place_type in place_type_colors:
                face_color = place_type_colors[place_type]
            else:
                face_color = default_colors[i % len(default_colors)]
            
            # Place covers -half_size to +half_size from center (inclusive)
            # Rectangle width/height = 2 * half_size + 1 to cover all cells
            place_width = 2 * half_size + 1
            place_rect = patches.Rectangle(
                (center_x - half_size - 0.5, center_y - half_size - 0.5),
                place_width,
                place_width,
                linewidth=BAR_LINEWIDTH,
                edgecolor='cyan',
                facecolor=face_color,
                alpha=BAR_ALPHA,
                label=f"{place_name} ({place_type})"
            )
            self.ax.add_patch(place_rect)
            
            label_text = f"{place_name}\n({place_type})"
            self.ax.text(
                center_x,
                center_y,
                label_text,
                fontsize=9,
                ha='center',
                va='center',
                weight='bold',
                color=self.label_color
            )
    
    def draw_fires(self, fire_states: List[Dict]):
        """Draw fire center markers and perception radius circles for all active fires.

        Fire areas are colored using a colormap based on intensity (0.0-1.0).
        """
        fire_cmap = matplotlib.colormaps['YlOrRd']

        for fire in fire_states:
            if not fire.get('active'):
                continue

            fx, fy = fire['position']
            radius = fire['radius']
            intensity = fire['intensity']
            name = fire.get('name', 'fire')

            # Map intensity to color via colormap
            face_color = fire_cmap(intensity)

            # Draw perception radius circle with intensity-based color
            fire_circle = patches.Circle(
                (fx, fy),
                radius,
                linewidth=FIRE_CIRCLE_LINEWIDTH,
                edgecolor='red',
                facecolor=face_color,
                alpha=FIRE_CIRCLE_ALPHA + 0.1,
                linestyle='--',
            )
            self.ax.add_patch(fire_circle)

            # Draw fire center marker
            self.ax.scatter(
                fx, fy,
                c='red',
                s=FIRE_MARKER_SIZE,
                marker='^',
                edgecolors='darkred',
                linewidths=2,
                zorder=10,
            )

            # Label
            self.ax.text(
                fx, fy - 1.5,
                f'{name}\n(int={intensity})',
                fontsize=8,
                ha='center',
                va='top',
                color='darkred',
                fontweight='bold',
            )

    def draw_agents(
        self,
        agents: List,
        agents_by_place: Dict[str, List[int]],
        communication_links: List[Tuple[int, int]] = None,
        current_step: int = 0
    ):
        """Draw agents and communication links"""
        # If multiple agents share the same position, spread them visually in a circle (actual coordinates unchanged)
        import math
        from collections import defaultdict
        position_groups = defaultdict(list)
        for agent in agents:
            position_groups[agent.position].append(agent)

        draw_offsets = {}
        SPREAD_RADIUS = 0.6
        for pos, group in position_groups.items():
            n = len(group)
            if n == 1:
                draw_offsets[group[0].id] = (0, 0)
            else:
                for i, a in enumerate(group):
                    angle = 2 * math.pi * i / n
                    draw_offsets[a.id] = (
                        SPREAD_RADIUS * math.cos(angle),
                        SPREAD_RADIUS * math.sin(angle)
                    )

        # Draw familiarity lines: only each agent's single strongest bond.
        # Previously every pair scoring >= 0.8 was drawn, which at high
        # population turned the field into a dense green mesh. Thinning to
        # one line per agent (its closest living tie) keeps each Lumis's
        # strongest relationship legible. Pairs are deduplicated, so a mutual
        # strongest bond (A's best is B and B's best is A) draws once; if B's
        # best is instead C, then B is touched by two lines (A→B and B→C),
        # each of which is genuinely some agent's single strongest bond.
        drawn_pairs = set()
        agent_map_all = {a.id: a for a in agents}
        for agent in agents:
            # Pick this agent's strongest bond among currently living agents.
            best_id = None
            best_score = 0.0
            for other_id in agent.familiarity:
                if other_id not in agent_map_all:
                    continue
                score = agent.get_familiarity_score(other_id)
                if score > best_score:
                    best_score = score
                    best_id = other_id
            if best_id is None or best_score < 0.8:
                continue
            pair = tuple(sorted([agent.id, best_id]))
            if pair in drawn_pairs:
                continue
            drawn_pairs.add(pair)
            other = agent_map_all[best_id]
            ox1, oy1 = draw_offsets.get(agent.id, (0, 0))
            ox2, oy2 = draw_offsets.get(other.id, (0, 0))
            self.ax.plot(
                [agent.position[0] + ox1, other.position[0] + ox2],
                [agent.position[1] + oy1, other.position[1] + oy2],
                color='#00ffaa',
                alpha=min(0.3, best_score * 0.35),
                linewidth=best_score * 2
            )

        # Draw communication links
        if communication_links:
            agent_map = {a.id: a for a in agents}
            for agent_id1, agent_id2 in communication_links:
                agent1 = agent_map.get(agent_id1)
                agent2 = agent_map.get(agent_id2)
                if agent1 is None or agent2 is None:
                    continue
                self.ax.plot(
                    [agent1.position[0], agent2.position[0]],
                    [agent1.position[1], agent2.position[1]],
                    'gray',
                    alpha=COMMUNICATION_LINK_ALPHA,
                    linewidth=1
                )

        for agent in agents:
            is_large = getattr(agent, 'lumis_type', 'small') == 'large'

            if getattr(agent, 'reproducing', False):
                # Reproducing or rearing: priority display regardless of location
                rep_type = getattr(agent, 'reproduction_type', None)
                if rep_type == "clone":
                    color = '#ff1493'      # Hot pink: clone parent (preparation or rearing)
                    edge_color = '#cc1060'
                elif rep_type == "sexual":
                    color = '#6600cc'      # Deep purple: sexual reproduction parent (preparation or rearing)
                    edge_color = '#9900cc'
                elif rep_type == "sexual_support":
                    color = '#6600cc'      # Deep purple: sexual reproduction parent (preparation or rearing)
                    edge_color = '#bb44bb'
                else:
                    color = '#ff1493'      # Fallback color
                    edge_color = '#cc1060'
            elif current_step <= getattr(agent, 'rearing_until_step', -1):
                # Rearing period: reproduction_type was already cleared to None
                # at birth (see simulation.py), so use last_reproduction_type,
                # which simulation.py saves right before that reset. Previously
                # this branch ignored type entirely and always rendered
                # hot pink, so sexual-reproduction parents looked identical
                # to clone parents throughout the whole rearing period.
                last_rep_type = getattr(agent, 'last_reproduction_type', None)
                if last_rep_type in ("sexual", "sexual_support"):
                    color = '#6600cc'      # Deep purple: sexual reproduction parent (rearing)
                    edge_color = '#9900cc' if last_rep_type == "sexual" else '#bb44bb'
                else:
                    color = '#ff1493'      # Hot pink: clone parent (rearing)
                    edge_color = '#ff70aa'
            elif getattr(agent, 'parent_ids', []) and (current_step - agent.birth_step) <= 30:
                # Newborn check: MUST come before in_place to override cyan
                if len(agent.parent_ids) == 2:
                    color = '#e8c8ff'      # Light purple: newborn from two-parent reproduction
                    edge_color = '#d4a0ff'
                else:
                    color = '#ffd6e0'      # Light pink: newborn from clone
                    edge_color = '#ffaacc'
            elif agent.in_place and agent.current_place:
                color = '#00ffff'
                edge_color = 'white'
            elif getattr(agent, 'is_sheltering', False):
                color = '#ffffff'      # White: sheltering from flare
                edge_color = '#aaaaaa'
            elif getattr(agent, 'is_resting', False):
                color = '#ffd700'      # Gold: photosynthesizing outside
                edge_color = '#cc9900'
            else:
                # Color varies by energy level
                e = agent.energy / getattr(agent, 'energy_capacity', 1.0)
                if e > 0.6:
                    color = '#7fdfff'    # Light blue: healthy energy
                    edge_color = '#00aaff'
                elif e > 0.3:
                    color = '#aaff00'    # Yellow-green: medium energy
                    edge_color = '#88cc00'
                else:
                    color = '#ff4444'    # Red: low energy
                    edge_color = '#cc0000'

            if is_large:
                marker = 'H'            # Hexagon marker for large Lumis
                size = AGENT_SIZE_OUTSIDE * 4
            else:
                marker = 'o'            # Circle marker for small Lumis
                size = AGENT_SIZE_OUTSIDE

            ox, oy = draw_offsets.get(agent.id, (0, 0))
            self.ax.scatter(
                agent.position[0] + ox,
                agent.position[1] + oy,
                c=color,
                s=size,
                marker=marker,
                alpha=AGENT_ALPHA,
                edgecolors=edge_color,
                linewidths=1.5
            )

            # Add Lumis ID label — use the agent's own display_name (set correctly
            # at construction time with the real num_large) rather than
            # recomputing lumis_name(agent.id) here with its default num_large=4.
            # Recomputing it was the same class of bug as the run-009 L2/L3
            # mislabeling: this file never picked up that fix because it wasn't
            # reading from the agent object at all.
            label = getattr(agent, 'display_name', None) or lumis_name(agent.id)
            self.ax.text(
                agent.position[0] + ox + 0.5,
                agent.position[1] + oy + 0.5,
                label,
                fontsize=8 if is_large else 7,
                ha='left',
                color=self.agent_label_color_large if is_large else self.agent_label_color_small,
                fontweight='bold' if is_large else 'normal'
            )
    
    def visualize_step(
        self,
        agents: List,
        place_status: Dict,
        step: int,
        communication_radius: float = None,
        save_path: str = None,
        fire_states: Optional[List[Dict]] = None,
        active_flare: Optional[Dict] = None,
        corpses: Optional[List[Dict]] = None
    ):
        """Visualize a single simulation step"""
        # For saving frames, create new figure each time and close after saving
        # For interactive display, reuse existing figure
        reuse = save_path is None and self.figure_initialized
        is_night = bool(fire_states) and any(f.get('active') for f in fire_states)
        self.setup_figure(reuse_existing=reuse, is_night=is_night)
        self.draw_bars()
        self.draw_fires(fire_states or [])
        
        # Get agents by place
        agents_by_place = {}
        for place in self.places:
            agents_by_place[place['name']] = [agent.id for agent in agents 
                                          if agent.in_place and agent.current_place == place['name']]
        
        # Find communication links (same-area condition: same place or both outside)
        communication_links = []
        if communication_radius:
            for i, agent1 in enumerate(agents):
                for agent2 in agents[i+1:]:
                    dist = agent1.distance_to(agent2.position)
                    # Must be within radius AND in the same area:
                    # - Both outside places, OR
                    # - Both in the same place
                    same_area = (
                        (not agent1.in_place and not agent2.in_place) or
                        (agent1.in_place and agent2.in_place and 
                         agent1.current_place == agent2.current_place)
                    )
                    if dist <= communication_radius and same_area:
                        communication_links.append((agent1.id, agent2.id))
        
        self.draw_agents(agents, agents_by_place, communication_links, current_step=step)

        # Memory transfer visualization: detect agents that disappeared and draw a light beam
        if hasattr(self, '_prev_agent_positions') and self._prev_agent_positions:
            prev_ids = set(self._prev_agent_positions.keys())
            curr_ids = {a.id for a in agents}
            dead_ids = prev_ids - curr_ids
            for dead_id in dead_ids:
                dead_pos = self._prev_agent_positions[dead_id]
                # Find the nearest surviving agent
                if agents:
                    nearest = min(agents, key=lambda a: (
                        (a.position[0] - dead_pos[0])**2 +
                        (a.position[1] - dead_pos[1])**2
                    ))
                    # Draw the memory transfer beam
                    self.ax.annotate(
                        '',
                        xy=(nearest.position[0], nearest.position[1]),
                        xytext=(dead_pos[0], dead_pos[1]),
                        arrowprops=dict(
                            arrowstyle='->', color='#ffffff',
                            lw=2.5, connectionstyle='arc3,rad=0.2'
                        ),
                        zorder=10
                    )
                    # Mark the position of the deceased agent with ×
                    self.ax.scatter(
                        dead_pos[0], dead_pos[1],
                        marker='x', s=120, color='#ff8888',
                        linewidths=2.5, zorder=10
                    )

        # Record current agent positions for next step comparison
        self._prev_agent_positions = {a.id: a.position for a in agents}

        # Draw corpses: black dots at the place of death, persisting until a Lumis
        # recovers the body. This is the visual counterpart to the burial mechanic —
        # a body left on the surface stays visible so its recovery (or its waiting)
        # can be seen.
        if corpses:
            cx = [c['position'][0] for c in corpses]
            cy = [c['position'][1] for c in corpses]
            self.ax.scatter(
                cx, cy,
                marker='o', s=70, color='#000000',
                edgecolors='#444444', linewidths=1.0, zorder=9
            )
        
        # Build title with statistics for all places
        alive_count = len(agents)
        if 'places' in place_status:
            place_info = []
            for place_name, status in place_status['places'].items():
                place_info.append(
                    f"{place_name}: {status['agents_in_place']}/{status['capacity']} "
                    f"({status['occupancy_rate']:.0%})"
                )
            title = (
                f"Step {step} | Alive: {alive_count} | "
                f"Total in places: {place_status['agents_in_place']} "
                f"({place_status['occupancy_rate']:.1%}) | "
                f"{' | '.join(place_info)}"
            )
        else:
            title = (
                f"Step {step} | Alive: {alive_count} | "
                f"Agents in place: {place_status['agents_in_place']}/{place_status['capacity']} "
                f"({place_status['occupancy_rate']:.1%})"
            )
        # Append fire info to title if any active
        active_fires = [f for f in (fire_states or []) if f.get('active')]
        if active_fires:
            # Draw lunar night overlay
            night_overlay = patches.Rectangle(
                (-self.half_space_size, -self.half_space_size),
                self.half_space_size * 2,
                self.half_space_size * 2,
                linewidth=0,
                facecolor='#000033',
                alpha=0.4,
                zorder=5
            )
            self.ax.add_patch(night_overlay)
            agents_in_any_fire = set()
            for fire in active_fires:
                for a in agents:
                    if a.distance_to(fire['position']) <= fire['radius']:
                        agents_in_any_fire.add(a.id)
            title += f" | ☾ LUNAR NIGHT"

        # Solar flare overlay — layered on top of the existing day/night
        # background WITHOUT replacing it. active_flare comes from
        # simulation.py (self.active_flare); a flare can strike in daylight or
        # during lunar night, so this is an additive blue wash, drawn just
        # under the night overlay (zorder 4 vs 5) so that when both are active
        # the night dimming still reads on top.
        if active_flare:
            flare_overlay = patches.Rectangle(
                (-self.half_space_size, -self.half_space_size),
                self.half_space_size * 2,
                self.half_space_size * 2,
                linewidth=0,
                facecolor='#1e90ff',
                alpha=0.22,
                zorder=4
            )
            self.ax.add_patch(flare_overlay)
            flare_name = active_flare.get('name', 'flare') if isinstance(active_flare, dict) else 'flare'
            title += f" | ☀ SOLAR FLARE ({flare_name})"
        self.ax.set_title(title, fontsize=11, fontweight='bold', color='lightgray')

        # Legend: Lumis style
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='H', color='w', markerfacecolor='#7fdfff', markersize=12, label='Large Lumis (surface)'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#7fdfff', markersize=8, label='Small Lumis (surface)'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#00ffff', markersize=8, label='In base'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#ffffff', markersize=8, label='Sheltering'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#ffd700', markersize=8, label='Resting (photosynthesis)'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#ff1493', markersize=8, label='Clone parent'),
            
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#6600cc', markersize=8, label='Sexual parent'),
            
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#ffd6e0', markersize=8, label='Newborn (clone)'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#e8c8ff', markersize=8, label='Newborn (two-parent)'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#aaff00', markersize=8, label='Low energy'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#ff4444', markersize=8, label='Critical energy'),
            Line2D([0], [0], color='#00ffaa', linewidth=2, alpha=0.6, label='Familiarity bond'),
        ]
        if active_fires:
            legend_elements.append(
                Line2D([0], [0], color='#000033', linewidth=8,
                       alpha=0.6, label='Lunar Night')
            )
        if active_flare:
            legend_elements.append(
                Line2D([0], [0], color='#1e90ff', linewidth=8,
                       alpha=0.6, label='Solar Flare')
            )
        for handle in self.ax.get_legend_handles_labels()[0]:
            legend_elements.append(handle)
        legend = self.ax.legend(handles=legend_elements, loc='upper right', fontsize=8,
                                facecolor='#1a1a2e', labelcolor='lightgray', edgecolor='gray')

        # Add fire intensity colorbar on the right side (always 0-1 range, shown from step 0)
        # Use make_axes_locatable to match colorbar height exactly to the plot's y-axis
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        fire_cmap = matplotlib.colormaps['YlOrRd']
        norm = mcolors.Normalize(vmin=0.0, vmax=1.0)
        sm = plt.cm.ScalarMappable(cmap=fire_cmap, norm=norm)
        sm.set_array([])
        divider = make_axes_locatable(self.ax)
        cax = divider.append_axes("right", size="3%", pad=0.1)
        cbar = self.fig.colorbar(sm, cax=cax)
        cbar.set_label('Lunar Night Intensity', fontsize=10, color='lightgray')
        cbar.ax.yaxis.set_tick_params(color='lightgray')
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color='lightgray')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=DPI, bbox_inches='tight')
            # Close figure after saving to prevent memory leak
            plt.close(self.fig)
            self.fig = None
            self.ax = None
        else:
            self._display_interactive(step)
    
    def _display_interactive(self, step: int):
        """Display visualization interactively"""
        backend = matplotlib.get_backend()
        is_gui_backend = backend.lower() not in NON_GUI_BACKENDS
        
        if is_gui_backend:
            # Use interactive mode for GUI backends
            plt.ion()  # Turn on interactive mode (allows non-blocking display)
            
            if not self.figure_initialized:
                # First time: create and show window
                plt.show(block=False)
                time.sleep(INITIAL_WINDOW_DELAY)
                logger.info(f"Created visualization window for step {step}")
                self.figure_initialized = True
            else:
                # Update existing window
                plt.draw()
                # Force GUI to process events and update display
                if hasattr(self.fig.canvas, 'flush_events'):
                    self.fig.canvas.flush_events()
            
            # Small pause to ensure window is updated
            plt.pause(VISUALIZATION_PAUSE)
            logger.debug(f"Updated visualization for step {step}")
        else:
            # Non-GUI backend (WSL, headless): just draw without showing
            plt.draw()
            logger.debug(f"Drew visualization for step {step} (non-GUI backend: {backend})")
            logger.warning("GUI backend not available. Use --save-frames to save visualization images.")
    
    def plot_statistics(
        self,
        stats: Dict,
        save_path: Optional[str] = None,
        occupancy_threshold: float = DEFAULT_OCCUPANCY_THRESHOLD,
        agent_threshold: int = DEFAULT_AGENT_THRESHOLD,
        fire_states: Optional[List[Dict]] = None
    ):
        """Plot simulation statistics"""
        # Determine number of subplots based on number of places
        num_places = len(self.places) if hasattr(self, 'places') else 1
        has_fire = 'agents_in_fire_radius' in stats and any(v > 0 for v in stats['agents_in_fire_radius'])
        num_plots = 2 + num_places + (1 if has_fire else 0)
        
        fig, axes = plt.subplots(num_plots, 1, figsize=STATS_FIGURE_SIZE)
        if num_plots == 1:
            axes = [axes]
        
        plot_idx = 0
        
        # Plot overall place occupancy over time
        if 'place_occupancy' in stats and stats['place_occupancy']:
            steps = range(len(stats['place_occupancy']))
            axes[plot_idx].plot(steps, stats['place_occupancy'], 'b-', alpha=0.7, label='Overall Occupancy Rate')
            axes[plot_idx].set_xlabel('Step')
            axes[plot_idx].set_ylabel('Place Occupancy Rate')
            axes[plot_idx].set_title('Overall Place Occupancy Over Time')
            axes[plot_idx].legend()
            axes[plot_idx].grid(True, alpha=0.3)
            axes[plot_idx].set_ylim(0, 1)
            plot_idx += 1
        
        # Plot overall number of agents in places over time
        if 'agents_in_place' in stats and stats['agents_in_place']:
            steps = range(len(stats['agents_in_place']))
            axes[plot_idx].plot(steps, stats['agents_in_place'], 'g-', alpha=0.7, label='Total Agents in Places')
            axes[plot_idx].set_xlabel('Step')
            axes[plot_idx].set_ylabel('Number of Agents')
            axes[plot_idx].set_title('Total Number of Agents in Places Over Time')
            axes[plot_idx].legend()
            axes[plot_idx].grid(True, alpha=0.3)
            max_agents = max(stats['agents_in_place']) if stats['agents_in_place'] else MAX_AGENTS_DISPLAY
            axes[plot_idx].set_ylim(0, max(MAX_AGENTS_DISPLAY, max_agents + 2))
            plot_idx += 1
        
        # Plot per-place statistics
        if 'places' in stats:
            place_colors = ['red', 'orange', 'green', 'purple', 'brown']
            for i, place in enumerate(self.places):
                place_name = place['name']
                if place_name in stats['places']:
                    place_stats = stats['places'][place_name]

                    # Occupancy rate stays on the left axis (0-1 range).
                    # Agent count previously shared this same axis and its
                    # ylim(0,1) — with run 010 peaking at 92 agents, that line
                    # was clipped flat at y=1 and effectively invisible. Given
                    # its own right-hand axis instead.
                    ax_left = axes[plot_idx]
                    ax_left.set_ylim(0, 1)
                    ax_right = ax_left.twinx()

                    # Plot occupancy
                    if place_stats['occupancy']:
                        steps = range(len(place_stats['occupancy']))
                        color = place_colors[i % len(place_colors)]
                        ax_left.plot(
                            steps, place_stats['occupancy'],
                            color=color, alpha=0.7,
                            label=f'{place_name} Occupancy'
                        )

                    if place_stats['agents_in_place']:
                        steps = range(len(place_stats['agents_in_place']))
                        color = place_colors[i % len(place_colors)]
                        ax_right.plot(
                            steps, place_stats['agents_in_place'],
                            color=color, alpha=0.5, linestyle=':',
                            label=f'{place_name} Agents'
                        )

                    ax_left.set_xlabel('Step')
                    ax_left.set_ylabel('Occupancy Rate (0-1)')
                    ax_right.set_ylabel('Agents in Place (count)')
                    ax_left.set_title(f'{place_name} Statistics Over Time')
                    lines_left, labels_left = ax_left.get_legend_handles_labels()
                    lines_right, labels_right = ax_right.get_legend_handles_labels()
                    ax_left.legend(lines_left + lines_right, labels_left + labels_right)
                    ax_left.grid(True, alpha=0.3)
                    plot_idx += 1

        # Plot fire statistics
        if has_fire:
            steps = range(len(stats['agents_in_fire_radius']))
            axes[plot_idx].plot(
                steps, stats['agents_in_fire_radius'],
                'r-', alpha=0.7, label='Agents in fire radius'
            )
            if fire_states:
                for fire in fire_states:
                    if 'start_step' in fire:
                        fire_start_idx = fire['start_step'] - 1
                        fire_name = fire.get('name', 'Fire')
                        axes[plot_idx].axvline(
                            x=fire_start_idx, color='red', linestyle='--',
                            alpha=0.5, label=f'{fire_name} start'
                        )
            axes[plot_idx].set_xlabel('Step')
            axes[plot_idx].set_ylabel('Number of Agents')
            axes[plot_idx].set_title('Agents Within Fire Radius Over Time')
            axes[plot_idx].legend()
            axes[plot_idx].grid(True, alpha=0.3)
            max_fire = max(stats['agents_in_fire_radius']) if stats['agents_in_fire_radius'] else MAX_AGENTS_DISPLAY
            axes[plot_idx].set_ylim(0, max(MAX_AGENTS_DISPLAY, max_fire + 2))
            plot_idx += 1

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=DPI, bbox_inches='tight')
            plt.close(fig)
        else:
            # Check if we have a GUI backend
            backend = matplotlib.get_backend()
            is_gui_backend = backend.lower() not in NON_GUI_BACKENDS
            
            if is_gui_backend:
                # Use non-blocking show for GUI backends
                plt.show(block=False)
                plt.pause(STATS_PAUSE)
            else:
                # Non-GUI backend: just draw without showing, then close
                plt.draw()
                plt.close(fig)
                logger.warning("GUI backend not available. Statistics plot not displayed. Use --save-frames to save.")