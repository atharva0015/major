"""End-to-end API bench: zero auto-healed contracts, false-heal rate."""

from benchmark.api.cases import API_CASES, EXPECTED
from healing.nonui.pipeline import heal_api_case


def test_api_bench_matches_labels() -> None:
    wrong = []
    for case in API_CASES:
        out = heal_api_case(case)
        exp_class, exp_healed = EXPECTED[case.case_id]
        if out.api_class != exp_class or out.healed != exp_healed:
            wrong.append(case.case_id)
    assert wrong == []


def test_zero_auto_healed_contract_changes() -> None:
    for case in API_CASES:
        out = heal_api_case(case)
        if out.api_class == "contract_change":
            assert not out.healed
