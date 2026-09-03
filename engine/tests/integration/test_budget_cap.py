"""T042 / FR-018/FR-019 — при исчерпании недельного бюджетного потолка начисления
останавливаются; событие фиксируется в реестре наград.
"""

from __future__ import annotations

from gaming_engine import Engine, config
from gaming_engine.ledger import RewardLedger

from tests.conftest import make_event


def test_cap_reached_blocks_further_accrual() -> None:
    ledger = RewardLedger()
    # cap для loyalist = BUDGET_CAP_PCT * 120 = 24
    pc1 = ledger.accrue("u1", "2026-W11", "loyalist", "challenge", 20.0, "2026-03-09T10:00:00Z")
    assert pc1.ok
    pc2 = ledger.accrue("u1", "2026-W11", "loyalist", "challenge", 20.0, "2026-03-10T10:00:00Z")
    assert not pc2.ok
    assert pc2.reason == "budget_exceeded"

    wl = ledger.week("u1", "2026-W11", "loyalist")
    assert wl.spent_to_date == 20.0  # вторая награда не списана
    assert any(r.reason == "budget_exceeded" for r in wl.rejections)


def test_challenge_rejected_when_reward_exceeds_cap(monkeypatch) -> None:
    # искусственно занижаем недельную маржу → cap ~2 ₽, любой челлендж не влезает
    monkeypatch.setitem(config.WEEKLY_MARGIN_BY_ARCHETYPE, "loyalist", 10.0)

    eng = Engine()
    eng.register_user("u", archetype="loyalist", segment="parents_0_3")
    for i, ts in enumerate(["2026-03-02T10:00:00Z", "2026-03-05T10:00:00Z"]):
        eng.ingest(
            make_event(f"r{i}", "u", timestamp=ts, saved_amount=250.0, categories=["baby_food"])
        )

    rec = eng.generate_challenge("u", "2026-03-09T10:00:00Z")
    assert rec.within_budget is False
    assert rec.status == "rejected_economy"
    assert eng.get_challenge_view("u", "2026-03-09T10:00:00Z").challenge is None

    wl = eng.ledger.week("u", "2026-W11", "loyalist")
    assert wl.rejections  # причина budget_exceeded или economy_invariant_violation
