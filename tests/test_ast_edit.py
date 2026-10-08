"""Tests for LibCST locator edits: single-change minimal diffs only."""

import pytest

from healing.gitops.ast_edit import edit_locator, stable_rank

SOURCE = """from selenium.webdriver.common.by import By


def test_submit(driver):
    driver.find_element(By.ID, "login-submit").click()
"""


def test_edit_changes_only_failing_locator() -> None:
    new_src, diff = edit_locator(SOURCE, "login-submit", "login-submit-v2")
    assert '"login-submit-v2"' in new_src
    assert new_src.count("find_element") == 1
    assert "- " in diff and "+ " in diff
    assert "login-submit-v2" in diff


def test_refuses_zero_or_two_occurrences() -> None:
    with pytest.raises(ValueError):
        edit_locator(SOURCE, "nope", "x")
    with pytest.raises(ValueError):
        edit_locator(SOURCE + 'y = "login-submit"\n', "login-submit", "x")


def test_stable_locator_preference_order() -> None:
    assert stable_rank("data-testid=x") < stable_rank("role=button")
    assert stable_rank("role=button") < stable_rank("text=Buy")
    assert stable_rank("text=Buy") < stable_rank("//div[3]")
