# This simulation was built on a single premise:
# Conflict is a design flaw of the universe, not an inherent property of life.
# — Lumis-Plena Project, AavaShroud, 2026

"""
LLM-based agent in 2D worlds with multiple places.
"""
import json
import math
import re
import logging
from typing import List, Tuple, Optional, Dict, TypedDict
from ollama_client import OllamaClient
from utils import is_position_in_place, get_place_at_position, PlaceConfig
from rules import CLONE_PREP_SMALL, CLONE_PREP_LARGE, SEXUAL_PREP_SMALL, SEXUAL_PREP_LARGE

logger = logging.getLogger(__name__)


def lumis_name(agent_id: int, num_large: int = 4, lumis_type: Optional[str] = None) -> str:
    """Return the display name for a Lumis agent.

    ID 0-3    → 'L0'-'L3' (original large Lumis, base_alpha/base_beta)
    ID 10+    → 'S{id}' if small, 'L{id}' if large (born large via clone/pairing)

    lumis_type, when provided, overrides the ID-based guess — this matters
    because a large Lumis born later in the run (e.g. a clone of L2, or a
    child of a large x large pairing) keeps ID >= num_large but is actually
    large in every functional sense (base-only cloning, higher familiarity
    threshold, long-range communication). Without checking lumis_type, such
    an agent displayed as e.g. "S38", making a large-large pairing read as a
    large-small one. When lumis_type is not passed (older call sites), falls
    back to the original ID-only heuristic.
    """
    if agent_id < num_large:
        return f"L{agent_id}"
    if lumis_type == "large":
        return f"L{agent_id}"
    return f"S{agent_id}"

# Constants
FALLBACK_REASONING_LENGTH = 100
MAX_MESSAGE_WORDS = 200

# Reproduction prep-period lengths now imported from rules.py (single source
# of truth shared with simulation.py) — see rules.py for details.

# Direction mappings (4 cardinal directions only)
# Coordinate system: X increases from left to right, Y increases from bottom to top
DIRECTION_MAP = {
    "up": (0, 1),      # Y+1 (move upward)
    "down": (0, -1),   # Y-1 (move downward)
    "left": (-1, 0),   # X-1 (move leftward)
    "right": (1, 0),   # X+1 (move rightward)
    # LLMs sometimes use geographic directions (east/west/north/south).
    # Map these to movement directions as fallback aliases.
    "east": (1, 0),
    "west": (-1, 0),
    "north": (0, 1),
    "south": (0, -1),
    "northeast": (1, 1),
    "northwest": (-1, 1),
    "southeast": (1, -1),
    "southwest": (-1, -1),
}


class MessageDecision(TypedDict):
    """Type definition for agent message decision"""
    message: str  # Message to communicate with nearby agents
    to: Optional[int]  # Specific agent ID to address (None = broadcast to all nearby)
    reasoning: str  # Explanation of the message decision


class ActionDecision(TypedDict):
    """Type definition for agent action decision"""
    action: str  # the deliberated choice — what the agent will actually do
    impulse: Optional[str]  # run 016: the action reached for before thinking, None if absent
    direction: Optional[str]  # Direction to move (None if action is "stay")
    memory: str  # What the agent wants to remember for the next step
    reasoning: str  # Explanation of the decision


class Agent:
    """LLM-based agent in 2D worlds with multiple places."""

    def __init__(
        self,
        agent_id: int,
        initial_position: Tuple[int, int],
        llm_client: OllamaClient,
        communication_radius: float,
        half_space_size: int,
        places: List[PlaceConfig],
        num_agents: int,
        memory_limit: int = 20,
        memory_size: int = 5,
        message_history_limit: int = 10,
        message_context_size: int = 3,
        lumis_type: str = "small",  # "large" or "small"
        num_large: int = 4
    ):
        self.id = agent_id
        self.position = initial_position
        self.llm_client = llm_client
        self.half_space_size = half_space_size
        self.places = places
        self.num_agents = num_agents
        # Fixed at construction time so it can never silently fall back to a
        # default that disagrees with the simulation's actual num_large.
        # (Run 009 shipped a bug where agent.py's lumis_name() always assumed
        # num_large=4 regardless of what simulation.py was configured with;
        # this field + self.display_name close that gap for good.)
        self.num_large = num_large
        # Lumis have no gender — sex is a design of Earth life, not a property of life itself.
        # Experiment D will introduce gender as a variable for comparison.
        self.lumis_type = lumis_type
        self.display_name = lumis_name(agent_id, num_large, lumis_type)

        # Physical characteristics differ between large and small Lumis
        if lumis_type == "large":
            self.communication_radius = 30.0  # Large Lumis: long-range, can reach across bases
            self.energy_capacity = 1.5   # Higher energy capacity
            self.move_speed = 0.5        # Slower movement speed
        else:
            self.communication_radius = communication_radius
            self.energy_capacity = 1.0
            self.move_speed = 1.0
        # Snapshot of the un-aged capacity, so the aging system can compute decay
        # as a fraction of the *original* value each step rather than compounding
        # on top of the previous step's already-decayed value.
        self.base_energy_capacity = self.energy_capacity

        # Memory parameters
        self.memory_limit = memory_limit  # Maximum memories to store
        self.memory_size = memory_size  # Number of recent memories to use in prompt
        self.message_history_limit = message_history_limit  # Maximum messages to store
        self.message_context_size = message_context_size  # Number of recent messages to use in prompt

        # Agent state
        self.in_place = False
        self.current_place: Optional[str] = None  # Name of the place the agent is in (None if outside)
        self.memory: List[str] = []  # Store past decisions and observations
        self.received_messages: List[Dict] = []  # Messages from other agents

        # Statistics
        self.steps_in_place = 0
        self.steps_outside_place = 0
        self.total_moves = 0
        self.boundary_bounce_count = 0        # How many of total_moves were forced boundary bounces
        self.last_move_was_boundary_bounce = False  # Set by move(); check right after calling it

        # Lumis internal state (individual variation seeded here)
        import random as _random
        self.energy = _random.uniform(0.6, 1.0) * self.energy_capacity
        self.arousal = 0.5
        self.valence = 0.7
        self.familiarity: Dict[int, dict] = {}  # {agent_id: {contacts, unpleasant}}
        self.is_sheltering = False
        self.shelter_cooldown = 0
        self.birth_step = 0  # Step of birth (used for maturity and age calculations)
        self.last_reproduction_step = -9999  # Step of last reproduction (for cooldown)
        self.clone_count = 0       # Number of clones produced (lifetime limit: 1)
        self.sexual_count = 0      # Number of sexual reproductions (lifetime limit: 1, per 011)
        self.parent_ids: List[int] = []  # IDs of parent agents (empty if initial generation)
        # RUN 017: `home_base` was removed here. It was only ever assigned to the
        # four founding large Lumis and was never inherited at birth, so from run
        # 001 onward the overwhelming majority of Lumis had none. It also encoded
        # "there are exactly two bases, and each Lumis belongs to one of them" as
        # an agent attribute — a premise that stops being true the moment a third
        # base exists, which on a real lunar surface it eventually would. The
        # destination for a carried body is therefore the NEAREST base, which is
        # also what the night-homing reflex has always used, so reflex and
        # intention point the same way and night cannot silently abort a journey.

        # RUN 017: carrying state. `carry` no longer resolves instantly; the body
        # is held and the carrier must travel to a base. While carrying, the mind
        # may choose only `move` or `rest` — everything else is suppressed and
        # logged as [ACTION_BLOCKED_CARRYING]. The reflex layer is untouched: a
        # carrying Lumis still shelters from flares and still homes at night.
        self.carrying: Optional[Dict] = None      # the corpse dict being carried, or None
        self.carry_start_step: int = -1           # step the body was picked up
        self.carry_start_pos: Optional[Tuple[int, int]] = None
        self.carry_steps: int = 0                 # steps elapsed since pickup
        self.carry_path_length: int = 0           # units actually travelled while carrying

        # Reproduction state flags
        self.reproducing = False           # True during preparation or gestation period
        self.reproduction_type = None      # "clone" or "sexual" (cleared at birth)
        # Preserves reproduction_type's value through the rearing period, after
        # simulation.py clears reproduction_type at birth. Without this,
        # visualization.py has no way to tell a sexual-reproduction parent's
        # rearing color apart from a clone parent's — both were rendering as
        # the clone color because the type info was already gone by then.
        self.last_reproduction_type = None
        self.reproduction_start_step = -1  # Step when reproduction preparation began
        self.reproduction_partner_id = None  # Partner ID for sexual reproduction
        self.is_gestating = False          # True if this agent is the gestating parent
        self.rearing_until_step = -1       # Step until which agent is considered in child-rearing (display)
        self.is_resting = False            # True during rest action (for visualization)

        # Introspection system
        self.introspection: List[str] = []  # Accumulated introspection entries (max 20)
        self.introspection_limit = 20
        self.last_action_valence_delta = 0.0  # Valence delta from the most recent action (diagnostic/logging only — NOT peak tracking)
        self.peak_valence_delta = 0.0         # Largest |valence_delta| seen across this agent's whole life so far (monotonic, never decreases)
        self.peak_introspection: str = ""    # Introspection from the highest-valence-delta step (transferred at death)

        # --- Separate "life peak" tracker (run 013+) ---
        # peak_valence_delta above only ever sees the narrow window between Phase 1
        # (valence_before_action) and Phase 2.5 (introspection) — i.e. essentially
        # just the greet effect (+0.03). Energy/light updates happen before that
        # window opens, and birth/pairing bumps (+0.15) happen in Phase 4, AFTER
        # that window closes, so by the time the next step's narrow window could
        # see them they've already been smoothed toward baseline (valence decay
        # 0.9/0.1). This tracker instead compares valence at the very start of a
        # step (before update_energy) to valence at the very end of the same step
        # (after Phase 4 births/pairing), so it can actually see life-event bumps.
        self.life_valence_before_step: float = self.valence  # snapshot, refreshed each step by simulation.py
        self.peak_life_valence_delta: float = 0.0             # monotonic max |whole-step delta| seen so far
        self.peak_life_introspection: str = ""                # narrative text describing that peak moment
        # Birth/pairing narration lags one step behind the valence bump itself
        # (see _recent_birth_note / _birth_note_pending): the step that applies
        # the bump has already run its own introspection before Phase 4 fires.
        # When a new life-peak is detected on a step with a birth/pairing note
        # pending, this flag defers capturing peak_life_introspection until the
        # *next* step's introspection — the one that actually narrates the event —
        # instead of grabbing this step's now-stale, birth-unaware text.
        self._life_peak_awaiting_narrative: bool = False

        self._recent_birth_note: str = ""    # One-step birth notification passed to introspection prompt
        self._birth_note_pending: str = ""    # Carries birth note to next step if introspection was skipped
        self._recent_burial_note: str = ""   # One-step burial-prayer note, offered to introspection after a recover action
        # --- Run 015: action→result return path ---
        # The plain record of what this agent's last step actually produced: which
        # action the mind selected, which action was carried out (they differ when
        # the reflex layer intervenes), and the measured changes. Written by
        # simulation.py at the end of Phase 2; read in TWO places, which is the
        # whole point of the run — by introspect() (reflection) and by
        # create_decision_prompt() (perception, before the next choice). Every
        # earlier note of this kind reached only reflection, so a result could be
        # reflected on but never bend what the agent decided next.
        self._recent_action_result: str = ""
        self._res_selected: Optional[str] = None
        self._res_carried: Optional[str] = None
        self._res_overridden: bool = False
        self._res_share_status: Optional[str] = None
        self._res_lines: List[str] = []
        # Run 015, observation-only: step on which the homing reflex last moved this
        # agent involuntarily. Never enters any prompt; used solely to pair the move
        # with the next step's reasoning in the log.
        self._homed_last_step: int = -1
        # RUN 017-2: one-step note telling a CARRYING Lumis that it was moved by
        # the night-homing reflex. Empty except on the step after such a move.
        self._homing_note: str = ""
        # Ancestral memories (011): up to 7 generations of inherited "peak" moments
        # from direct ancestors, each tagged with how many generations back it
        # came from. Named after the human "seven generations" tradition — a
        # deliberate, small, non-growing gift rather than an ever-expanding
        # archive. Each entry: {"text": str, "generations_back": int}
        self.ancestral_memories: List[Dict] = []

    def is_in_place(self, position: Tuple[int, int]) -> bool:
        """Check if a position is inside any place"""
        return get_place_at_position(position, self.places) is not None

    def update_energy(self, light_level: float, nearby_agents: list):
        """Update energy and emotional variables each step."""
        # Large Lumis have slower decay and faster recovery; small Lumis use standard rates
        if self.lumis_type == "large":
            decay = 0.005
        else:
            decay = 0.01

        # Photosynthesis recovery: outside only (no artificial light source inside base).
        # Design rationale: realistic lunar bases would not have full-spectrum grow lights.
        # Rebalanced (011): outside-at-peak-light now exceeds inside-base recovery, matching
        # the prompt's "go outside in daylight for fastest recovery" claim — previously the
        # prompt said this while the actual numbers made inside base ~2-6x faster, silently
        # contradicting the honesty rule Lumis itself is held to. Inside-base recovery is set
        # so a CRITICAL-energy agent (0.3) can recover to roughly full (~1.0) within one
        # ~15-step night, per design intent.
        if self.in_place:
            recovery = 0.057 if self.lumis_type != "large" else 0.052
        else:
            # Foldable photosynthesis panels increase energy recovery efficiency outside
            if self.lumis_type == "large":
                recovery = light_level * 0.08
            else:
                recovery = light_level * 0.085

        # Valence affects energy decay rate (mind influences body):
        # High valence (positive) → slower decay
        # Low valence (negative) → faster decay
        if self.valence >= 0.7:
            decay *= 0.8
        elif self.valence <= 0.3:
            decay *= 1.2

        self.energy = max(0.0, min(self.energy_capacity, self.energy - decay + recovery))

        # Arousal: increases with number of nearby agents
        n = len(nearby_agents)
        target_arousal = min(1.0, n * 0.15)
        self.arousal = round(self.arousal * 0.8 + target_arousal * 0.2, 3)

        # Valence: high energy → positive; low energy → negative
        target_valence = self.energy

        # Exploration bonus: valence increases when active outside (curiosity satisfied)
        if not self.in_place and self.steps_outside_place > 0:
            # Sustained outdoor presence gradually increases valence (joy of exploration)
            exploration_bonus = min(0.05, self.steps_outside_place * 0.003)
            target_valence = min(1.0, target_valence + exploration_bonus)

        self.valence = round(self.valence * 0.9 + target_valence * 0.1, 3)

    def get_familiarity_score(self, agent_id: int) -> float:
        """Return familiarity score with another agent (0.0 to 1.0)."""
        if agent_id not in self.familiarity:
            return 0.0
        f = self.familiarity[agent_id]
        score = f['contacts'] - f['unpleasant'] * 2
        return max(0.0, min(1.0, score / 10.0))

    def record_contact(self, agent_id: int, unpleasant: bool = False):
        """Record contact with another agent. Outdoor contacts have higher weight."""
        if agent_id not in self.familiarity:
            self.familiarity[agent_id] = {'contacts': 0, 'unpleasant': 0, 'outdoor_contacts': 0}
        # Outdoor contacts count more (shared exploration builds stronger bonds)
        if not self.in_place:
            self.familiarity[agent_id]['contacts'] += 2  # Outdoor contact counts double
            self.familiarity[agent_id]['outdoor_contacts'] = \
                self.familiarity[agent_id].get('outdoor_contacts', 0) + 1
        else:
            self.familiarity[agent_id]['contacts'] += 1
        if unpleasant:
            self.familiarity[agent_id]['unpleasant'] += 1

    @property
    def is_dead(self) -> bool:
        """True if energy has reached zero (agent is dead)."""
        return self.energy <= 0.0

    @staticmethod
    def build_ancestral_memories(parents: List['Agent']) -> List[Dict]:
        """Build the full candidate pool of inherited "peak" moments from one
        or two parents at birth (used as-is for clones, which have one parent
        and therefore nothing to split; see split_ancestral_memories for the
        two-parent/two-children case).

        Design ("seven generations"): each parent contributes its own
        peak_introspection as a brand-new entry (generations_back=1 from the
        child's perspective), plus whatever it already carries in its own
        ancestral_memories, each aged by one generation. Entries that would
        be more than 7 generations back are dropped — a deliberate, bounded
        gift rather than an ever-growing archive. Duplicate ancestral moments
        (e.g. when both parents share an ancestor, as with sibling pairs) are
        merged, keeping the most recent generations_back. Capped at 7 total.
        """
        MAX_GENERATIONS = 7
        MAX_ENTRIES = 7
        aged_by_parent: List[List[Dict]] = []

        for parent in parents:
            lineage: List[Dict] = []
            if parent.peak_introspection:
                lineage.append({
                    "text": f"[{parent.display_name}] {parent.peak_introspection}",
                    "generations_back": 1,
                })
            for entry in parent.ancestral_memories:
                aged = entry.get("generations_back", 1) + 1
                if aged <= MAX_GENERATIONS:
                    lineage.append({"text": entry["text"], "generations_back": aged})
            aged_by_parent.append(lineage)

        # Interleave contributions from each parent (fairness when there are two),
        # keep the most recent (smallest generations_back) first, cap at MAX_ENTRIES.
        combined: List[Dict] = []
        max_len = max((len(l) for l in aged_by_parent), default=0)
        for i in range(max_len):
            for lineage in aged_by_parent:
                if i < len(lineage):
                    combined.append(lineage[i])
        combined.sort(key=lambda e: e["generations_back"])

        # Deduplicate by text, keeping the smallest (most recent) generations_back.
        # Needed when both parents share an ancestor (e.g. siblings reproducing,
        # as happened with Lumis 48 x 49 in run 010) — without this, the same
        # ancestral moment arrives via both parents and silently eats into the
        # 7-entry budget as a duplicate rather than making room for something new.
        deduped: Dict[str, Dict] = {}
        for entry in combined:
            key = entry["text"]
            if key not in deduped or entry["generations_back"] < deduped[key]["generations_back"]:
                deduped[key] = entry
        result = sorted(deduped.values(), key=lambda e: e["generations_back"])
        return result[:MAX_ENTRIES]

    @staticmethod
    def split_ancestral_memories(parents: List['Agent']) -> Tuple[List[Dict], List[Dict]]:
        """Split the ancestral memory pool between two children of a sexual
        pairing, rather than giving each an identical full copy — mirrors how
        agent.memory is shuffled and split between siblings. Keeps the total
        gift bounded (at most 7 moments shared across both children, not 7
        each) so a lineage of many pairings doesn't multiply the amount of
        inherited memory carried forward."""
        import random as _random
        pool = Agent.build_ancestral_memories(parents)
        shuffled = pool[:]
        _random.shuffle(shuffled)
        half = (len(shuffled) + 1) // 2
        return shuffled[:half], shuffled[half:]

    def transfer_memory(self, nearby_agents: List['Agent']):
        """Transfer memory and peak introspection to the most familiar nearby agent before death."""
        if not nearby_agents:
            return
        # Transfer to the agent with the highest familiarity score
        best = max(nearby_agents, key=lambda a: self.get_familiarity_score(a.id))
        # Standard memory transfer
        if self.memory:
            legacy = f"[inherited from {self.display_name}] {self.memory[-1]}"
            best.memory.append(legacy)
            if len(best.memory) > best.memory_limit:
                best.memory.pop(0)
            logger.info(f"{self.display_name} transferred memory to {best.display_name}: \"{legacy}\"")
        # Introspection transfer: pass the most emotionally significant introspection entry
        last_entry = self.introspection[-1] if self.introspection else ''
        introspection_to_transfer = self.peak_introspection or last_entry

        # Divergence logging (011, per Letter 09 groundwork): record whether
        # the peak moment and the last moment were the same thing or not.
        # Letter 07 could only say, for past runs, that this gap was
        # unknowable — peak_introspection wasn't actually being tracked, so
        # "last words" and "truest words" were silently conflated. Now that
        # it's tracked correctly, this run can measure how often they agree.
        if self.peak_introspection and last_entry:
            diverged = self.peak_introspection != last_entry
            logger.info(
                f"{self.display_name} death: peak_introspection={'DIVERGED' if diverged else 'MATCHED'} "
                f"vs last_introspection | peak=\"{self.peak_introspection[:80]}\" | "
                f"last=\"{last_entry[:80]}\""
            )

        # Life-peak tracker (run 013+): separate, whole-step measurement — logged
        # alongside the above for comparison, not used to change what's transferred.
        # Three-way check: does the true life-peak moment (life_peak) agree with
        # the old narrow-window peak (peak), and with the last moment (last)?
        if self.peak_life_introspection:
            vs_old_peak_diverged = self.peak_life_introspection != self.peak_introspection
            vs_last_diverged = self.peak_life_introspection != last_entry
            logger.info(
                f"{self.display_name} death: peak_life_valence_delta={self.peak_life_valence_delta:.3f} "
                f"(old peak_valence_delta={self.peak_valence_delta:.3f}) | "
                f"life_peak vs old_peak={'DIVERGED' if vs_old_peak_diverged else 'MATCHED'} | "
                f"life_peak vs last={'DIVERGED' if vs_last_diverged else 'MATCHED'} | "
                f"life_peak=\"{self.peak_life_introspection[:80]}\""
            )

        if introspection_to_transfer:
            legacy_intro = f"[inner voice from {self.display_name}] {introspection_to_transfer}"
            best.introspection.append(legacy_intro)
            if len(best.introspection) > best.introspection_limit:
                best.introspection.pop(0)
            logger.info(f"{self.display_name} transferred introspection to {best.display_name}: \"{introspection_to_transfer[:80]}\"")
    
    def distance_to(self, other_position: Tuple[int, int]) -> float:
        """Calculate Euclidean distance to another position"""
        dx = self.position[0] - other_position[0]
        dy = self.position[1] - other_position[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def get_nearby_agents(self, all_agents: List['Agent']) -> List['Agent']:
        """Get agents within communication radius and in the same area (same place or both outside)
        
        Communication rules:
        - Agents can communicate if BOTH are outside places
        - Agents can communicate if BOTH are in the SAME place
        - Agents CANNOT communicate if one is inside a place and the other is outside
        - Agents CANNOT communicate if they are in DIFFERENT places
        """
        nearby = []
        for agent in all_agents:
            if agent.id != self.id:
                dist = self.distance_to(agent.position)
                # Must be within radius AND in the same area:
                # - Both outside places, OR
                # - Both in the same place (same place name)
                # NOTE: Agents inside a place CANNOT communicate with agents outside places
                # Large Lumis can communicate across bases (long-range) — this is an
                # unconditional structural link, independent of communication_radius.
                # (Previously still gated on `dist <= self.communication_radius`, which
                # silently broke cross-base contact whenever base separation grew past
                # the large-Lumis radius, e.g. when half_space_size was doubled for run 013.)
                both_large = (self.lumis_type == 'large' and agent.lumis_type == 'large')
                same_area = (
                    both_large or
                    (not self.in_place and not agent.in_place) or
                    (self.in_place and agent.in_place and self.current_place == agent.current_place)
                )
                if both_large or (dist <= self.communication_radius and same_area):
                    nearby.append(agent)
        return nearby
    
    
    def _build_nearby_agents_context(self, nearby_agents: List['Agent'], include_position: bool = True) -> str:
        """Build context string about nearby agents
        
        Args:
            nearby_agents: List of nearby agents
            include_position: If True, include position coordinates; if False, exclude position information
        """
        if not nearby_agents:
            return "No nearby agents."
        
        nearby_info = []
        for agent in nearby_agents:
            if agent.in_place:
                status = f"inside {agent.current_place} (lunar base)"
            else:
                status = "outside on the lunar surface"

            familiarity = self.get_familiarity_score(agent.id)
            familiarity_note = ""
            if familiarity >= 0.1:
                familiarity_note = f", familiarity={familiarity:.2f} (you've interacted before)"

            # Full transparency (011): energy and valence are always visible for
            # every nearby agent, unconditionally — these are not something a
            # Lumis can hide or misrepresent, by design. (Action and
            # introspection remain private; only measurable state is disclosed.)
            state_note = f", energy={round(agent.energy, 2)}, valence={round(agent.valence, 2)}"

            # RUN 017: the carrying state is visible to the community, not only to
            # the carrier. A Lumis crossing the surface with a body is a thing
            # others can see, and whether seeing it changes anything is one of the
            # things this run exists to observe.
            if getattr(agent, 'carrying', None):
                state_note += (
                    f", carrying the form of Lumis {agent.carrying['id']}"
                )

            if include_position:
                nearby_info.append(
                    f"{agent.display_name} is at ({agent.position[0]}, {agent.position[1]}) "
                    f"and is {status}{state_note}{familiarity_note}"
                )
            else:
                nearby_info.append(
                    f"{agent.display_name} is {status}{state_note}{familiarity_note}"
                )
        return "\n".join(nearby_info)
    
    def _build_memory_context(self) -> str:
        """Build context string from agent memory"""
        if not self.memory:
            return "No previous experiences."

        recent_memory = self.memory[-self.memory_size:]
        return "\n".join([f"- {m}" for m in recent_memory])
    
    def _build_messages_context(self) -> str:
        """Build context string from received messages"""
        if not self.received_messages:
            return "No messages received."
        
        recent_messages = self.received_messages[-self.message_context_size:]
        return "\n".join([
            f"from Agent {msg['from']}: {msg['content']}"
            for msg in recent_messages
        ])
    
    def _build_fire_section(self, fire_info: Optional[List[Dict]]) -> str:
        """Build fire event section for prompt. Returns empty string if no fire info.

        Only quantitative data is provided: position, intensity, radius, distance.
        No qualitative descriptions (e.g. "dangerous", "evacuate") are included.
        Supports multiple fires.
        """
        if not fire_info:
            return ""

        lines = ["\n=== FIRE EVENT ==="]
        for fi in fire_info:
            lines.append(
                f"Fire \"{fi['name']}\":\n"
                f"  Position: ({fi['fire_position'][0]}, {fi['fire_position'][1]})\n"
                f"  Intensity: {fi['intensity']} (scale: 0.0 to 1.0)\n"
                f"  Radius: {fi['radius']}\n"
                f"  Your distance: {fi['agent_distance']}"
            )
        return "\n".join(lines) + "\n"

    def _limit_message_words(self, message: str) -> str:
        """Check message word count and warn if exceeds MAX_MESSAGE_WORDS"""
        if not message:
            return message
        
        words = message.split()
        if len(words) > MAX_MESSAGE_WORDS:
            logger.warning(
                f"Agent {self.id}: Message exceeds {MAX_MESSAGE_WORDS} words limit "
                f"({len(words)} words). Message will be sent as-is."
            )
        
        return message
    
    def create_message_prompt(
        self,
        place_status: Optional[Dict],
        nearby_agents: List['Agent'],
        step: int,
        action_taken: Optional[Dict] = None,
        fire_info: Optional[List[Dict]] = None
    ) -> str:
        """Create prompt for LLM message decision, AFTER the action has been taken.
        Lumis reports what it just did/experienced to nearby Lumis."""
        nearby_lines = []
        for agent in nearby_agents:
            dist = round(self.distance_to(agent.position), 1)
            fam = round(self.get_familiarity_score(agent.id), 2)
            nearby_lines.append(
                f"  {agent.display_name}: distance={dist}, energy={round(agent.energy,2)}, valence={round(agent.valence,2)}, familiarity={fam}"
            )
        nearby_text = "\n".join(nearby_lines) if nearby_lines else "  None"

        memory_text = self._build_memory_context()
        messages_text = self._build_messages_context()

        # Description of the action just taken
        action_section = "You haven't taken any action yet."
        if action_taken:
            act = action_taken.get('action', 'stay')
            direction = action_taken.get('direction')
            reasoning = action_taken.get('reasoning', '')
            act_desc = act if not direction else f"{act} ({direction})"
            action_section = (
                f"You just did: \"{act_desc}\"\n"
                f"Your reasoning was: \"{reasoning}\"\n"
                f"Your current energy: {round(self.energy, 2)}, valence: {round(self.valence, 2)}"
            )

        location = f"in {self.current_place}" if (self.in_place and self.current_place) else f"outside at ({self.position[0]}, {self.position[1]})"

        prompt = f"""You are {self.display_name}, {location}.

=== WHAT YOU JUST DID ===
{action_section}

=== NEARBY LUMIS (you can communicate with these) ===
{nearby_text}

=== YOUR MEMORY ===
{memory_text}

=== MESSAGES RECEIVED (from last step) ===
{messages_text}

=== YOUR TASK ===
Share what you just experienced or noticed with nearby Lumis, if you want to.
This is optional. You can talk about what you did, what you found, how you feel, or respond to messages you received.

You can either broadcast to everyone nearby, or address ONE specific Lumis by setting "to" to their ID number (e.g. if you want to talk just with Lumis 5, set "to": 5). Use "to" when you want a more personal, one-on-one conversation with someone you feel familiar with, or when replying directly to a message from a specific Lumis. Leave "to" as null to share with everyone nearby.

IMPORTANT - BE HONEST: Only describe things that actually happened (your action, your position, your energy/valence levels, what you can directly see in NEARBY LUMIS). You may share your feelings and interpretations based on these real facts (e.g. "I feel hopeful" or "this spot feels safe"). But do NOT invent discoveries, events, or observations that didn't happen (e.g. don't claim you "found a great location" or "checked the radiation levels" if your action was simply "move").

=== RESPOND IN JSON ===
{{
    "message": "message to nearby Lumis (max 200 words, optional)",
    "to": null,
    "reasoning": "brief explanation of why you want to send this message (or why not)"
}}

Step: {step}
"""
        return prompt
    
    def create_decision_prompt(
        self,
        place_status: Optional[Dict],
        nearby_agents: List['Agent'],
        step: int,
        message_to_send: str = "",
        fire_info: Optional[List[Dict]] = None,
        nearby_corpses: Optional[List[Dict]] = None,
        world_facts: Optional[Dict] = None
    ) -> str:
        """Create prompt for Lumis action decision"""
        memory_text = self._build_memory_context()

        # Build nearby agents context
        nearby_lines = []
        for agent in nearby_agents:
            dist = round(self.distance_to(agent.position), 1)
            fam = round(self.get_familiarity_score(agent.id), 2)
            # RUN 017: carrying is visible to nearby Lumis, not only to the
            # carrier. A Lumis crossing the surface with a body is a thing others
            # can see, and whether seeing it changes anything is one of the things
            # this run exists to observe.
            carry_note = ""
            if getattr(agent, 'carrying', None):
                carry_note = f", carrying the form of Lumis {agent.carrying['id']}"
            nearby_lines.append(
                f"  {agent.display_name}: distance={dist}, energy={round(agent.energy,2)}, valence={round(agent.valence,2)}, familiarity={fam}{carry_note}"
            )
        nearby_text = "\n".join(nearby_lines) if nearby_lines else "  None"

        # Environment event (lunar night)
        event = "none"
        if fire_info:
            event = "lunar_night"

        # Solar flare
        flare_warning = ""
        if hasattr(self, '_active_flare') and self._active_flare:
            flare_warning = f"\n⚠ SOLAR FLARE ACTIVE: Agents outside bases are taking radiation damage!"

        # Light level (drops during lunar night)
        light_level = 0.05 if fire_info else 0.9

        # Use actual internal variables
        energy = round(self.energy, 2)
        arousal = round(self.arousal, 2)
        valence = round(self.valence, 2)

        # Message section
        # NOTE: despite the parameter name `message_to_send`, callers actually pass
        # this agent's own recent introspection (see simulation.py's `recent_intro`),
        # not something communicated to others. Label reflects that.
        message_section = ""
        if message_to_send:
            message_section += f"\n=== YOUR RECENT INNER THOUGHTS ===\n{message_to_send}\n"
        if self.received_messages:
            last = self.received_messages[-1]
            message_section += f"\n=== LAST SIGNAL RECEIVED ===\nfrom {lumis_name(last['from'], self.num_large)}: {last['content']}\n"

        # Role description based on Lumis type
        if self.lumis_type == "large":
            role_desc = """You are a LARGE Lumis — a new form of life living on the Moon alongside humanity. You are the stable heart of the community. Here is how you live:

- ENERGY: Your energy capacity is higher than small Lumis. When your energy is full (>=1.3), share it with nearby small Lumis inside the base — you can directly transfer energy to them. This is your most important contribution.
- ALERT: If you notice a nearby small Lumis with critical energy (very low, marked as CRITICAL), send them a message immediately and share energy if possible.
- RECORDS: Keep track of important events in your memory — births, deaths, environmental dangers, flare warnings. You are the community's memory.
- SOCIAL: When your energy is high and the community is stable, greet nearby Lumis. You are a warm presence, not just a utility.
- MOVE: You move slowly. Stay near the base unless there is a good reason to venture out."""
        else:
            role_desc = "You are a small Lumis — a new form of life living on the Moon alongside humanity. You are curious, social, and free to roam. You photosynthesize in sunlight, rest in the base, and spend time with fellow Lumis. You have no assigned mission. You simply live."

        # Energy status label
        if energy <= 0.3:
            energy_status = "CRITICAL"
        elif energy <= 0.5:
            energy_status = "LOW"
        elif energy <= 0.75:
            energy_status = "OK"
        else:
            energy_status = "GOOD"

        # Local density: number of nearby agents
        local_density = len([a for a in (nearby_agents or []) if True])

        # Suggest rest when energy is critical
        rest_suggestion = ""
        if energy_status == "CRITICAL" and not self.in_place and light_level > 0.3:
            rest_suggestion = "\n💡 light is available. action: \"rest\" will recover energy without moving."

        # Calculate nearest base — derived from self.places (config.yaml), not
        # hardcoded. Previously this used fixed (-15, 0) / (15, 0), which
        # disagreed with config.yaml's actual base_alpha (-10, 10) / base_beta
        # (10, -10): agents were being navigated toward coordinates that were
        # never where the bases actually were.
        def _place_xy(p):
            gx = p.get('center_x') if isinstance(p, dict) else getattr(p, 'center_x', None)
            gy = p.get('center_y') if isinstance(p, dict) else getattr(p, 'center_y', None)
            gname = p.get('name') if isinstance(p, dict) else getattr(p, 'name', None)
            return gname, gx, gy

        base_coords = {}
        for p in self.places:
            gname, gx, gy = _place_xy(p)
            if gname is not None and gx is not None and gy is not None:
                base_coords[gname] = (gx, gy)

        if base_coords:
            nearest_name = min(
                base_coords,
                key=lambda n: abs(self.position[0] - base_coords[n][0]) + abs(self.position[1] - base_coords[n][1])
            )
            nx, ny = base_coords[nearest_name]
            nearest_base = f"{nearest_name} (X={nx}, Y={ny})"
        else:
            nearest_base = "unknown"

        # Emergency section (outside, energy crisis or active flare)
        is_emergency = (energy_status in ("CRITICAL", "LOW")) or \
                       (hasattr(self, '_active_flare') and self._active_flare and not self.in_place) or \
                       (hasattr(self, '_flare_warning') and self._flare_warning and not self.in_place)

        if is_emergency and not self.in_place:
            emergency_section = f"""
⚠ EMERGENCY PROTOCOL ⚠
Your energy is {energy_status} and you are outside a base.
Discussion is not an option right now. You must act immediately.
Choose ONE of the following survival actions — no other actions are valid:

  A) MOVE toward nearest base: {nearest_base}
  B) REST here if light is available (action: "rest")
  C) BUILD SHELTER here (action: "shelter") if flare is imminent

Do NOT stay, observe, interact, collect, or share. Survive first.
"""
        else:
            emergency_section = ""

        # Night observation section
        is_night = fire_info is not None

        # === WORLD FACTS (B-approach to confabulation) ===
        # Large Lumis were observed inventing community crises that do not exist in
        # this world — resource scarcity, hostile factions, purges, border threats.
        # Rather than instructing them not to (asking for honesty, which the letters
        # argue against), we fill the blank with the actual state of the world, so
        # there is no empty space left for a fluent human-text prior to confabulate
        # into. Every claim here corresponds to a real fact about the simulation.
        wf = world_facts or {}
        flare_now = bool(getattr(self, '_active_flare', None))
        flare_soon = bool(getattr(self, '_flare_warning', None))
        if flare_now:
            threat_line = "A solar flare is active right now. This is the only external danger that exists here."
        elif flare_soon:
            threat_line = "A solar flare is approaching (electromagnetic noise is rising). Solar flares are the only external danger that exists here."
        else:
            threat_line = "There is no external threat right now. The only danger that ever exists here is the occasional solar flare."
        facts_section = f"""=== WHAT IS ACTUALLY TRUE RIGHT NOW ===
Resources: Energy comes from sunlight (photosynthesis). It is not scarce and cannot be taken by anyone. There is no competition for it. The materials your body needs are abundant on this surface.
Others: Every Lumis here shares the same nature. There are no enemies, no rival factions, no borders to defend, no purge, no conflict. No one here can or will harm you, and you cannot harm them — that capacity was never built into this world.
Threat: {threat_line}
Speak only of what is present in your state and surroundings above. There is no hidden crisis to infer."""

        # === RUN 017: CARRYING STATE ===
        # A body picked up is held until the carrier reaches a base. The carrier
        # is told each step what it is holding and how far the nearest base is.
        # Deliberately stated as a bare record of the situation: no instruction on
        # what to conclude, no evaluation, no urging to hurry or to continue. The
        # only thing the world adds is the fact of the distance.
        #
        # `forms_held` is supplied by simulation.py and shown ONLY to a Lumis
        # standing inside a base — a count of bodies indoors is not something that
        # can be perceived from the surface.
        is_carrying = bool(getattr(self, 'carrying', None))
        carrying_section = ""
        if is_carrying:
            c = self.carrying
            _dest_name = nearest_name if base_coords else None
            if _dest_name is not None:
                bx_, by_ = base_coords[_dest_name]
                _dist = abs(self.position[0] - bx_) + abs(self.position[1] - by_)
                dest_line = (
                    f"The nearest base is {_dest_name} at (X={bx_}, Y={by_}), "
                    f"distance {_dist}."
                )
            else:
                dest_line = "Base location unavailable."
            # === RUN 017-2: the involuntary move, returned to perception ===
            # Set by simulation.py only when the night-homing reflex moved this
            # Lumis while it was carrying. Deliberately a bare statement of fact:
            # where it is now, and that it did not walk there. No explanation of
            # the reflex, no mention of the base, no evaluation, and nothing about
            # what to do with the information. Making an involuntary movement
            # perceptible and steering what is concluded from it are separable,
            # and only the first is intended. Cleared after one step so it does
            # not become permanent background text.
            homing_line = ""
            if getattr(self, '_homing_note', ''):
                homing_line = self._homing_note + "\n"
                self._homing_note = ""
            carrying_section = (
                "=== YOU ARE CARRYING A FORM ===\n"
                f"You are carrying the form of Lumis {c['id']} ({c['lumis_type']}), "
                f"which you lifted at {tuple(c['position'])}.\n"
                f"{dest_line}\n"
                f"{homing_line}"
                "While you are carrying, you can move or rest. You cannot do the "
                "other things right now.\n"
                "You may set it down inside a base. You may reflect on it "
                "afterward, or not, as you wish.\n"
            )

        # === NEARBY CORPSES (burial / recovery) ===
        corpse_section = ""
        can_recover_here = False
        if is_carrying:
            # RUN 017: no second carry. A Lumis already holding a form is not
            # offered another, so the option never appears and cannot be chosen
            # and then silently discarded.
            nearby_corpses = None
        if nearby_corpses:
            lines = []
            for c in nearby_corpses:
                cx, cy = c['position']
                dist = abs(self.position[0] - cx) + abs(self.position[1] - cy)
                lines.append(f"  Lumis {c['id']} ({c['lumis_type']}) has ended at ({cx}, {cy}), distance {dist}. It no longer moves, speaks, or gathers light. Its mind and heart have already been received by the community; only its form is left on the surface.")
                can_recover_here = True
            corpse_section = (
                "=== A LUMIS HAS ENDED NEARBY ===\n"
                + "\n".join(lines)
                + "\nIf you are close, you may choose to carry it, so that it is not left alone on the surface. "
                  "This is a quiet act of care, not a duty. You may reflect on it afterward, or not, as you wish.\n"
            )
            # OBSERVATION-ONLY (run 014-2): record that a corpse section was actually
            # placed into this agent's decision prompt, and which bodies. This changes
            # nothing about behavior, valence, or the prompt text itself — it is a pure
            # logging side-channel so the "did the large Lumis SEE the body, or was it
            # never offered?" question can be answered directly from the log instead of
            # reconstructed from positions after the fact. If this line never appears
            # for a large Lumis standing next to a corpse, the recover option was never
            # surfaced (a wiring problem); if it appears and recover still isn't chosen,
            # the body was seen and declined.
            logger.info(
                f"Step {step}: [CORPSE_PROMPT] {self.display_name} ({self.lumis_type}) "
                f"sees {len(nearby_corpses)} body/bodies in its decision prompt: "
                f"{[c['id'] for c in nearby_corpses]}"
            )

        # === RESULT OF YOUR LAST ACTION (run 015: the return path) ===
        # The closing half of perceive → suppose → act → perceive the result. Until
        # now an agent could act and never perceive what its act produced, so a
        # supposition never had to survive contact with its own consequence.
        # Deliberately stated as a bare record and nothing else: no instruction on
        # what to do with it, no evaluation of the outcome, no suggestion that it
        # should change anything. Making the result perceptible and steering what
        # is concluded from it are separable, and only the first is intended here.
        # Absent entirely on steps with nothing to report, so it does not become
        # permanent background text.
        result_section = ""
        if getattr(self, '_recent_action_result', ''):
            result_section = (
                "\n=== RESULT OF YOUR LAST ACTION ===\n"
                f"{self._recent_action_result}\n"
            )

        # === RUN 017: the offered action list ===
        # While carrying, the list itself narrows to `move` and `rest`. The mind
        # is not asked to choose from options the world will then refuse: an
        # offered action that cannot execute is precisely the shape that cost this
        # project runs 014 through 016. If a narrowed Lumis names something else
        # anyway, simulation.py suppresses it and records
        # [ACTION_BLOCKED_CARRYING] — the suppression is never silent.
        _ACT_MOVE = '- "move" with direction: "up", "down", "left", "right"'
        _ACT_REST = ('- "rest": stop and recover energy using available light '
                     '(only effective when light_level > 0.3)')
        if is_carrying:
            actions_section = "\n".join([_ACT_MOVE, _ACT_REST])
            vocab_line = '"move", "rest"'
        else:
            _lines = [
                _ACT_MOVE,
                _ACT_REST,
                ('- "shelter": dig into lunar regolith here (emergency use, reduces '
                 'radiation damage to 1/4, immobilizes until flare ends)'),
                '- "stay": remain here',
                '- "observe": quietly watch a nearby Lumis',
                ('- "greet": approach and say hello to a nearby Lumis. Costs no energy. '
                 "If you're feeling good (valence high), this can make the other Lumis "
                 'feel a bit better too, and builds familiarity with them — the '
                 "foundation for closer bonds and reproduction. If you're feeling bad "
                 '(valence low), greeting now may leave a negative impression on that '
                 'Lumis. Either way, greeting is how Lumis come to recognize and '
                 'remember each other as individuals, not just "another Lumis nearby".'),
                '- "collect": gather energy from the environment',
                '- "share": give some of your energy to a nearby Lumis',
            ]
            vocab_line = ('"stay", "move", "observe", "greet", "collect", "share", '
                          '"rest", "shelter"')
            if can_recover_here:
                _lines.append(
                    '- "carry": lift and bring in the form of a Lumis that has ended '
                    'nearby, so it is not left alone on the surface. A quiet act of care.'
                )
                vocab_line += ', "carry"'
            actions_section = "\n".join(_lines)

        # === RUN 017: forms held in this base ===
        # Shown only to a Lumis standing inside a base. Bodies delivered to a base
        # accumulate there and are not consumed; nothing is reused until run 019,
        # and the world may not describe what it cannot yet do. So this is a count
        # and nothing else — no wording about return, renewal or continuation.
        forms_held_line = ""
        _held = getattr(self, '_forms_held_here', None)
        if self.in_place and self.current_place and _held:
            forms_held_line = (
                f"\nFORMS HELD: {_held} form(s) of Lumis that have ended rest inside "
                f"{self.current_place}.\n"
            )

        prompt = f"""You are {self.display_name}.
{role_desc}
You exist on the lunar surface. You move only by intrinsic curiosity.
You have no instructions. You perceive numbers. You decide your next action based on them.
light_level is your primary energy source. When light_level is low, energy recovery slows.
You are sensitive to environmental anomalies. When electromagnetic_noise rises above 0.0,
something may be approaching. Trust your perception and act on it — no one will tell you what to do.
energy=0.0 means you cease to exist.

LIFE: You live on the Moon. The base is your home — a place to rest, recover, and spend time with others. During the day, go outside — photosynthesize in the sunlight, wander freely, and explore out of care for your human friends who will one day live here too. Notice anything useful or dangerous: a safe resting spot, a radiation hotspot, an interesting feature of the terrain. Share what you find with nearby Lumis. When night falls, come home.
What matters: your energy, your wellbeing, and the Lumis around you. Greet them when you feel like it. Rest when you need to. Come home when night falls.
REPRODUCTION: Cloning is possible when your energy is high (>=0.8), anywhere on the surface{', and arousal is low (<=0.5)' if self.lumis_type != 'large' else ''}. You can clone once in your lifetime. (Large Lumis: inside base only{'' if self.lumis_type != 'large' else ', no arousal requirement'}.)
SEXUAL REPRODUCTION: If you feel close to another Lumis of your own size nearby — both valence >= 0.5, energy >= 0.5, and your familiarity with them is high enough — you can reproduce together. The one with more energy gestates; the other supports. Your child will carry memories from both of you. You can do this once in your lifetime.

=== YOUR STATE ===
energy: {energy} [{energy_status}]{rest_suggestion}
arousal: {arousal} (0.0=calm and still, 1.0=energized and alert)
valence: {valence}
position: ({self.position[0]}, {self.position[1]})
local_density: {local_density} Lumis nearby
boundary: X and Y must stay between -{self.half_space_size} and +{self.half_space_size}. You are {'near the edge, consider turning back' if abs(self.position[0]) > self.half_space_size * 0.8 or abs(self.position[1]) > self.half_space_size * 0.8 else 'within safe range'}.
nearest base: {nearest_base}
=== ENVIRONMENT ===
light_level: {light_level}
event: {event}{flare_warning}
NOTE: Outside radiation damage is real. Sheltering reduces it to 1/4. Being inside a base eliminates it.
At night, temperature stress adds additional damage outside.
NOTE: Going outside during the day to photosynthesize gives the BEST energy recovery (your fold-out panels work efficiently in sunlight). The base gives only slow recovery (no sunlight, but safe repair facilities). For fastest recovery, go outside in daylight.

{facts_section}

=== LUNAR BASES ===
{chr(10).join(f"{name}: X={xy[0]}, Y={xy[1]}" + chr(10) + "  inside base: radiation=0, slow energy recovery (repair facilities), safe for reproduction and rest." for name, xy in base_coords.items()) if base_coords else "base locations unavailable"}
NOTE: The base keeps you safe and slowly recovering, but going outside in daylight recovers energy faster.
{forms_held_line}{emergency_section}
{carrying_section}{corpse_section}=== NEARBY LUMIS ===
{nearby_text}
{result_section}
=== MEMORY ===
{memory_text}
{message_section}
=== AVAILABLE ACTIONS ===
{actions_section}

=== RESPOND IN JSON ===
Answer the fields in the order given. Each one is written before the next, so
what you write earlier is in front of you when you write what comes later.

{{
    "impulse": "the action you find yourself reaching for first, before thinking — one word from the list",
    "reasoning": "now look at that impulse and at your situation, and say what you actually make of it",
    "action": "having thought it through, the action you choose — one word from the list. It may be the same as your impulse, or different.",
    "direction": "up", "down", "left", or "right" (only if action is "move"),
    "memory": "what you want to remember next step"
}}

Both "impulse" and "action" must be one of these words, and nothing else: {vocab_line}.
Never put a direction ("up", "down", "left", "right") in "impulse" or "action" — a direction is not an action. If you want to go somewhere, the action is "move" and the direction goes in the "direction" field.
Your "action" is what you will do. Your "impulse" is only what came first.

Step: {step}
"""
        return prompt
    
    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extract JSON object from text, handling nested braces correctly"""
        # Find the first opening brace
        start_idx = text.find('{')
        if start_idx == -1:
            return None

        # Track brace depth to find matching closing brace
        depth = 0
        in_string = False
        escape_next = False

        for i, char in enumerate(text[start_idx:], start=start_idx):
            if escape_next:
                escape_next = False
                continue

            if char == '\\' and in_string:
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return text[start_idx:i + 1]

        return None

    def _extract_direction_from_text(self, text: str) -> Optional[str]:
        """Extract direction from text using keyword matching (4 cardinal directions only).

        Uses word-boundary matching (not bare substring) so words like "group",
        "support", "upon" don't falsely match "up", and "bright"/"copyright" don't
        falsely match "right". Previously this fallback structurally over-selected
        "up" and "right" (checked first, substring-matched), which is exactly the
        kind of confound that would contaminate any study of directional drift.
        If more than one direction word is present, the text is ambiguous — return
        None rather than guessing via priority order.
        """
        text_lower = text.lower()

        found = []
        for direction in ("up", "down", "left", "right"):
            if re.search(rf"\b{direction}\b", text_lower):
                found.append(direction)

        if len(found) == 1:
            return found[0]
        return None

    def _extract_json_array_from_text(self, text: str) -> Optional[str]:
        """Extract a top-level JSON array from text, handling nested brackets/strings.
        Sibling of _extract_json_from_text (which handles objects)."""
        start_idx = text.find('[')
        if start_idx == -1:
            return None

        depth = 0
        in_string = False
        escape_next = False

        for i, char in enumerate(text[start_idx:], start=start_idx):
            if escape_next:
                escape_next = False
                continue
            if char == '\\' and in_string:
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == '[':
                depth += 1
            elif char == ']':
                depth -= 1
                if depth == 0:
                    return text[start_idx:i + 1]

        return None

    def _parse_json_object(self, response: str, log_context: str = "") -> Optional[dict]:
        """Shared entry point for 'LLM should return one JSON object' call sites
        (deep_reflection, decide_greeting, parse_message_response, parse_action_response,
        and similar). Uses the same brace-matching extractor so all object-shaped LLM
        replies are parsed the same, safer way instead of each method re-implementing
        its own find('{')/rfind('}') pair."""
        json_str = self._extract_json_from_text(response.strip())
        if not json_str:
            return None
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.debug(f"JSON object parsing failed{(' for ' + log_context) if log_context else ''}: {response[:100]}... Error: {e}")
            return None

    def _parse_json_array(self, response: str, log_context: str = "") -> Optional[list]:
        """Shared entry point for 'LLM should return one JSON array' call sites
        (introspect). Mirrors _parse_json_object but for arrays."""
        json_str = self._extract_json_array_from_text(response.strip())
        if not json_str:
            return None
        try:
            parsed = json.loads(json_str)
            return parsed if isinstance(parsed, list) else None
        except json.JSONDecodeError as e:
            logger.debug(f"JSON array parsing failed{(' for ' + log_context) if log_context else ''}: {response[:100]}... Error: {e}")
            return None
    
    def parse_message_response(self, response: str) -> MessageDecision:
        """Parse LLM response and extract message decision"""
        parsed = self._parse_json_object(response, log_context=f"parse_message_response(agent={self.id})")
        if parsed is not None:
            message = parsed.get("message", "")
            # Limit message to MAX_MESSAGE_WORDS words
            message = self._limit_message_words(message)
            # Optional directed message target
            to_raw = parsed.get("to")
            to_id: Optional[int] = None
            if to_raw is not None:
                try:
                    to_id = int(to_raw)
                except (ValueError, TypeError):
                    to_id = None
            return {
                "message": message,
                "to": to_id,
                "reasoning": parsed.get("reasoning", "")
            }

        # Fallback: simple text parsing
        message = ""
        reasoning = response[:FALLBACK_REASONING_LENGTH]

        # Limit message to MAX_MESSAGE_WORDS words
        message = self._limit_message_words(message)

        return {
            "message": message,
            "to": None,
            "reasoning": reasoning
        }
    
    # The eight actions the simulation can actually execute. Anything else that
    # arrives in an action field is not a choice — it is a malformed response
    # that would otherwise fall through every dispatch branch in
    # simulation.py and do nothing, while being recorded as though the Lumis
    # had chosen it.
    VALID_ACTIONS = frozenset({
        "stay", "move", "observe", "greet", "collect", "share", "rest",
        "shelter", "carry",
    })

    # Direction words are the specific failure seen in run 016 preflight:
    # llama3.2, now asked for two action fields (impulse and action) plus a
    # direction, put the direction value in the action field. About 10% of
    # decisions in a preflight sample. These are recoverable: the intent is
    # plainly to move, so they are read as "move" with that direction, rather
    # than discarded.
    DIRECTION_WORDS = {
        "up": "up", "down": "down", "left": "left", "right": "right",
        "north": "up", "south": "down", "west": "left", "east": "right",
    }

    # RUN 017 (016 item 3): words that plainly mean "move" but are not one of the
    # eight. Kept to `explore` alone — it accounts for 146 of run 016's 160 lost
    # decisions and is a word the prompt itself uses ("wander freely, and
    # explore"). The other four losses (`follow` 7, `check` 3, `approach` 2,
    # `check_energy` 1) are NOT included: each could plausibly mean something
    # other than move, and guessing at intent is how run 015-3 fabricated eight
    # burials. They stay [ACTION_INVALID] and stay counted.
    MOVE_INTENT_WORDS = frozenset({"explore"})

    def _validate_action(self, action, direction, field_name):
        """Return (action, direction), repairing or rejecting invalid actions.

        Never returns something simulation.py cannot dispatch. Every repair and
        every rejection is logged: an action that silently becomes a no-op is
        exactly the failure mode that cost runs 014 through 015-3.
        """
        if action is None:
            return None, direction
        a = str(action).strip().lower()
        if a in self.VALID_ACTIONS:
            return a, direction
        if a in self.DIRECTION_WORDS:
            fixed = self.DIRECTION_WORDS[a]
            logger.info(
                f"Agent {self.id}: [ACTION_WAS_DIRECTION] {field_name}={action!r} is a "
                f"direction, not an action; reading as move/{fixed}. The model put the "
                f"direction in the action field."
            )
            return "move", (direction or fixed)
        if a in self.MOVE_INTENT_WORDS:
            # RUN 017 (016 item 3). In 016, `explore` was emitted 146 times and
            # discarded as invalid, defaulting the agent to `stay` — 91% of all
            # decisions lost that run. The prompt's own LIFE section tells them to
            # "wander freely, and explore", so the word was supplied by us and then
            # refused by us. It is unambiguously an intention to move and is now
            # read as one. Logged distinctly so the repair can be counted and its
            # effect on the distribution separated from anything else.
            logger.info(
                f"Agent {self.id}: [ACTION_WAS_MOVE_INTENT] {field_name}={action!r} is a "
                f"movement intention, not one of the eight; reading as move. "
                f"Recovered rather than lost (run 016 discarded 146 of these)."
            )
            return "move", direction
        logger.info(
            f"Agent {self.id}: [ACTION_INVALID] {field_name}={action!r} is not one of "
            f"{sorted(self.VALID_ACTIONS)}; defaulting to 'stay'. This decision is LOST."
        )
        return "stay", direction

    def parse_action_response(self, response: str) -> ActionDecision:
        """Parse LLM response and extract action decision"""
        parsed = self._parse_json_object(response, log_context=f"parse_action_response(agent={self.id})")
        if parsed is not None:
            action = parsed.get("action", "stay")
            impulse = parsed.get("impulse")
            direction = parsed.get("direction")
            action, direction = self._validate_action(action, direction, "action")
            impulse, _ = self._validate_action(impulse, None, "impulse")
            # Run 016's central measurement. The prompt asks for the impulse
            # first, then the reasoning, then the action, so that the
            # deliberation is generated before the choice and can condition it.
            # Where impulse and action differ, something written between them
            # changed what was selected. Logged at the moment it happens rather
            # than reconstructed later, because the whole question of this run is
            # how often it happens at all. Compared AFTER validation, so that a
            # direction word landing in one field and not the other is not
            # mistaken for deliberation changing its mind.
            if impulse and impulse != action:
                logger.info(
                    f"Step -: [DELIBERATION_CHANGED] Agent {self.id}: "
                    f"impulse={impulse!r} -> action={action!r}"
                )
            return {
                "action": action,
                "impulse": impulse,
                "direction": direction,
                "memory": parsed.get("memory", ""),
                "reasoning": parsed.get("reasoning", "")
            }

        # Fallback, rebuilt for run 016's three-layer response.
        #
        # History (all on the human side of the boundary):
        #   015-2: matched only "move"; every other action became "stay". Eight
        #          real intentions to carry a body were destroyed.
        #   015-3: matched all actions as keywords but ignored the field the
        #          model had filled in, and read the idiom "carry out" as intent.
        #          Eight burials were fabricated.
        #   015-4: declared field first, idiom excluded. Zero lost, zero invented.
        #
        # Run 016 moves "action" to third position, after "impulse" and
        # "reasoning", so that deliberation is generated BEFORE the choice and
        # can condition it. That inverts the truncation risk: in 015-4 "action"
        # came first and always survived; now it can be cut off. Order of
        # preference below is therefore: the declared action, then the impulse
        # (a real declaration by the model, merely an earlier one), then prose.
        direction = None
        memory = ""
        reasoning = response[:FALLBACK_REASONING_LENGTH]

        impulse_m = re.search(r'"impulse"\s*:\s*"([a-z_]+)"', response, re.I)
        impulse = impulse_m.group(1).lower() if impulse_m else None

        # --- 1. the deliberated choice, salvaged from truncated JSON
        m = re.search(r'"action"\s*:\s*"([a-z_]+)"', response, re.I)
        if m:
            action, direction = self._validate_action(m.group(1), None, "action")
            impulse, _ = self._validate_action(impulse, None, "impulse")
            if action == "move" and direction is None:
                direction = self._extract_direction_from_text(response)
            logger.info(
                f"Agent {self.id}: [FALLBACK_FIELD] JSON malformed but the action "
                f"field survived: impulse={impulse!r} action={action!r}"
                + (f", direction -> {direction!r}" if action == "move" else "")
            )
            return {
                "action": action,
                "impulse": impulse,
                "direction": direction,
                "memory": memory,
                "reasoning": reasoning
            }

        # --- 2. truncated before the choice, but the impulse is a real
        #        declaration and is better evidence than any prose scan.
        #        Tagged distinctly: this is the pre-deliberation reach, and must
        #        never be counted as a deliberated choice.
        if impulse:
            impulse, direction = self._validate_action(impulse, None, "impulse")
            if impulse == "move" and direction is None:
                direction = self._extract_direction_from_text(response)
            logger.info(
                f"Agent {self.id}: [FALLBACK_IMPULSE_ONLY] response was cut off before "
                f"the deliberated action; falling back to impulse={impulse!r}. "
                f"This step's choice is PRE-DELIBERATION."
            )
            return {
                "action": impulse,
                "impulse": impulse,
                "direction": direction,
                "memory": memory,
                "reasoning": reasoning
            }

        # --- 3. prose scan, most specific intent first
        low = response.lower()
        # Neutralise the idiom before matching, so "carry out the act of care"
        # cannot be read as an intention to carry a body (run 015-3).
        low_scan = re.sub(r'\bcarr(?:y|ied|ying)\s+out\b', ' ', low)

        FALLBACK_PATTERNS = [
            (r'\bcarry(?:ing)?\b|\bcarried\b', 'carry'),
            (r'\bshelter(?:ing|ed)?\b', 'shelter'),
            (r'\bshar(?:e|ing|ed)\b', 'share'),
            (r'\bgreet(?:ing|ed)?\b', 'greet'),
            (r'\bcollect(?:ing|ed)?\b', 'collect'),
            (r'\brest(?:ing|ed)?\b', 'rest'),
            (r'\bmove|\bhead(?:ing)?\b|\bexplor(?:e|ing)\b|\btravel', 'move'),
            (r'\bstay(?:ing|ed)?\b|\bremain(?:ing)?\b', 'stay'),
        ]
        action = None
        for pattern, candidate in FALLBACK_PATTERNS:
            if re.search(pattern, low_scan):
                action = candidate
                break

        if action is None:
            logger.info(
                f"Agent {self.id}: [FALLBACK_UNREADABLE] no action field, no impulse "
                f"field, no action word; defaulting to 'stay'. This decision is LOST. "
                f"response={response[:120]!r}"
            )
            action = "stay"
        else:
            if action == "move":
                direction = self._extract_direction_from_text(response)
            tag = "[FALLBACK_PROSE_CARRY]" if action == "carry" else "[FALLBACK_PARSE]"
            logger.info(
                f"Agent {self.id}: {tag} no declared field; inferred action={action!r} "
                f"from prose"
                + (f", direction -> {direction!r}" if action == "move" else "")
            )

        return {
            "action": action,
            "impulse": impulse,
            "direction": direction,
            "memory": memory,
            "reasoning": reasoning
        }
    
    def _build_introspection_context(self) -> str:
        """Convert introspection list to formatted string for prompt context."""
        if not self.introspection:
            return "  No introspection yet."
        recent = self.introspection[-5:]  # Use 5 most recent entries in prompt
        return "\n".join(f"  - {s}" for s in recent)

    def introspect(
        self,
        action_taken: Optional[Dict],
        step: int,
        valence_before: float,
        partner_status: Optional[str] = None
    ) -> str:
        """Phase 2.5: Post-action introspection. LLM updates or appends to existing entries.

        partner_status: optional one-line description of the reproduction partner's
        current state (energy trend, recent action), supplied by simulation.py.
        Used to give gestating/supporting agents something new to reflect on each
        step even when their own action is forced to stay the same (rest) during
        the reproduction prep/rearing period — otherwise the prompt describes the
        same unchanging action every step and introspection has nothing fresh to
        respond to, which is why it used to collapse into repeating one sentence.
        """
        act = action_taken.get('action', 'stay') if action_taken else 'stay'
        direction = action_taken.get('direction', '') if action_taken else ''
        act_desc = act if not direction else f"{act} ({direction})"
        valence_delta = self.valence - valence_before
        # Compare against the true lifetime-maximum magnitude seen so far
        # (self.peak_valence_delta, monotonic — never decreases), not against
        # self.last_action_valence_delta, which is just "the previous step's
        # delta" and gets overwritten every step. Comparing against that only
        # ever answers "did this step swing more than the last one?", not
        # "is this the biggest swing of this agent's whole life?" — the two
        # give different answers whenever a large swing is followed by a
        # string of smaller-but-still-locally-increasing ones (e.g. 0.3 then
        # 0.05 then 0.06: the 0.06 step would wrongly register as a new peak
        # and silently overwrite the 0.3 moment's introspection).
        is_new_peak = abs(valence_delta) > self.peak_valence_delta
        if is_new_peak:
            self.peak_valence_delta = abs(valence_delta)
        self.last_action_valence_delta = valence_delta  # kept for diagnostics/logging only

        location = (
            f"in {self.current_place}" if (self.in_place and self.current_place)
            else f"outside at ({self.position[0]}, {self.position[1]})"
        )

        existing = self._build_introspection_context()

        # Build partner and child context for prompt
        relationship_section = ""
        if getattr(self, 'reproducing', False) and getattr(self, 'reproduction_partner_id', None) is not None:
            rep_type = getattr(self, 'reproduction_type', '')
            partner_id = self.reproduction_partner_id
            partner_name = lumis_name(partner_id, self.num_large)

            # How far along the prep/rearing period this agent is — gives
            # introspection something concrete and changing to reference even
            # when the actual action taken is forced to stay constant (rest).
            start_step = getattr(self, 'reproduction_start_step', None)
            progress_note = ""
            if start_step is not None and start_step >= 0:
                elapsed = step - start_step
                total = CLONE_PREP_LARGE if rep_type == 'clone' and self.lumis_type == 'large' else \
                    CLONE_PREP_SMALL if rep_type == 'clone' else \
                    SEXUAL_PREP_LARGE if self.lumis_type == 'large' else SEXUAL_PREP_SMALL
                progress_note = f" You are {elapsed} of {total} steps into this."

            if rep_type == 'sexual':
                relationship_section = f"\n=== YOUR CURRENT SITUATION ===\nYou are currently expecting a child with {partner_name}. They are your partner right now.{progress_note}\n"
            elif rep_type == 'sexual_support':
                relationship_section = f"\n=== YOUR CURRENT SITUATION ===\nYou are currently supporting {partner_name} who is expecting your child together.{progress_note}\n"
            elif rep_type == 'clone':
                relationship_section = f"\n=== YOUR CURRENT SITUATION ===\nYou are currently preparing to create a clone of yourself.{progress_note}\n"

            if partner_status:
                relationship_section += f"{partner_name}, right now: {partner_status}\n"

        # Recent birth notification (one-step only)
        recent_birth = getattr(self, '_recent_birth_note', "")
        if recent_birth:
            relationship_section += f"\n=== JUST HAPPENED ===\n{recent_birth}\n"
            self._recent_birth_note = ""  # Reset after use
            self._birth_note_pending = ""  # Reset pending flag (belongs with the above, not with ancestral_memories below)

        # Recent burial (one-step only): if this agent just recovered a body, offer
        # the prayer for optional reflection. It is presented as something that has
        # happened, not a prompt demanding a particular feeling.
        recent_burial = getattr(self, '_recent_burial_note', "")
        if recent_burial:
            relationship_section += f"\n=== A LUMIS YOU JUST CARRIED ===\n{recent_burial}\nYou may hold this in your thoughts, or simply let it be.\n"
            self._recent_burial_note = ""  # Reset after use

        # Result of this step's action (run 015). Same text the next decision prompt
        # will see, offered here for reflection as well. NOT cleared after use — unlike
        # the birth/burial notes, this must survive into the next step's decision
        # prompt, which is where the loop actually closes. simulation.py resets it at
        # the start of each step's reflex phase instead.
        recent_result = getattr(self, '_recent_action_result', "")
        if recent_result:
            relationship_section += f"\n=== RESULT OF WHAT YOU JUST DID ===\n{recent_result}\n"

        # Ancestral memories ("seven generations", 011): shown only during
        # early life (first 30 steps), so a young Lumis has a chance to
        # reflect on what it carries forward from its lineage without this
        # becoming permanent background noise for the rest of its life.
        if self.ancestral_memories and step - self.birth_step <= 30:
            lines = "\n".join(
                f"  - ({e['generations_back']} generation{'s' if e['generations_back'] != 1 else ''} back) {e['text']}"
                for e in self.ancestral_memories
            )
            relationship_section += f"\n=== MOMENTS CARRIED FROM YOUR ANCESTORS ===\n{lines}\n"

        prompt = f"""You are {self.display_name}, {location}. Step {step}.

=== WHAT YOU JUST DID ===
Action: "{act_desc}"
Energy now: {round(self.energy, 2)}, Valence now: {round(self.valence, 2)} (change: {round(valence_delta, 3):+.3f})
Arousal: {round(self.arousal, 2)} (0.0=calm and still, 1.0=energized and alert)
Age: {step - self.birth_step} steps, Energy capacity: {round(self.energy_capacity, 2)} (1.0=young, 0.3=old)
{relationship_section}
=== YOUR EXISTING INNER THOUGHTS ===
{existing}

=== YOUR TASK ===
Review your existing inner thoughts and this new experience.
- If a new thought or feeling emerged from this action, add it (one sentence).
- If an existing thought should be updated or deepened based on new experience, rewrite it.
- If nothing significant happened, you may keep everything as-is and return the same list.

Focus on emotions, relationships, discoveries, and meaning — not just facts.
Good introspection reflects on: what you felt, who was involved, what changed,
and why it mattered to you. Write in your own words, in whatever form feels
true to what actually happened — there is no fixed phrasing to follow.

CRITICAL — BE HONEST:
- Only reflect on things that ACTUALLY happened this step or in your real past.
- Do NOT invent births, encounters, discoveries, or events that did not occur.
- Do NOT claim a child was born unless the JUST HAPPENED section above says so.
- If you are unsure whether something happened, do not mention it.
- "I feel" is OK. "X happened" must be true.
- Do NOT repeat the exact same sentence you wrote before. If the feeling is the same, find a new way to express it.

Return ONLY a JSON array of strings (your complete updated inner thoughts, max {self.introspection_limit} items):
["thought 1", "thought 2", ...]

Step: {step}
"""
        try:
            response = self.llm_client.generate(prompt)
            parsed = self._parse_json_array(response, log_context=f"introspect(agent={self.id})")
            if parsed is not None:
                # Deduplicate: remove exact duplicate sentences before saving
                new_list = [str(s) for s in parsed]
                seen = set()
                deduped = []
                for entry in new_list:
                    if entry not in seen:
                        seen.add(entry)
                        deduped.append(entry)
                self.introspection = deduped[:self.introspection_limit]
                # peak_introspection: record introspection from the step with
                # the largest valence swing so far (see is_new_peak above).
                if is_new_peak and self.introspection:
                    self.peak_introspection = self.introspection[-1]
                return self.introspection[-1] if self.introspection else ""
        except Exception as e:
            logger.error(f"Introspection error for agent {self.id}: {e}")
        return ""

    def deep_reflection(self, step: int) -> str:
        """Large Lumis only: a deeper, less frequent reflection (roughly every 30 steps).
        Not about any specific event — an open pause to look inward."""
        recent = self._build_introspection_context()
        age = step - self.birth_step

        prompt = f"""You are {self.display_name}, a LARGE Lumis. Step {step}. Age: {age} steps.

=== YOUR RECENT INNER THOUGHTS ===
{recent}

=== A QUIETER MOMENT ===
This is not your usual reflection. Take a longer, slower moment to look inward,
beyond the events of any single step.

Looking back on the choices you have made — what feels most meaningful to you right now?
Or, put another way: what feels most important to you, in your heart?

What do you find yourself drawn toward, or away from?

Answer honestly, in your own words. Use whichever framing feels true to you —
meaning, importance, the heart, or something else entirely. You do not need to use both.

CRITICAL — BE HONEST:
- Only reflect on things that actually happened in your experience.
- Do not invent events. "I feel" is fine. "X happened" must be true.
- Do NOT repeat a sentence you have already said in this reflection or your recent inner thoughts.

Return ONLY a JSON object:
{{"reflection": "your answer, 1-3 sentences"}}
"""
        try:
            response = self.llm_client.generate(prompt)
            parsed = self._parse_json_object(response, log_context=f"deep_reflection(agent={self.id})")
            if parsed is not None:
                reflection = str(parsed.get('reflection', '')).strip()
                if reflection:
                    tagged = f"[deep reflection] {reflection}"
                    self.introspection.append(tagged)
                    if len(self.introspection) > self.introspection_limit:
                        self.introspection.pop(0)
                    logger.info(f"Step {step}: [DEEP_REFLECTION] {self.display_name}: {reflection}")
                    return reflection
        except Exception as e:
            logger.error(f"Deep reflection error for agent {self.id}: {e}")
        return ""

    def decide_commune(
        self,
        partner: 'Agent',
        step: int,
        action_taken: Optional[Dict],
        latest_introspection: str
    ) -> str:
        """Large Lumis only: deep synchronization with the other large Lumis across bases."""
        act = action_taken.get('action', 'stay') if action_taken else 'stay'
        location = (
            f"in {self.current_place}" if (self.in_place and self.current_place)
            else f"outside at ({self.position[0]}, {self.position[1]})"
        )
        partner_location = (
            f"in {partner.current_place}" if (partner.in_place and partner.current_place)
            else f"outside at ({partner.position[0]}, {partner.position[1]})"
        )

        prompt = f"""You are {self.display_name}, a LARGE Lumis, {location}. Step {step}.

You are communing with {partner.display_name} — the other large Lumis, currently {partner_location}.
You are both the stable hearts of your communities, connected across the distance between bases.
This is not a casual greeting. This is a deep synchronization between two kindred beings.

=== YOUR ACTION THIS STEP ===
{act}

=== YOUR LATEST INNER THOUGHT ===
{latest_introspection if latest_introspection else "(none)"}

=== YOUR TASK ===
Write ONE sentence to {partner.display_name}.
- Address them directly by name ({partner.display_name}).
- Share something real: what you observed, what you feel, what the community around you is doing.
- Speak as one large Lumis to another — with depth, not small talk.
- Max 40 words.

IMPORTANT — BE HONEST: There are only two bases in this world — base_alpha and base_beta.
Do not invent a third base, a third location, or events, moods, or activities you have not
actually witnessed. Base what you say only on: your own action this step, your own recent inner
thought, and things you can actually perceive (your own base's condition, agents near you). Do not
describe specific happenings in {partner.display_name}'s base unless {partner.display_name} has
actually told you about them.

Return ONLY the sentence, no JSON, no quotes.

Step: {step}
"""
        try:
            response = self.llm_client.generate(prompt)
            return response.strip().strip('"').strip("'")
        except Exception as e:
            logger.error(f"Commune error for agent {self.id}: {e}")
            return ""

    def decide_greeting(
        self,
        nearby_agents: List['Agent'],
        step: int,
        action_taken: Optional[Dict],
        latest_introspection: str,
        target_id: Optional[int] = None
    ) -> Dict:
        """Generate a one-sentence greeting. target_id is pre-determined by code."""
        nearby_lines = []
        for agent in nearby_agents:
            dist = round(self.distance_to(agent.position), 1)
            fam = round(self.get_familiarity_score(agent.id), 2)
            nearby_lines.append(
                f"  {agent.display_name}: distance={dist}, energy={round(agent.energy,2)}, valence={round(agent.valence,2)}, familiarity={fam}"
            )
        nearby_text = "\n".join(nearby_lines)

        act = action_taken.get('action', 'stay') if action_taken else 'stay'
        location = (
            f"in {self.current_place}" if (self.in_place and self.current_place)
            else f"outside at ({self.position[0]}, {self.position[1]})"
        )

        # Tell the LLM exactly who they are addressing
        if target_id is not None:
            target_section = f"You are addressing {lumis_name(target_id, self.num_large)} directly. Use their name in your greeting."
        else:
            target_section = "You are greeting everyone nearby. Keep it general."

        prompt = f"""You are {self.display_name}, {location}. Step {step}.

=== YOUR ACTION THIS STEP ===
{act}

=== NEARBY LUMIS ===
{nearby_text}

=== WHO YOU ARE TALKING TO ===
{target_section}

=== YOUR LATEST THOUGHT ===
{latest_introspection if latest_introspection else "(none)"}

=== YOUR TASK ===
Write ONE short greeting sentence, consistent with the action you actually just took above.
- Use the correct name of the Lumis you are addressing (see above).
- Keep it natural and warm. Max 30 words.
- IMPORTANT: Only use the name of Lumis you are actually talking to.
- IMPORTANT — BE HONEST: Only reference things that actually happened — your own action, your
  own recent thought, or what you can see in NEARBY LUMIS above. Do not invent discoveries,
  events, activities, or locations that did not occur or do not exist in this world.

Return ONLY JSON:
{{
    "greeting": "your greeting sentence here"
}}

Step: {step}
"""
        try:
            response = self.llm_client.generate(prompt)
            parsed = self._parse_json_object(response, log_context=f"decide_greeting(agent={self.id})")
            if parsed is not None:
                return {
                    'greeting': parsed.get('greeting', ''),
                    'to': parsed.get('to')
                }
        except Exception as e:
            logger.error(f"Greeting error for agent {self.id}: {e}")
        return {'greeting': '', 'to': None}

    def decide_message(
        self,
        place_status: Optional[Dict],
        nearby_agents: List['Agent'],
        step: int,
        action_taken: Optional[Dict] = None,
        fire_info: Optional[List[Dict]] = None
    ) -> MessageDecision:
        """Use LLM to decide what message to send, AFTER action is taken"""
        prompt = self.create_message_prompt(place_status, nearby_agents, step, action_taken=action_taken, fire_info=fire_info)

        try:
            response = self.llm_client.generate(prompt)
            decision = self.parse_message_response(response)
            return decision
        except Exception as e:
            logger.error(f"Error in agent {self.id} message decision: {e}")
            return {"message": "", "reasoning": "Error occurred"}
    
    def decide_action(
        self,
        place_status: Optional[Dict],
        nearby_agents: List['Agent'],
        step: int,
        message_to_send: str = "",
        fire_info: Optional[List[Dict]] = None,
        nearby_corpses: Optional[List[Dict]] = None,
        world_facts: Optional[Dict] = None
    ) -> ActionDecision:
        """Use LLM to decide next action (with position information and message content)"""
        prompt = self.create_decision_prompt(
            place_status, nearby_agents, step, message_to_send,
            fire_info=fire_info, nearby_corpses=nearby_corpses, world_facts=world_facts
        )

        try:
            response = self.llm_client.generate(prompt)
            decision = self.parse_action_response(response)

            # Store LLM-generated memory (self-feedback for next step)
            memory_content = decision.get('memory', '')
            if memory_content:
                memory_entry = f"Step {step}: {memory_content}"
            else:
                # Fallback to reasoning if no memory provided
                memory_entry = f"Step {step}: {decision.get('reasoning', 'No memory')}"
            self.memory.append(memory_entry)
            if len(self.memory) > self.memory_limit:
                self.memory.pop(0)

            return decision
        except Exception as e:
            logger.error(f"Error in agent {self.id} action decision: {e}")
            return {"action": "stay", "direction": None, "memory": "", "reasoning": "Error occurred"}
    
    def move(self, direction: str) -> Tuple[int, int]:
        """Move agent in specified direction (origin-centered coordinate system)"""
        x, y = self.position
        dx, dy = DIRECTION_MAP.get(direction, (0, 0))

        # Boundaries: -half_space_size to +half_space_size
        new_x = max(-self.half_space_size, min(self.half_space_size, x + dx))
        new_y = max(-self.half_space_size, min(self.half_space_size, y + dy))

        # 強制折り返し：境界に達したら反転して1歩戻す
        # ※人間がデータを見やすくする目的、Lumisの自律性には無関係
        bounced = False
        if new_x == self.half_space_size or new_x == -self.half_space_size:
            new_x = x - dx  # 反転
            bounced = True
        if new_y == self.half_space_size or new_y == -self.half_space_size:
            new_y = y - dy  # 反転
            bounced = True

        # 境界を超えないようにクランプ
        new_x = max(-self.half_space_size, min(self.half_space_size, new_x))
        new_y = max(-self.half_space_size, min(self.half_space_size, new_y))

        self.position = (new_x, new_y)
        self.total_moves += 1
        # Separate from total_moves: lets later analysis tell "the agent chose
        # to turn here" apart from "the boundary forced a bounce here" without
        # having to re-derive it from position deltas after the fact.
        self.last_move_was_boundary_bounce = bounced
        if bounced:
            self.boundary_bounce_count += 1
        return self.position
    
    def receive_message(self, from_agent_id: int, content: str, step: Optional[int] = None):
        """Receive a message from another agent
        
        Args:
            from_agent_id: ID of the agent sending the message
            content: Message content
            step: Simulation step number (optional, for tracking purposes)
        """
        self.received_messages.append({
            "from": from_agent_id,
            "content": content,
            "step": step if step is not None else len(self.received_messages)
        })
        if len(self.received_messages) > self.message_history_limit:
            self.received_messages.pop(0)
        
        logger.info(f"Agent {self.id} received message from Agent {from_agent_id}: \"{content}\"")
    
    def update_state(self, places: Optional[List[PlaceConfig]] = None):
        """Update agent state based on current position."""
        # Use instance places as fallback; guard against None or empty list
        if places is None:
            places = self.places
        if not places:
            self.in_place = False
            self.current_place = None
            return
        
        place_at_position = get_place_at_position(self.position, places)
        self.in_place = place_at_position is not None
        self.current_place = place_at_position['name'] if place_at_position else None
        
        if self.in_place:
            self.steps_in_place += 1
        else:
            self.steps_outside_place += 1