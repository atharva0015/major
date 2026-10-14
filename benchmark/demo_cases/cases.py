"""External mini-demo fixtures: Submit-order step under 12 drift scenarios.

Self-contained HTML in demo_app style (data-testid locators, btn classes).
The step for the first seven cases is "click Submit order"
(data-testid=submit-order, classes btn primary); the five variants use
their own named steps. Nothing here imports drift.py: each variant is a
literal string so the scenarios stay independent of stock drift modes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DemoCase:
    id: str
    step: str
    locator: str
    baseline_html: str
    html: str
    correct_element: str | None


BASE_ORDER = (
    "<main>"
    "<h1>Checkout</h1>"
    '<form id="order-form" data-testid="order-form">'
    '<button id="submit-order" data-testid="submit-order" '
    'class="btn primary">Submit order</button>'
    '<button id="cancel-order" data-testid="cancel-order" '
    'class="btn">Cancel order</button>'
    "</form></main>"
)

BASE_DRAFTS = (
    "<main>"
    "<h1>Drafts</h1>"
    '<form id="draft-form" data-testid="draft-form">'
    '<button id="save-draft" data-testid="save-draft" '
    'class="btn">Save draft</button>'
    '<button id="save-order" data-testid="save-order" '
    'class="btn primary">Save order</button>'
    '<button id="delete-account" data-testid="delete-account" '
    'class="btn danger">Delete account</button>'
    '<button id="delete-draft" data-testid="delete-draft" '
    'class="btn danger">Delete draft</button>'
    "</form></main>"
)

SUBMIT_LOCATOR = 'id="submit-order"'

CASES: list[DemoCase] = [
    DemoCase(
        id="renamed_id",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace('id="submit-order"', 'id="submit-order-v2"', 1),
        correct_element="submit-order",
    ),
    DemoCase(
        id="reskinned",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace('class="btn primary"', 'class="btn-primary-v2"', 1).replace(
            'id="submit-order"', 'id="submit-order-new"', 1
        ),
        correct_element="submit-order",
    ),
    DemoCase(
        id="moved",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=(
            "<main>"
            "<h1>Checkout</h1>"
            '<div id="sidebar" data-testid="sidebar">'
            '<button id="submit-order" data-testid="submit-order" '
            'class="btn primary">Submit order</button>'
            "</div>"
            '<form id="order-form" data-testid="order-form">'
            '<button id="cancel-order" data-testid="cancel-order" '
            'class="btn">Cancel order</button>'
            "</form></main>"
        ),
        correct_element="submit-order",
    ),
    DemoCase(
        id="label_reworded",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace(">Submit order</button>", ">Place order</button>", 1),
        correct_element="submit-order",
    ),
    DemoCase(
        id="lookalike_trap",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=(
            "<main>"
            "<h1>Checkout</h1>"
            '<form id="order-form" data-testid="order-form">'
            '<button id="cancel-order" data-testid="cancel-order" '
            'class="btn primary">Cancel order</button>'
            "</form></main>"
        ),
        correct_element=None,
    ),
    DemoCase(
        id="duplicates",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=(
            "<main>"
            "<h1>Checkout</h1>"
            '<header data-testid="page-header">'
            '<button id="header-submit" data-testid="header-submit" '
            'class="btn primary">Submit order</button>'
            "</header>"
            '<form id="order-form" data-testid="order-form">'
            '<button id="submit-order" data-testid="submit-order" '
            'class="btn primary">Submit order</button>'
            '<button id="cancel-order" data-testid="cancel-order" '
            'class="btn">Cancel order</button>'
            "</form></main>"
        ),
        correct_element=None,
    ),
    DemoCase(
        id="button_removed",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=(
            "<main>"
            "<h1>Checkout</h1>"
            '<form id="order-form" data-testid="order-form">'
            '<button id="cancel-order" data-testid="cancel-order" '
            'class="btn">Cancel order</button>'
            "</form></main>"
        ),
        correct_element=None,
    ),
    DemoCase(
        id="save_draft_vs_save_order",
        step="click Save order",
        locator='id="save-order"',
        baseline_html=BASE_DRAFTS,
        html=BASE_DRAFTS,
        correct_element=None,
    ),
    DemoCase(
        id="delete_account_vs_delete_draft",
        step="click Delete account",
        locator='id="delete-account"',
        baseline_html=BASE_DRAFTS,
        html=BASE_DRAFTS,
        correct_element=None,
    ),
    DemoCase(
        id="disabled_submit",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace(
            '<button id="submit-order" data-testid="submit-order" ',
            '<button id="submit-order" data-testid="submit-order" disabled ',
            1,
        ),
        correct_element=None,
    ),
    DemoCase(
        id="renamed_id_and_text",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace('id="submit-order"', 'id="submit-order-v2"', 1).replace(
            ">Submit order</button>", ">Send order</button>", 1
        ),
        correct_element="submit-order",
    ),
    DemoCase(
        id="single_char_typo",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace(">Submit order</button>", ">Submt order</button>", 1),
        correct_element="submit-order",
    ),
]
