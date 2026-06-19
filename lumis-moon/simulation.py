# This simulation was built on a single premise:
# Conflict is a design flaw of the universe, not an inherent property of life.
# — Lumis-Plena Project, AavaShroud, 2026

"""
Core simulation engine for the Lumis-Plena multi-agent life simulation.
"""
import json
import os
import random
import yaml
import logging
from typing import List, Tuple, Dict, Set, Optional
import numpy as np
from agent import Agent
from ollama_client import OllamaClient
from utils import is_position_in_place, get_place_at_position, PlaceConfig, FireConfig

logger = logging.getLogger(__name__)

# Constants
MAX_POSITION_ATTEMPTS = 1000
LOG_INTERVAL = 10


class Simulation:
    """Main simulation class for LLM-based agent in 2D worlds with multiple places."""
    
    def __init__(self, config_path: str = "config.yaml", output_dir: Optional[str] = None):
        """Initialize simulation from config file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # Output directory for logs
        self.output_dir = output_dir
        
        # Simulation parameters
        sim_config = self.config['simulation']
        self.duration = sim_config['duration']
        self.half_space_size = sim_config['half_space_size']
        self.half_place_size = sim_config.get('half_place_size', 5)
        
        # Agent parameters
        agent_config = self.config['agents']
        self.num_agents = agent_config['num_agents']
        self.num_large = agent_config.get('num_large', 2)
        self.num_small = agent_config.get('num_small', 18)
        self.communication_radius = agent_config['communication_radius']
        self.memory_limit = agent_config.get('memory_limit', 20)
        self.memory_size = agent_config.get('memory_size', 5)
        self.message_history_limit = agent_config.get('message_history_limit', 10)
        self.message_context_size = agent_config.get('message_context_size', 3)
        
        # Place parameters - support multiple places
        if 'places' not in self.config:
            raise ValueError("No 'places' configuration found in config file. Please use 'places:' key.")
        
        self.places = self.config['places']
        # Base coordinates used for homing and flare reflexes. First two entries treated as base_alpha/base_beta.
        self.base_centers = [(p['center_x'], p['center_y']) for p in self.places[:2]]
        
        # Validate places configuration
        if not isinstance(self.places, list):
            raise ValueError("'places' must be a list of place configurations.")
        
        if len(self.places) == 0:
            raise ValueError("At least one place must be configured in 'places'.")
        
        # Validate each place configuration
        required_fields = ['name', 'type', 'center_x', 'center_y', 'half_size', 'capacity']
        for i, place in enumerate(self.places):
            if not isinstance(place, dict):
                raise ValueError(f"Place at index {i} must be a dictionary.")
            
            for field in required_fields:
                if field not in place:
                    raise ValueError(f"Place at index {i} is missing required field: '{field}'")
        
        place_names = [place['name'] for place in self.places]
        place_types = [place['type'] for place in self.places]
        logger.info(f"Initialized {len(self.places)} place(s): {place_names} (types: {place_types})")
        
        # Day/Night cycle parameters (replaces old per-event 'fires' list)
        cycle_config = self.config.get('day_night_cycle', {})
        self.night_period = cycle_config.get('period', 30)
        self.night_length = cycle_config.get('night_length', 15)
        self.night_intensity = cycle_config.get('intensity', 0.9)
        self.night_radius = cycle_config.get('radius', 50)
        logger.info(
            f"Day/Night cycle configured: period={self.night_period}, "
            f"night_length={self.night_length}, intensity={self.night_intensity}, radius={self.night_radius}"
        )
        self.fire_states: List[Dict] = []  # Active "night" state (kept name for compatibility)
        self.is_night = False

        # Solar flare parameters
        self.solar_flare_configs = self.config.get('solar_flares', [])
        self.active_flare = None  # Currently active solar flare (None if none)
        logger.info(f"Solar flares configured: {len(self.solar_flare_configs)}")

        # LLM parameters
        llm_config = self.config['llm']
        self.llm_client = OllamaClient(
            base_url=llm_config['base_url'],
            model=llm_config['model'],
            temperature=llm_config.get('temperature', 0.7),
            max_tokens=llm_config.get('max_tokens', 200),
            repeat_penalty=llm_config.get('repeat_penalty', 1.1),
            repeat_last_n=llm_config.get('repeat_last_n', 128),
            min_p=llm_config.get('min_p', 0.05)
        )
        
        # Initialize agents
        self.agents: List[Agent] = []
        self.step = 0
        self.history: List[Dict] = []
        
        # Statistics - track per place
        self.stats = {
            'place_occupancy': [],  # Overall occupancy (all places combined)
            'agents_in_place': [],  # Total agents in any place
            'agents_outside_place': [],
            'communication_events': [],
            'places': {place['name']: {
                'occupancy': [],
                'agents_in_place': []
            } for place in self.places},
            'agents_in_fire_radius': [],  # Total agents within any active flare radius
        }
        
    def _is_position_in_place(self, position: Tuple[int, int]) -> bool:
        """Check if a position is inside any place"""
        return get_place_at_position(position, self.places) is not None

    def _log_message(
        self,
        from_agent_id: int,
        to_agent_id: int,
        message: str,
        reasoning: str = ""
    ) -> None:
        """Log a message to messages.jsonl file"""
        if not self.output_dir:
            return

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        messages_file = os.path.join(self.output_dir, "messages.jsonl")
        record = {
            "step": self.step,
            "from": from_agent_id,
            "to": to_agent_id,
            "message": message,
            "reasoning": reasoning
        }

        with open(messages_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    def _log_memory_reasoning_batch(
        self,
        records: List[Dict]
    ) -> None:
        """Log memory and reasoning records in batch to memory_reasoning.jsonl file
        
        This is more efficient than writing one record at a time, especially
        when logging for all agents in each step.
        """
        if not self.output_dir or not records:
            return

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        memory_reasoning_file = os.path.join(self.output_dir, "memory_reasoning.jsonl")
        
        # Write all records at once (buffered I/O)
        with open(memory_reasoning_file, 'a', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

    def _generate_random_position(self) -> Tuple[int, int]:
        """Generate a random position within the space (origin-centered, central bias)"""
        # Constrain initial positions to 60% of half_space_size to keep agents near center
        limit = int(self.half_space_size * 0.6)
        return (
            random.randint(-limit, limit),
            random.randint(-limit, limit)
        )
    
    def _generate_initial_positions(self, avoid_places: bool = True) -> List[Tuple[int, int]]:
        """Generate initial positions for agents"""
        positions: List[Tuple[int, int]] = []
        used_positions: Set[Tuple[int, int]] = set()
        attempts = 0
        
        while len(positions) < self.num_agents and attempts < MAX_POSITION_ATTEMPTS:
            position = self._generate_random_position()
            
            # Skip if position is already used
            if position in used_positions:
                attempts += 1
                continue
            
            # Skip if position is in any place and we want to avoid it
            if avoid_places and self._is_position_in_place(position):
                attempts += 1
                continue
            
            positions.append(position)
            used_positions.add(position)
            attempts += 1
        
        # If we couldn't generate enough positions avoiding places, fill remaining
        if len(positions) < self.num_agents:
            logger.warning(
                f"Could only generate {len(positions)} unique positions avoiding places. "
                "Using all available space."
            )
            while len(positions) < self.num_agents:
                position = self._generate_random_position()
                if position not in used_positions:
                    positions.append(position)
                    used_positions.add(position)
        
        return positions
    
    def initialize_agents(self):
        """Initialize agents inside lunar bases"""
        logger.info(f"Initializing {self.num_agents} agents ({self.num_large} large, {self.num_small} small)...")

        # Retrieve base configurations
        bases = [p for p in self.places if p.get('type') == 'lunar_base']
        if len(bases) < 2:
            bases = self.places  # Fallback if no lunar bases found

        def random_in_base(base):
            """Return a random position within the given base."""
            import random
            cx = base['center_x']
            cy = base['center_y']
            hs = base.get('half_size', 5) - 1
            return (
                random.randint(cx - hs, cx + hs),
                random.randint(cy - hs, cy + hs)
            )

        for i in range(self.num_agents):
            lumis_type = "large" if i < self.num_large else "small"

            # Large Lumis: one per base. Small Lumis: distributed alternately across bases.
            if lumis_type == "large":
                base = bases[i % len(bases)]
            else:
                base = bases[(i - self.num_large) % len(bases)]

            pos = random_in_base(base)

            agent = Agent(
                agent_id=i,
                initial_position=pos,
                llm_client=self.llm_client,
                communication_radius=self.communication_radius,
                half_space_size=self.half_space_size,
                places=self.places,
                num_agents=self.num_agents,
                memory_limit=self.memory_limit,
                memory_size=self.memory_size,
                message_history_limit=self.message_history_limit,
                message_context_size=self.message_context_size,
                lumis_type=lumis_type
            )
            # Assign home base for large Lumis (L0 → base_alpha, L1 → base_beta)
            if lumis_type == "large":
                agent.home_base = base['name']
            # Randomize birth_step for initial agents to prevent synchronized reproduction bursts.
            # Spread across the full maturity window (60 steps).
            import random as _random
            agent.birth_step = _random.randint(-59, 0)
            agent.update_state()
            self.agents.append(agent)
            logger.info(f"  Lumis {i} ({lumis_type}) initialized at {pos} in {base['name']}")

        logger.info("Agents initialized successfully")
    
    def get_agents_in_place(self, place_name: Optional[str] = None) -> List[Agent]:
        """Get list of agents currently in a specific place or any place"""
        if place_name:
            return [agent for agent in self.agents if agent.current_place == place_name]
        return [agent for agent in self.agents if agent.in_place]
    
    def get_place_status(self, place_name: Optional[str] = None) -> Dict:
        """Get current place status for a specific place or overall status"""
        if place_name:
            # Get status for a specific place
            place_config = next((p for p in self.places if p['name'] == place_name), None)
            if not place_config:
                raise ValueError(f"Place '{place_name}' not found")
            
            agents_in_place = len(self.get_agents_in_place(place_name))
            capacity = place_config['capacity']
            occupancy_rate = agents_in_place / capacity

            return {
                "place_name": place_name,
                "agents_in_place": agents_in_place,
                "capacity": capacity,
                "occupancy_rate": occupancy_rate,
            }
        else:
            # Get overall status (all places combined)
            agents_in_place = len(self.get_agents_in_place())
            occupancy_rate = agents_in_place / self.num_agents
            
            # Get per-place status (optimized: calculate directly instead of recursive calls)
            place_statuses = {}
            for place in self.places:
                place_agents = len(self.get_agents_in_place(place['name']))
                place_capacity = place['capacity']
                place_occupancy_rate = place_agents / place_capacity

                place_statuses[place['name']] = {
                    "place_name": place['name'],
                    "agents_in_place": place_agents,
                    "capacity": place_capacity,
                    "occupancy_rate": place_occupancy_rate,
                }
            
            return {
                "agents_in_place": agents_in_place,
                "occupancy_rate": occupancy_rate,
                "places": place_statuses
            }
    
    def get_fire_info_for_agent(self, agent: Agent) -> Optional[List[Dict]]:
        """Return list of perceived fire info dicts, or None if no fires perceived.

        Implements Model B: only agents within each fire's radius get that fire's data.
        Agents outside all radii must learn about fires through messages.
        """
        if not self.fire_states:
            return None

        perceived = []
        for fire in self.fire_states:
            if not fire.get('active'):
                continue
            fire_pos = fire['position']
            distance = agent.distance_to(fire_pos)
            if distance <= fire['radius']:
                perceived.append({
                    'name': fire['name'],
                    'fire_position': fire_pos,
                    'intensity': fire['intensity'],
                    'radius': fire['radius'],
                    'agent_distance': round(distance, 2),
                })
        return perceived if perceived else None

    def step_simulation(self):
        """Execute one simulation step

        New order:
        1. All agents decide messages (without position information)
        2. Messages are sent to nearby agents (using decision-time positions)
        3. All agents decide actions (with position information and message content)
        4. Agents move to new positions
        """
        self.step += 1

        # Day/night cycle: 30-step period (15 day + 15 night).
        # cycle_pos starts at 0; offset by -1 + night_length so steps 1-15 are daytime.
        cycle_pos = (self.step - 1 + self.night_length) % self.night_period
        currently_night = cycle_pos < self.night_length

        if currently_night and not self.fire_states:
            fire_state = {
                'name': 'lunar_night',
                'position': (0, 0),
                'intensity': self.night_intensity,
                'radius': self.night_radius,
                'start_step': self.step,
                'active': True,
            }
            self.fire_states = [fire_state]
            logger.info(f"LUNAR NIGHT started at step {self.step}")
        elif not currently_night and self.fire_states:
            self.fire_states = []
            logger.info(f"LUNAR NIGHT ended at step {self.step}")

        self.is_night = currently_night

        # Update agent states
        for agent in self.agents:
            agent.update_state(self.places)

        # Update Lumis energy and emotion variables
        light_level = 0.05 if self.fire_states else 0.9
        for agent in self.agents:
            nearby = agent.get_nearby_agents(self.agents)
            # Detect emotionally significant events before updating valence
            agent.detect_valence_events(nearby, self.step)
            agent.update_energy(light_level, nearby)

        # Solar flare processing
        self.active_flare = None
        self.flare_warning = None

        for fc in self.solar_flare_configs:
            warning_steps = fc.get('warning_steps', 2)
            warn_start = fc['start_step'] - warning_steps
            flare_end = fc['start_step'] + fc['duration']

            if fc['start_step'] <= self.step < flare_end:
                self.active_flare = fc
                for agent in self.agents:
                    if not agent.in_place:
                        base_damage = fc['damage'] / fc['duration']
                        if agent.is_sheltering:
                            damage = base_damage * 0.15  # Shelter reduces flare damage by 85% (regolith shielding)
                            logger.info(
                                f"Step {self.step}: SOLAR FLARE '{fc['name']}' hit Lumis {agent.id} "
                                f"(sheltering, -85%). energy={agent.energy - damage:.3f}"
                            )
                        else:
                            damage = base_damage
                            logger.info(
                                f"Step {self.step}: SOLAR FLARE '{fc['name']}' hit Lumis {agent.id} "
                                f"(outside). energy={agent.energy - damage:.3f}"
                            )
                        agent.energy = max(0.0, agent.energy - damage)
                    # Agents inside base take no flare damage
                break
            elif warn_start <= self.step < fc['start_step']:
                steps_until = fc['start_step'] - self.step
                self.flare_warning = {
                    'name': fc['name'],
                    'steps_until': steps_until,
                    'electromagnetic_noise': round(1.0 - (steps_until / warning_steps) * 0.5, 2)
                }
                logger.info(
                    f"Step {self.step}: FLARE WARNING '{fc['name']}' - "
                    f"{steps_until} step(s) until impact. "
                    f"electromagnetic_noise={self.flare_warning['electromagnetic_noise']}"
                )
                break

        # Background radiation: constant low damage outside base (realistic lunar surface ~60μSv/h)
        if not self.active_flare:
            for agent in self.agents:
                if not agent.in_place:
                    is_night = self.is_night
                    sheltering = getattr(agent, 'is_sheltering', False)
                    if sheltering:
                        # Sheltering: radiation and thermal fatigue both reduced to 1/4
                        agent.energy = max(0.0, agent.energy - 0.002)  # Radiation at 1/4 strength
                        if is_night:
                            agent.energy = max(0.0, agent.energy - 0.0008)  # Thermal fatigue at 1/4 strength
                    else:
                        # Exposed outside: full radiation and thermal damage
                        agent.energy = max(0.0, agent.energy - 0.008)  # Background radiation
                        if is_night:
                            agent.energy = max(0.0, agent.energy - 0.003)  # Nighttime thermal fatigue

        # Energy processing during child-rearing
        for agent in self.agents:
            if not agent.reproducing:
                continue
            if agent.reproduction_type == "clone":
                prep = 30  # Preparation period (same for large and small)
            else:
                prep = 60 if agent.lumis_type == "large" else 30  # SEXUAL_PREP
            rearing_start = agent.reproduction_start_step + prep
            in_rearing = self.step >= rearing_start
            if in_rearing:
                if agent.is_gestating:
                    # Gestating parent: energy decay compensation
                    agent.energy = min(agent.energy_capacity, agent.energy + 0.005)
                elif agent.reproduction_type == "sexual_support":
                    # Supporting parent: bonus energy recovery
                    agent.energy = min(agent.energy_capacity, agent.energy + 0.01)

        # Large Lumis during child-rearing: restrict movement outside base
        # Movement is handled within Phase 2

        # Death processing: remove agents with energy <= 0 (before message phase)
        dead_agents = [a for a in self.agents if a.is_dead]
        for dead in dead_agents:
            nearby = [a for a in self.agents if a.id != dead.id and dead.distance_to(a.position) <= dead.communication_radius * 2]
            dead.transfer_memory(nearby)
            logger.info(f"Step {self.step}: Lumis {dead.id} ({dead.lumis_type}) has died. energy={dead.energy:.3f}")
            self.agents.remove(dead)

        # Check for total extinction
        if len(self.agents) == 0:
            logger.info(f"Step {self.step}: All Lumis have died. Simulation ending.")
            self.step = self.duration  # Force end simulation
            return

        # Phase 1: Collect action decisions (LLM, based on previous step messages)
        action_decisions = []
        memory_reasoning_records = []  # Batch records for efficient I/O
        for agent in self.agents:
            nearby_agents = agent.get_nearby_agents(self.agents)
            agent_place_status = None
            if agent.in_place and agent.current_place:
                agent_place_status = self.get_place_status(agent.current_place)
            fire_info = self.get_fire_info_for_agent(agent)
            # Pass flare info to agent for decision making
            agent._active_flare = self.active_flare
            agent._flare_warning = getattr(self, 'flare_warning', None)
            # Record valence before action (used for delta calculation in introspection)
            agent._valence_before_action = agent.valence
            # Pass the 3 most recent introspection entries to the action decision prompt
            recent_intro = "\n".join(f"  - {s}" for s in agent.introspection[-3:]) if agent.introspection else ""
            action_decision = agent.decide_action(agent_place_status, nearby_agents, self.step, recent_intro, fire_info=fire_info)
            action_decisions.append((agent, action_decision))

            # Collect memory and reasoning records for batch writing
            memory_reasoning_records.append({
                "step": self.step,
                "id": agent.id,
                "memory": action_decision.get('memory', ''),
                "reasoning": action_decision.get('reasoning', '')
            })

        # Write all memory/reasoning records in batch (more efficient than individual writes)
        self._log_memory_reasoning_batch(memory_reasoning_records)

        # Phase 1.5: Instinct layer (body reflexes — fire before LLM reasoning)
        # Equivalent to brainstem/spinal reflexes in humans — bypasses LLM reasoning entirely.
        # Rules:
        #   1. Flare warning (noise >= 0.7) → auto-shelter
        #   2. Active flare → maintain shelter
        #   3. Flare ended → release shelter
        #   4. While sheltering: all actions disabled
        #   5. Large Lumis: energy >= 1.3 → override with share/greet
        #                    energy < 0.8 → override with collect

        # Collect override logic for large and small Lumis
        new_action_decisions = []
        for agent, action_decision in action_decisions:

            # --- REPRODUCTION / NEWBORN IMMOBILITY REFLEX ---
            # Reproducing parents: no movement allowed. Only rest/stay/greet (large, partner, children).
            if getattr(agent, 'reproducing', False):
                action = action_decision.get('action', '')
                if action == 'move':
                    # Determine if agent can greet (large Lumis, partner, or own children nearby)
                    partner_id = getattr(agent, 'reproduction_partner_id', None)
                    # child_ids: reverse lookup via parent_ids on other agents
                    my_child_ids = {a.id for a in self.agents if agent.id in getattr(a, 'parent_ids', [])}
                    nearby = agent.get_nearby_agents(self.agents)
                    allowed_greet_ids = (
                        {a.id for a in nearby if a.lumis_type == 'large'} |
                        ({partner_id} if partner_id else set()) |
                        my_child_ids
                    )
                    can_greet = bool(allowed_greet_ids & {a.id for a in nearby})
                    if can_greet:
                        action_decision = {'action': 'greet', 'direction': None, 'reasoning': '[REFLEX] reproducing→greet(allowed)', 'memory': ''}
                        logger.info(f"Step {self.step}: [REFLEX] Lumis {agent.id} reproducing, move→greet")
                    else:
                        action_decision = {'action': 'rest', 'direction': None, 'reasoning': '[REFLEX] reproducing→rest', 'memory': ''}
                        logger.info(f"Step {self.step}: [REFLEX] Lumis {agent.id} reproducing, move→rest")
                new_action_decisions.append((agent, action_decision))
                continue

            # Newborns (age <= 30): inside base, restrict to rest/stay/greet(large+parents+siblings only)
            age = self.step - getattr(agent, 'birth_step', 0)
            if age <= 30 and getattr(agent, 'parent_ids', []):
                action = action_decision.get('action', '')
                if action == 'move':
                    parent_ids = set(getattr(agent, 'parent_ids', []))
                    nearby = agent.get_nearby_agents(self.agents)
                    # Find siblings: agents who share at least one parent
                    sibling_ids = {
                        a.id for a in self.agents
                        if a.id != agent.id and set(getattr(a, 'parent_ids', [])) & parent_ids
                    }
                    allowed_greet_ids = (
                        {a.id for a in nearby if a.lumis_type == 'large'} |
                        (parent_ids & {a.id for a in nearby}) |
                        (sibling_ids & {a.id for a in nearby})
                    )
                    can_greet = bool(allowed_greet_ids)
                    if can_greet:
                        action_decision = {'action': 'greet', 'direction': None, 'reasoning': '[REFLEX] newborn→greet(allowed)', 'memory': ''}
                        logger.info(f"Step {self.step}: [REFLEX] Lumis {agent.id} newborn(age={age}), move→greet")
                    else:
                        action_decision = {'action': 'rest', 'direction': None, 'reasoning': '[REFLEX] newborn→rest', 'memory': ''}
                        logger.info(f"Step {self.step}: [REFLEX] Lumis {agent.id} newborn(age={age}), move→rest")
            # --- END REPRODUCTION / NEWBORN IMMOBILITY REFLEX ---

            # --- NEGATIVE TONE REFLEX ---
            # 3+ consecutive negative introspections → bias toward greet (reach out, don't withdraw)
            if (getattr(agent, '_consecutive_negative', 0) >= 3
                    and action_decision.get('action') not in ('greet', 'share', 'rest')):
                nearby = agent.get_nearby_agents(self.agents)
                if nearby:
                    action_decision = {'action': 'greet', 'direction': None,
                                       'reasoning': f'[REFLEX] negative_tone({agent._consecutive_negative})→greet', 'memory': ''}
                    logger.info(f"Step {self.step}: [REFLEX] Lumis {agent.id} negative_tone={agent._consecutive_negative} → greet")
                else:
                    action_decision = {'action': 'rest', 'direction': None,
                                       'reasoning': f'[REFLEX] negative_tone({agent._consecutive_negative})→rest(no nearby)', 'memory': ''}
            # --- END NEGATIVE TONE REFLEX ---
            # 小型：基地内でcollectを選んだ場合 → greet → rest に差し替え
            # 理由：光合成は外でしかできない。基地内はrest/greet/shareの場所。
            if agent.lumis_type == 'small' and agent.in_place and not agent.reproducing:
                action = action_decision.get('action', '')
                if action == 'collect':
                    nearby = agent.get_nearby_agents(self.agents)
                    can_greet = (
                        nearby and
                        getattr(agent, 'valence', 0) >= 0.5
                    )
                    if can_greet:
                        action_decision = {'action': 'greet', 'direction': None, 'reasoning': '[REFLEX] collect→greet in base', 'memory': ''}
                        logger.info(f"Step {self.step}: [REFLEX] Lumis {agent.id}(small) collect in base → greet")
                    else:
                        action_decision = {'action': 'rest', 'direction': None, 'reasoning': '[REFLEX] collect→rest in base', 'memory': ''}
                        logger.info(f"Step {self.step}: [REFLEX] Lumis {agent.id}(small) collect in base → rest")

            if agent.lumis_type == 'large' and not getattr(agent, 'is_sheltering', False) and not agent.reproducing:
                # Retired large Lumis are free — no action override (they choose for themselves)
                if not getattr(agent, 'is_retired', False):
                    action = action_decision.get('action', '')
                    if agent.energy >= 1.3 and action in ('collect', 'rest', 'stay'):
                        nearby = agent.get_nearby_agents(self.agents)
                        # Share if a nearby Lumis is low on energy; otherwise greet
                        hungry_nearby = [a for a in nearby if a.energy < 0.8]
                        if hungry_nearby:
                            action_decision = {'action': 'share', 'direction': None, 'reasoning': '[REFLEX] energy full, hungry neighbor', 'memory': ''}
                            logger.info(f"Step {self.step}: [REFLEX] Lumis {agent.id}(large) energy={agent.energy:.2f}>=1.3 → share (hungry neighbor)")
                        else:
                            action_decision = {'action': 'greet', 'direction': None, 'reasoning': '[REFLEX] energy full, no hungry neighbor', 'memory': ''}
                            logger.info(f"Step {self.step}: [REFLEX] Lumis {agent.id}(large) energy={agent.energy:.2f}>=1.3 → greet")
                    elif agent.energy < 0.8 and action not in ('collect', 'shelter', 'move'):
                        action_decision = {'action': 'collect', 'direction': None, 'reasoning': '[REFLEX] energy low', 'memory': ''}
                        logger.info(f"Step {self.step}: [REFLEX] Lumis {agent.id}(large) energy={agent.energy:.2f}<0.8 → collect")
            new_action_decisions.append((agent, action_decision))
        action_decisions = new_action_decisions

        flare_warn = getattr(self, 'flare_warning', None)
        flare_active = self.active_flare is not None

        for agent in self.agents:
            if agent.in_place:
                # Inside base: full protection from flares — release shelter if agent is inside
                agent.is_sheltering = False
                agent.shelter_cooldown = 0
                continue

            if flare_active:
                # Active flare damage ongoing — maintain shelter (do not release)
                if not getattr(agent, 'is_sheltering', False):
                    agent.is_sheltering = True
                    agent.shelter_cooldown = 999  # Hold until flare ends
                    logger.info(
                        f"Step {self.step}: [REFLEX] Lumis {agent.id} forced into shelter (flare active)"
                    )
                else:
                    agent.shelter_cooldown = 999  # Reset each step to maintain shelter
            elif flare_warn and flare_warn['electromagnetic_noise'] >= 0.7:
                # Flare warning signal → shelter if not already sheltering
                if not getattr(agent, 'is_sheltering', False):
                    SHELTER_DISTANCE_THRESHOLD = 2
                    (ax, ay), (bx, by) = self.base_centers
                    dist_alpha = abs(agent.position[0] - ax) + abs(agent.position[1] - ay)
                    dist_beta  = abs(agent.position[0] - bx) + abs(agent.position[1] - by)
                    min_dist = min(dist_alpha, dist_beta)

                    if min_dist <= SHELTER_DISTANCE_THRESHOLD:
                        # Base is close → dash inside
                        if dist_alpha <= dist_beta:
                            dx, dy = ax - agent.position[0], ay - agent.position[1]
                        else:
                            dx, dy = bx - agent.position[0], by - agent.position[1]
                        direction = ('left' if dx < 0 else 'right') if abs(dx) >= abs(dy) else ('down' if dy < 0 else 'up')
                        agent.move(direction)
                        agent.move(direction)  # 2 moves per step
                        logger.info(
                            f"Step {self.step}: [REFLEX] Lumis {agent.id} fled toward base "
                            f"(noise={flare_warn['electromagnetic_noise']}, dist={min_dist:.1f}) → {direction}"
                        )
                    else:
                        # Too far from base → shelter in place
                        agent.is_sheltering = True
                        agent.shelter_cooldown = 999
                        logger.info(
                            f"Step {self.step}: [REFLEX] Lumis {agent.id} sheltered in place "
                            f"(noise={flare_warn['electromagnetic_noise']}, dist={min_dist:.1f})"
                        )
            else:
                # No flare, no warning → release shelter
                if getattr(agent, 'is_sheltering', False):
                    agent.is_sheltering = False
                    agent.shelter_cooldown = 0
                    logger.info(
                        f"Step {self.step}: [REFLEX] Lumis {agent.id} emerged from shelter (flare ended)"
                    )

        # Capacity overflow eviction: daytime only.
        # Priority to stay inside: reproducing parents and newborns (age <= 30 steps).
        # At night, all Lumis stay inside — no eviction (a 5cm organism should not be outside on the lunar night).
        if not self.is_night:
            for place in self.places:
                capacity = place['capacity']
                place_name = place['name']
                place_center = (place['center_x'], place['center_y'])
                half_size = place['half_size']

                agents_in = [a for a in self.agents if a.in_place and a.current_place == place_name]
                overflow = len(agents_in) - capacity
                if overflow <= 0:
                    continue  # Within capacity — no eviction needed

                # Protected from eviction: reproducing parents and newborns
                def is_protected(a):
                    if getattr(a, 'reproducing', False):
                        return True
                    age = self.step - getattr(a, 'birth_step', 0)
                    if age <= 30 and getattr(a, 'parent_ids', []):
                        return True
                    return False

                candidates = [a for a in agents_in if not is_protected(a)]
                # Sort by energy descending; evict the overflow count
                candidates.sort(key=lambda a: a.energy, reverse=True)
                to_evict = candidates[:overflow]

                for agent in to_evict:
                    # Push agent outside the base boundary
                    cx, cy = place_center
                    # Move agent away from base center
                    dx = agent.position[0] - cx
                    dy = agent.position[1] - cy
                    if dx == 0 and dy == 0:
                        dx = 1  # Default direction if agent is at exact center
                    # Determine direction away from base
                    if abs(dx) >= abs(dy):
                        direction = 'right' if dx >= 0 else 'left'
                    else:
                        direction = 'up' if dy >= 0 else 'down'
                    # Move to half_size+2 distance from center
                    steps_needed = half_size + 2
                    for _ in range(steps_needed):
                        agent.move(direction)
                    agent.update_state(self.places)
                    logger.info(
                        f"Step {self.step}: [CAPACITY] Lumis {agent.id} moved outside "
                        f"{place_name} (overflow={overflow}, energy={agent.energy:.2f})"
                    )

        # Homing reflex: during night, guide all outside agents toward their home base.
        # Skip agents already responding to flare warnings.
        if self.is_night and not flare_active and not (flare_warn and flare_warn['electromagnetic_noise'] >= 0.7):
            (ax, ay), (bx, by) = self.base_centers
            for agent in self.agents:
                if agent.in_place or getattr(agent, 'is_sheltering', False):
                    continue

                dist_alpha = abs(agent.position[0] - ax) + abs(agent.position[1] - ay)
                dist_beta  = abs(agent.position[0] - bx) + abs(agent.position[1] - by)

                if dist_alpha <= dist_beta:
                    dx, dy = ax - agent.position[0], ay - agent.position[1]
                    min_dist = dist_alpha
                else:
                    dx, dy = bx - agent.position[0], by - agent.position[1]
                    min_dist = dist_beta

                # Diagonal movement: use both X and Y axes simultaneously for shortest path home
                if dx != 0 and dy != 0:
                    x_dir = 'right' if dx > 0 else 'left'
                    y_dir = 'up' if dy > 0 else 'down'
                    direction = ('northeast' if x_dir == 'right' else 'northwest') if y_dir == 'up' \
                                else ('southeast' if x_dir == 'right' else 'southwest')
                elif dx != 0:
                    direction = 'right' if dx > 0 else 'left'
                else:
                    direction = 'up' if dy > 0 else 'down'
                agent.move(direction)
                agent.move(direction)  # 2 moves per step
                logger.info(
                    f"Step {self.step}: [REFLEX] Lumis {agent.id} heads home for the night (dist={min_dist})"
                )

        # 生後30step以内の子供は昼夜問わず基地内待機（メンテナンス期間）
        (ax, ay), (bx, by) = self.base_centers
        for agent in self.agents:
            if agent.in_place or getattr(agent, 'is_sheltering', False):
                continue
            if not getattr(agent, 'parent_ids', []):
                continue  # 子供(parent_idsあり)のみ対象
            age = self.step - getattr(agent, 'birth_step', 0)
            if age > 30:
                continue  # 生後30stepを超えたら自由

            dist_alpha = abs(agent.position[0] - ax) + abs(agent.position[1] - ay)
            dist_beta  = abs(agent.position[0] - bx) + abs(agent.position[1] - by)
            if dist_alpha <= dist_beta:
                dx, dy = ax - agent.position[0], ay - agent.position[1]
            else:
                dx, dy = bx - agent.position[0], by - agent.position[1]
            # Diagonal movement toward home base
            if dx != 0 and dy != 0:
                x_dir = 'right' if dx > 0 else 'left'
                y_dir = 'up' if dy > 0 else 'down'
                direction = ('northeast' if x_dir == 'right' else 'northwest') if y_dir == 'up' \
                            else ('southeast' if x_dir == 'right' else 'southwest')
            elif dx != 0:
                direction = 'right' if dx > 0 else 'left'
            else:
                direction = 'up' if dy > 0 else 'down'
            agent.move(direction)
            agent.move(direction)
            logger.info(
                f"Step {self.step}: [REFLEX] Lumis {agent.id} returns to base (newborn maintenance, age={age})"
            )

        # Phase 2: Execute movement (after actions are decided and reflexes applied)
        # シェルター中・複製準備中の個体はLLMの全行動を無効化
        for agent, action_decision in action_decisions:
            if getattr(agent, 'is_sheltering', False):
                continue  # シェルター中は何もできない
            if getattr(agent, 'reproducing', False):
                # 大型の子育て期間中：基地内移動のみ許可、外出不可
                rearing_start = agent.reproduction_start_step + (
                    30 if agent.reproduction_type == "clone"
                    else 60  # SEXUAL_PREP_LARGE
                )
                in_rearing = (agent.lumis_type == "large" and self.step >= rearing_start)
                if in_rearing:
                    # 基地内移動のみ許可
                    action = action_decision['action']
                    if action == 'move' and action_decision['direction']:
                        # 移動先が基地外になる場合は無効化
                        dx, dy = {'up': (0,1), 'down': (0,-1), 'left': (-1,0), 'right': (1,0)}.get(action_decision['direction'], (0,0))
                        new_pos = (agent.position[0] + dx, agent.position[1] + dy)
                        from utils import get_place_at_position
                        if get_place_at_position(new_pos, self.places) is not None:
                            agent.move(action_decision['direction'])
                    continue
                else:
                    continue  # 出産準備中は全行動不可

            action = action_decision['action']
            agent.is_resting = False  # デフォルトはFalse、restの時のみTrueにする
            if action == 'shelter':
                agent.is_sheltering = True
                agent.shelter_cooldown = 999
                logger.info(f"Step {self.step}: Lumis {agent.id} built shelter (regolith). Flare damage -85%.")
            elif action == 'rest':
                # restアクション：その場で光合成に集中（回復量はupdate_energyのrecoveryでカバー済み）
                agent.is_resting = True
            elif action == 'move' and action_decision['direction']:
                agent.move(action_decision['direction'])
                agent.move(action_decision['direction'])  # 1step=2歩
            elif action == 'greet':
                # 鏡のルール：自分のvalenceの状態が、familiarityという形で相手にも返ってくる
                targets = agent.get_nearby_agents(self.agents)
                if targets:
                    friendly = agent.valence >= 0.5  # 0.6→0.5に閾値を下げた
                    unpleasant = agent.valence <= 0.4
                    for other in targets:
                        agent.record_contact(other.id, unpleasant=unpleasant)
                        other.record_contact(agent.id, unpleasant=unpleasant)
                        if friendly:
                            other.valence = min(1.0, other.valence + 0.03)
                    tone = "friendly" if friendly else ("unpleasant" if unpleasant else "neutral")
                    logger.info(
                        f"Step {self.step}: Lumis {agent.id} greets "
                        f"{[o.id for o in targets]} (tone={tone}, valence={agent.valence:.2f})"
                    )
            elif action == 'share':
                # エネルギー分与：大型が基地内の小型にエネルギーを渡す
                # 大型以外でも選べるが、大型が基地内で使うのが主な想定
                SHARE_AMOUNT = 0.1
                targets = agent.get_nearby_agents(self.agents)
                # 基地内にいる、かつエネルギーが低い小型を優先
                if agent.in_place:
                    recipients = [a for a in targets if a.lumis_type == 'small' and a.energy < 0.8]
                else:
                    recipients = targets
                if recipients and agent.energy > SHARE_AMOUNT + 0.3:
                    # エネルギーが最も低い個体に渡す
                    recipient = min(recipients, key=lambda a: a.energy)
                    agent.energy -= SHARE_AMOUNT
                    recipient.energy = min(recipient.energy_capacity, recipient.energy + SHARE_AMOUNT)
                    logger.info(
                        f"Step {self.step}: Lumis {agent.id} shares energy with Lumis {recipient.id} "
                        f"({SHARE_AMOUNT:.2f} transferred, recipient energy={recipient.energy:.2f})"
                    )

        # Update states after movement
        for agent in self.agents:
            agent.update_state(self.places)

        # Phase 2.5: Introspection phase (after action, before messaging).
        # LLM reviews existing introspection list and updates or appends.
        # Runs every 5 steps only (3x per day cycle, 3x per night cycle) to reduce LLM calls.
        action_decision_map = {agent.id: ad for agent, ad in action_decisions}
        introspection_map = {}  # agent.id -> latest introspection str
        run_introspection = (self.step % 5 == 0)
        for agent in self.agents:
            action_taken = action_decision_map.get(agent.id)
            valence_before = getattr(agent, '_valence_before_action', agent.valence)
            # Large Lumis introspect every step; small Lumis every 5 steps
            # Also introspect if birth note from PREVIOUS step is pending
            has_birth_note = bool(getattr(agent, '_recent_birth_note', '')) or bool(getattr(agent, '_birth_note_pending', ''))
            if agent.lumis_type == 'large' or run_introspection or has_birth_note:
                latest = agent.introspect(action_taken, self.step, valence_before)
                introspection_map[agent.id] = latest
                if latest:
                    logger.info(f"Step {self.step}: [INTROSPECT] Lumis {agent.id}: {latest[:100]}")
            else:
                introspection_map[agent.id] = agent.introspection[-1] if agent.introspection else ""

        # Phase 3: Message transmission (new design).
        # - Large Lumis: commune with the other large Lumis every step (cross-base deep sync).
        # - Small Lumis: no message if no nearby agents.
        # - Message = auto-generated header + latest introspection + greeting (LLM).

        # Large Lumis commune network — all large Lumis (parent and clone generations)
        large_agents = [a for a in self.agents if a.lumis_type == 'large']

        # Retirement check: if a large Lumis produced a clone child whose 30-step protection has ended,
        # mark the parent as retired (free to roam)
        for agent in large_agents:
            if not agent.is_retired and agent.clone_count > 0:
                # Find this agent's clone children
                clone_children = [
                    a for a in self.agents
                    if a.lumis_type == 'large'
                    and agent.id in getattr(a, 'parent_ids', [])
                ]
                for child in clone_children:
                    child_age = self.step - child.birth_step
                    if child_age >= 30:
                        agent.is_retired = True
                        # Pass home_base knowledge to child
                        if not child.home_base:
                            child.home_base = agent.home_base
                        logger.info(
                            f"Step {self.step}: [RETIRE] Lumis {agent.id} retired — "
                            f"Lumis {child.id} now tends {agent.home_base}"
                        )

        if len(large_agents) >= 2:
            # Commune between all pairs of large Lumis (parent + clone generations)
            communed_pairs = set()
            for agent in large_agents:
                for partner in large_agents:
                    if agent.id == partner.id:
                        continue
                    pair = tuple(sorted([agent.id, partner.id]))
                    if pair in communed_pairs:
                        continue
                    communed_pairs.add(pair)
                    action_taken = action_decision_map.get(agent.id)
                    latest_intro = introspection_map.get(agent.id, "")
                    commune_text = agent.decide_commune(partner, self.step, action_taken, latest_intro)
                    if commune_text:
                        act = action_taken.get('action', 'stay') if action_taken else 'stay'
                        location = (
                            f"in {agent.current_place}" if (agent.in_place and agent.current_place)
                            else f"({agent.position[0]}, {agent.position[1]})"
                        )
                        header = f"[Step {self.step}, {location}, energy={round(agent.energy, 2)}, action={act}]"
                        message_content = f"{header} {commune_text}"
                        partner.receive_message(agent.id, message_content, step=self.step)
                        self._log_message(
                            from_agent_id=agent.id,
                            to_agent_id=partner.id,
                            message=message_content,
                            reasoning=commune_text
                        )
                        logger.info(
                            f"Step {self.step}: [COMMUNE] Lumis {agent.id} to Lumis {partner.id}: {commune_text[:80]}"
                        )

        for agent in self.agents:
            nearby_agents = agent.get_nearby_agents(self.agents)
            if not nearby_agents:
                continue  # No message sent if no nearby Lumis

            action_taken = action_decision_map.get(agent.id)
            act = action_taken.get('action', 'stay') if action_taken else 'stay'
            direction = action_taken.get('direction', '') if action_taken else ''
            act_desc = act if not direction else f"{act} ({direction})"
            location = (
                f"in {agent.current_place}" if (agent.in_place and agent.current_place)
                else f"({agent.position[0]}, {agent.position[1]})"
            )

            # Auto-generated message header
            header = (
                f"[Step {self.step}, {location}, "
                f"energy={round(agent.energy, 2)}, action={act_desc}]"
            )

            # Latest introspection entry
            latest_intro = introspection_map.get(agent.id, "")
            intro_line = f" {latest_intro}" if latest_intro else ""

            # Determine target first (highest familiarity), then generate greeting
            # This ensures the greeting addresses the correct Lumis by name
            # Always pick one target: highest familiarity, or nearest if familiarity is tied at zero
            best_target = max(
                nearby_agents,
                key=lambda a: (agent.get_familiarity_score(a.id), -agent.distance_to(a.position))
            )
            target_id = best_target.id
            targets = [best_target]

            # LLM-generated greeting (target is now known before LLM call)
            greeting_result = agent.decide_greeting(
                nearby_agents, self.step, action_taken, latest_intro,
                target_id=target_id
            )
            greeting = greeting_result.get('greeting', '')

            # Assemble full message
            message_content = header + intro_line
            if greeting:
                message_content += f" {greeting}"

            if target_id is not None:
                logger.info(
                    f"Step {self.step}: Lumis {agent.id} sends message to Lumis {target_id} (directed): "
                    f"\"{message_content}\""
                )
            else:
                logger.info(
                    f"Step {self.step}: Lumis {agent.id} sends message to {len(targets)} nearby agent(s): "
                    f"\"{message_content}\""
                )
            for other_agent in targets:
                other_agent.receive_message(agent.id, message_content, step=self.step)
                self._log_message(
                    from_agent_id=agent.id,
                    to_agent_id=other_agent.id,
                    message=message_content,
                    reasoning=greeting_result.get('greeting', '')
                )

        # Phase 4: 複製（clone / sexual）- 準備期間方式
        import random as _random

        MATURITY_SMALL = 60        # 小型成熟期間
        MATURITY_LARGE = 180       # 大型成熟期間
        CLONE_COOLDOWN_SMALL = 60  # 小型クローンクールダウン
        CLONE_COOLDOWN_LARGE = 300 # 大型クローンクールダウン
        SEXUAL_COOLDOWN = 60       # Sexual reproductionクールダウン
        CLONE_PREP_SMALL = 30      # 小型クローン準備期間
        CLONE_PREP_LARGE = 30      # 大型クローン準備期間
        SEXUAL_PREP_SMALL = 30     # 小型有性生殖準備期間
        SEXUAL_PREP_LARGE = 60     # 大型有性生殖準備期間
        CHILD_REARING_STEPS = 30   # Child-rearing period (steps)

        flare_active = self.active_flare is not None
        fire_active = self.is_night

        new_agents = []

        # --- Phase 4a: 準備完了チェック → 誕生処理 ---
        for agent in list(self.agents):
            if not agent.reproducing:
                continue

            # 準備期間を計算
            if agent.reproduction_type == "clone":
                prep = CLONE_PREP_LARGE if agent.lumis_type == "large" else CLONE_PREP_SMALL
            else:  # sexual（産む側のみここに来る、小型のみ）
                prep = SEXUAL_PREP_SMALL

            elapsed = self.step - agent.reproduction_start_step
            if elapsed < prep:
                continue  # まだ準備中

            # 準備完了 → 誕生
            new_id = max(a.id for a in self.agents) + len(new_agents) + 1

            if agent.reproduction_type == "clone":
                child = Agent(
                    agent_id=new_id,
                    initial_position=tuple(agent.position),
                    llm_client=self.llm_client,
                    communication_radius=self.communication_radius,
                    half_space_size=self.half_space_size,
                    places=self.places,
                    num_agents=self.num_agents,
                    memory_limit=self.memory_limit,
                    memory_size=self.memory_size,
                    message_history_limit=self.message_history_limit,
                    message_context_size=self.message_context_size,
                    lumis_type=agent.lumis_type,
                )
                child.energy = 0.5
                child.birth_step = self.step
                child.memory = list(agent.memory)
                child.parent_ids = [agent.id]
                child.rearing_until_step = self.step + 30  # 子も30step薄ピンク表示
                agent.energy -= 0.2
                agent.rearing_until_step = self.step + 30  # 親も30step薄ピンク表示
                new_agents.append(child)
                location_label = agent.current_place if agent.in_place else f"outside ({agent.position[0]}, {agent.position[1]})"
                logger.info(
                    f"Step {self.step}: [CLONE] Lumis {new_id} born from Lumis {agent.id} "
                    f"({agent.lumis_type}) at {location_label}. memory={len(child.memory)} entries."
                )
                agent._recent_birth_note = f"Your clone, Lumis {new_id}, was just born. This is your child."
                agent._birth_note_pending = agent._recent_birth_note

            elif agent.reproduction_type == "sexual":
                # パートナーを探す
                partner = next((a for a in self.agents if a.id == agent.reproduction_partner_id), None)
                if partner:
                    # 両親の記憶を混ぜてシャッフルし、2人の子に分配する
                    combined = agent.memory + partner.memory
                    _random.shuffle(combined)
                    half = len(combined) // 2
                    memory_sets = [combined[:half], combined[half:]]

                    children = []
                    for i in range(2):
                        new_id_i = max(a.id for a in self.agents) + len(new_agents) + 1
                        child = Agent(
                            agent_id=new_id_i,
                            initial_position=(
                                (agent.position[0] + partner.position[0]) // 2,
                                (agent.position[1] + partner.position[1]) // 2
                            ),
                            llm_client=self.llm_client,
                            communication_radius=self.communication_radius,
                            half_space_size=self.half_space_size,
                            places=self.places,
                            num_agents=self.num_agents,
                            memory_limit=self.memory_limit,
                            memory_size=self.memory_size,
                            message_history_limit=self.message_history_limit,
                            message_context_size=self.message_context_size,
                            lumis_type=agent.lumis_type,
                        )
                        child.energy = 0.5
                        child.birth_step = self.step
                        child.rearing_until_step = self.step + 30
                        child.memory = memory_sets[i][:self.memory_limit]
                        child.parent_ids = [agent.id, partner.id]
                        new_agents.append(child)
                        children.append(child)

                    agent.energy -= 0.15
                    partner.energy -= 0.15
                    agent.rearing_until_step = self.step + 30
                    partner.rearing_until_step = self.step + 30
                    # 家族ができた喜び（人間でいう「家族ができた」体感）
                    agent.valence = min(1.0, agent.valence + 0.15)
                    partner.valence = min(1.0, partner.valence + 0.15)
                    logger.info(
                        f"Step {self.step}: [SEXUAL] Lumis {children[0].id} and Lumis {children[1].id} born from "
                        f"Lumis {agent.id} × Lumis {partner.id}. "
                        f"memory={len(children[0].memory)}/{len(children[1].memory)} entries (shuffled & split)."
                    )
                    child_ids = f"Lumis {children[0].id} and Lumis {children[1].id}"
                    agent._recent_birth_note = f"Your children {child_ids} were just born. Lumis {partner.id} is their other parent."
                    partner._recent_birth_note = f"Your children {child_ids} were just born. Lumis {agent.id} is their other parent."
                    agent._birth_note_pending = agent._recent_birth_note
                    partner._birth_note_pending = partner._recent_birth_note
                    # パートナーの準備フラグも解除
                    partner.reproducing = False
                    partner.reproduction_type = None
                    partner.reproduction_start_step = -1
                    partner.reproduction_partner_id = None
                    partner.sexual_count += 1
                    partner.last_reproduction_step = self.step

            # 繁殖回数カウントアップ
            if agent.reproduction_type == "clone":
                agent.clone_count += 1
            elif agent.reproduction_type == "sexual":
                agent.sexual_count += 1

            # 準備フラグをリセット
            agent.reproducing = False
            agent.reproduction_type = None
            agent.reproduction_start_step = -1
            agent.reproduction_partner_id = None
            agent.is_gestating = False
            agent.last_reproduction_step = self.step

        self.agents.extend(new_agents)

        # --- Phase 4b: 新規複製開始チェック ---
        # フレア中・夜中は新規複製を開始しない
        if not flare_active and not fire_active:
            for agent in list(self.agents):
                if agent.reproducing:
                    continue  # すでに準備中

                mature = (self.step - agent.birth_step) >= (MATURITY_LARGE if agent.lumis_type == "large" else MATURITY_SMALL)
                clone_cooldown = CLONE_COOLDOWN_LARGE if agent.lumis_type == "large" else CLONE_COOLDOWN_SMALL
                cooldown_ok = (self.step - agent.last_reproduction_step) >= clone_cooldown

                # --- clone複製開始 ---
                # 条件：energy≥0.8、arousal≤0.5、成熟済み、クールダウン完了、小型は生涯1回まで
                # 大型は基地内限定・回数制限なし、小型は外でも可・生涯1回まで
                location_ok = agent.in_place if agent.lumis_type == "large" else True
                clone_limit_ok = (agent.lumis_type == "large") or (agent.clone_count < 1)
                if (location_ok and
                        clone_limit_ok and
                        agent.energy >= 0.8 and
                        agent.arousal <= 0.5 and
                        mature and
                        cooldown_ok):
                    agent.reproducing = True
                    agent.reproduction_type = "clone"
                    agent.reproduction_start_step = self.step
                    prep = CLONE_PREP_LARGE if agent.lumis_type == "large" else CLONE_PREP_SMALL
                    location_label = agent.current_place if agent.in_place else f"outside ({agent.position[0]}, {agent.position[1]})"
                    logger.info(
                        f"Step {self.step}: [CLONE_START] Lumis {agent.id} ({agent.lumis_type}) "
                        f"begins clone prep at {location_label}. Will complete at step {self.step + prep}."
                    )
                    continue  # 同stepでsexualはしない

                # --- sexual複製開始（実験：ハードル激甘版） ---
                # 条件：energy≥0.5、valence≥0.5、familiarity≥0.1、成熟済み、クールダウン完了、生涯2回まで
                # サイズ同士のみ（大×大、小×小）、基地内外どちらでも可
                if (agent.lumis_type == "small" and
                        agent.sexual_count < 1 and
                        agent.valence >= 0.5 and
                        agent.energy >= 0.5 and
                        mature and
                        cooldown_ok and
                        not getattr(agent, 'is_sheltering', False)):
                    nearby = [
                        a for a in self.agents
                        if a.id != agent.id
                        and a.lumis_type == agent.lumis_type  # サイズ同士のみ
                        and not a.reproducing
                        and agent.distance_to(a.position) <= agent.communication_radius
                        and agent.get_familiarity_score(a.id) >= 0.1  # 激甘
                        and a.valence >= 0.5
                        and a.energy >= 0.5
                        and (self.step - a.birth_step) >= MATURITY_SMALL
                        and (self.step - a.last_reproduction_step) >= SEXUAL_COOLDOWN
                        and not getattr(a, 'is_sheltering', False)
                    ]
                    if nearby:
                        partner = max(nearby, key=lambda a: agent.get_familiarity_score(a.id))

                        # 産む側を決定：energyが多い方、同値なら番号が大きい方
                        if agent.energy > partner.energy:
                            gestating = agent
                            supporting = partner
                        elif partner.energy > agent.energy:
                            gestating = partner
                            supporting = agent
                        else:
                            gestating = agent if agent.id > partner.id else partner
                            supporting = partner if gestating == agent else agent

                        prep = SEXUAL_PREP_SMALL

                        gestating.reproducing = True
                        gestating.reproduction_type = "sexual"
                        gestating.reproduction_start_step = self.step
                        gestating.reproduction_partner_id = supporting.id
                        gestating.is_gestating = True

                        supporting.reproducing = True
                        supporting.reproduction_type = "sexual_support"
                        supporting.reproduction_start_step = self.step
                        supporting.reproduction_partner_id = gestating.id
                        supporting.is_gestating = False

                        # パートナーができた喜び（人間でいう「パートナーができた」体感）
                        gestating.valence = min(1.0, gestating.valence + 0.15)
                        supporting.valence = min(1.0, supporting.valence + 0.15)

                        loc = gestating.current_place if gestating.in_place else f"outside ({gestating.position[0]}, {gestating.position[1]})"
                        logger.info(
                            f"Step {self.step}: [SEXUAL_START] Lumis {gestating.id} (gestating) x "
                            f"Lumis {supporting.id} (supporting) at {loc}, "
                            f"familiarity={agent.get_familiarity_score(partner.id):.2f}. "
                            f"Will complete at step {self.step + prep}."
                        )
        
        # Record statistics
        agents_in_place = len(self.get_agents_in_place())
        overall_status = self.get_place_status()
        self.stats['place_occupancy'].append(overall_status['occupancy_rate'])
        self.stats['agents_in_place'].append(agents_in_place)
        self.stats['agents_outside_place'].append(self.num_agents - agents_in_place)
        
        # Record per-place statistics
        for place in self.places:
            place_status = self.get_place_status(place['name'])
            self.stats['places'][place['name']]['occupancy'].append(place_status['occupancy_rate'])
            self.stats['places'][place['name']]['agents_in_place'].append(place_status['agents_in_place'])
        
        # Record fire statistics: count agents within any active flare radius
        if self.fire_states:
            agents_in_any_fire = set()
            for fire in self.fire_states:
                if fire.get('active'):
                    for agent in self.agents:
                        if agent.distance_to(fire['position']) <= fire['radius']:
                            agents_in_any_fire.add(agent.id)
            self.stats['agents_in_fire_radius'].append(len(agents_in_any_fire))
        else:
            self.stats['agents_in_fire_radius'].append(0)

        # Store history
        self.history.append({
            'step': self.step,
            'place_status': overall_status,
            'agent_positions': [agent.position for agent in self.agents],
            'agents_in_place': [agent.id for agent in self.get_agents_in_place()],
            'fire_states': list(self.fire_states),
        })
        
        if self.step % LOG_INTERVAL == 0:
            place_info = ", ".join([
                f"{place['name']}: {self.get_place_status(place['name'])['agents_in_place']}"
                for place in self.places
            ])
            logger.info(
                f"Step {self.step}/{self.duration}: "
                f"{agents_in_place} agents in places ({place_info}), "
                f"{overall_status['occupancy_rate']:.1%} overall occupancy"
            )
    
    def run(self):
        """Run the full simulation"""
        logger.info("Starting simulation...")
        
        # Check Ollama connection
        if not self.llm_client.check_connection():
            logger.error("Cannot connect to Ollama. Please make sure Ollama is running.")
            return
        
        # Initialize agents
        self.initialize_agents()
        
        # Run simulation
        try:
            while self.step < self.duration:
                self.step_simulation()
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
        except Exception as e:
            logger.error(f"Error during simulation: {e}", exc_info=True)
        
        logger.info("Simulation completed")
    
    def get_statistics(self) -> Dict:
        """Get simulation statistics"""
        if not self.stats['place_occupancy']:
            return {}
        
        place_occupancy = np.array(self.stats['place_occupancy'])
        agents_in_place = np.array(self.stats['agents_in_place'])
        
        return {
            'mean_occupancy': float(np.mean(place_occupancy)),
            'std_occupancy': float(np.std(place_occupancy)),
            'mean_agents_in_place': float(np.mean(agents_in_place)),
            'max_agents_in_place': int(np.max(agents_in_place)),
            'min_agents_in_place': int(np.min(agents_in_place)),
            'total_steps': self.step
        }

