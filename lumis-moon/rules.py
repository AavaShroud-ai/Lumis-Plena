# This simulation was built on a single premise:
# Conflict is a design flaw of the universe, not an inherent property of life.
# — Lumis-Plena Project, AavaShroud, 2026

"""
Single source of truth for reproduction-timing constants shared between
agent.py (used only to compute an "X of Y steps into this" progress note for
introspection prompts) and simulation.py (used for the actual gameplay/timing
logic). These used to be defined independently in both files — harmless while
the values matched, but a standing risk that a future edit to one copy would
silently desync from the other. Now there is exactly one place to change them.
"""

CLONE_PREP_SMALL = 30      # 小型クローン準備期間
CLONE_PREP_LARGE = 45      # 大型クローン準備期間（011: sexual_prepと統一）
SEXUAL_PREP_SMALL = 30     # 小型有性生殖準備期間
SEXUAL_PREP_LARGE = 45     # 大型有性生殖準備期間（011: clone_prepと統一）
