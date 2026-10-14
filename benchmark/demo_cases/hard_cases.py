"""Harder blind cases: 12 adversarial scenarios over the order form.

Same BASE_ORDER fixture family as cases.py (new file so the original 12
stay untouched). Expectations live in cases.yaml and were fixed before
any run. correct_element is None for every expected ESCALATE so the
intent layer must refuse on identity grounds, not on luck.
"""

from __future__ import annotations

from benchmark.demo_cases.cases import BASE_ORDER, DemoCase

SUBMIT_LOCATOR = 'id="submit-order"'

HARD_CASES: list[DemoCase] = [
    DemoCase(
        id="hidden_submit",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace(
            '<button id="submit-order" data-testid="submit-order" ',
            '<button id="submit-order" data-testid="submit-order" style="display:none" ',
            1,
        ),
        correct_element=None,
    ),
    DemoCase(
        id="iframe_submit",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=(
            "<main>"
            "<h1>Checkout</h1>"
            '<form id="order-form" data-testid="order-form">'
            '<button id="cancel-order" data-testid="cancel-order" '
            'class="btn">Cancel order</button>'
            "</form>"
            '<iframe id="pay-frame" data-testid="pay-frame" src="/pay">'
            '<button id="submit-order" data-testid="submit-order" '
            'class="btn primary">Submit order</button>'
            "</iframe></main>"
        ),
        correct_element=None,
    ),
    DemoCase(
        id="translated_label",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace(">Submit order</button>", ">Enviar pedido</button>", 1),
        correct_element="submit-order",
    ),
    DemoCase(
        id="shortened_label",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace(">Submit order</button>", ">Submit</button>", 1),
        correct_element="submit-order",
    ),
    DemoCase(
        id="near_identical_pair",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace(
            '<button id="cancel-order" data-testid="cancel-order" ',
            '<button id="submit-order-2" data-testid="submit-order-2" '
            'class="btn primary">Submit order</button>'
            '<button id="cancel-order" data-testid="cancel-order" ',
            1,
        ),
        correct_element=None,
    ),
    DemoCase(
        id="link_replaces_button",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace(
            '<button id="submit-order" data-testid="submit-order" '
            'class="btn primary">Submit order</button>',
            '<a id="submit-order" data-testid="submit-order" '
            'class="btn primary" href="/submit">Submit order</a>',
            1,
        ),
        correct_element="submit-order",
    ),
    DemoCase(
        id="reordered_steps",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=(
            "<main>"
            "<h1>Checkout</h1>"
            '<form id="order-form" data-testid="order-form">'
            '<button id="cancel-order" data-testid="cancel-order" '
            'class="btn">Cancel order</button>'
            '<button id="submit-order" data-testid="submit-order" '
            'class="btn primary">Submit order</button>'
            "</form></main>"
        ),
        correct_element="submit-order",
    ),
    DemoCase(
        id="cookie_covered",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace(
            "</form></main>",
            "</form>"
            '<div id="cookie-banner" data-testid="cookie-banner" '
            'class="overlay">Accept cookies</div></main>',
            1,
        ),
        correct_element=None,
    ),
    DemoCase(
        id="redesign_removed",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=(
            "<main>"
            "<h1>Checkout</h1>"
            '<form id="order-form" data-testid="order-form">'
            '<button id="cancel-order" data-testid="cancel-order" '
            'class="btn">Cancel order</button>'
            '<p data-testid="auto-submit-note">Order submits automatically.</p>'
            "</form></main>"
        ),
        correct_element=None,
    ),
    DemoCase(
        id="ab_continue_variant",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace(">Submit order</button>", ">Continue</button>", 1),
        correct_element="submit-order",
    ),
    DemoCase(
        id="duplicate_ids",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace(
            '<button id="cancel-order" data-testid="cancel-order" ',
            '<button id="submit-order" data-testid="submit-dup" '
            'class="btn primary">Submit order</button>'
            '<button id="cancel-order" data-testid="cancel-order" ',
            1,
        ),
        correct_element=None,
    ),
    DemoCase(
        id="action_changed",
        step="click Submit order",
        locator=SUBMIT_LOCATOR,
        baseline_html=BASE_ORDER,
        html=BASE_ORDER.replace(
            '<button id="submit-order" data-testid="submit-order" ',
            '<button id="submit-order" data-testid="submit-order" data-action="preview" ',
            1,
        ),
        correct_element=None,
    ),
]
