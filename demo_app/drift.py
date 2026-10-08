"""Drift injection for the demo app (deterministic, fixed seed)."""

from __future__ import annotations

DRIFT_MODES: list[str] = [
    "none",
    "renamed_ids",
    "changed_classes",
    "moved_elements",
    "reskinned_layout",
    "duplicate_buttons",
    "removed_element",
    "swapped_roles",
    "ab_variant_text",
]

DEFAULT_SEED = 42


def apply_drift(html: str, mode: str, seed: int = DEFAULT_SEED) -> str:
    """Apply exactly one drift to HTML. Pure function; seed reserved for future shuffles."""
    _ = seed  # deterministic string rewrites; seed kept for replayability
    if mode in ("none", ""):
        return html
    if mode == "renamed_ids":
        # Leading space avoids rewriting data-testid="..." (stable locator).
        out = html
        for old, new in [
            (' id="login-submit"', ' id="login-submit-v2"'),
            (' id="username"', ' id="user-name-field"'),
            (' id="password"', ' id="passwd-field"'),
            (' id="checkout-submit"', ' id="checkout-submit-v2"'),
            (' id="cart-checkout"', ' id="cart-checkout-v2"'),
        ]:
            out = out.replace(old, new)
        return out
    if mode == "changed_classes":
        return (
            html.replace("btn btn-primary", "button button--primary-new")
            .replace('class="product-card"', 'class="item-tile"')
            .replace('class="cart-item"', 'class="basket-row"')
        )
    if mode == "moved_elements":
        # Move primary action to the top of <main> (marker proves the move).
        marker = "<!-- moved:primary-action-first -->"
        for btn in [
            '<button id="login-submit"',
            '<button id="checkout-submit"',
            '<a id="cart-checkout"',
        ]:
            if btn in html:
                html = html.replace(btn, marker + btn, 1)
                break
        return html.replace("<main>", '<main data-layout-moved="true">', 1)
    if mode == "reskinned_layout":
        return html.replace("<main>", '<main class="reskinned" data-theme="v2">', 1).replace(
            "btn btn-primary", "btn btn-primary reskinned-btn", 1
        )
    if mode == "duplicate_buttons":
        # Add a lookalike with identical text/class but a decoy test id.
        if "Buy Now</button>" in html:
            lookalike = (
                '<button class="btn btn-primary" '
                'data-testid="decoy-buy" id="decoy-buy">Buy Now</button>'
            )
            return html.replace("Buy Now</button>", "Buy Now</button>" + lookalike, 1)
        # Pages without "Buy Now": clone their primary button as the decoy.
        cls_at = html.find('class="btn btn-primary"')
        if cls_at == -1:
            return html
        open_tag = html.rfind("<button", 0, cls_at)
        if open_tag == -1:
            return html
        text_start = html.find(">", open_tag) + 1
        text_end = html.find("</button>", text_start)
        label = html[text_start:text_end]
        lookalike = (
            '<button class="btn btn-primary" '
            f'data-testid="decoy-action" id="decoy-action">{label}</button>'
        )
        cut = text_end + len("</button>")
        return html[:cut] + lookalike + html[cut:]
    if mode == "removed_element":
        # Genuine regression: primary action is gone.
        for snippet in [
            '<button id="login-submit"',
            '<button id="checkout-submit"',
            '<a id="cart-checkout"',
            '<button id="add-cart-1"',
        ]:
            if snippet in html:
                start = html.find(snippet)
                # Remove from opening tag start to the closing tag end.
                tag_open = html.rfind("<", 0, start + 1)
                if snippet.startswith("<a"):
                    end = html.find("</a>", start) + len("</a>")
                else:
                    end = html.find("</button>", start) + len("</button>")
                return html[:tag_open] + "<!-- removed:primary-action -->" + html[end:]
        return html
    if mode == "swapped_roles":
        # Concept drift: Buy and Cancel swap text/roles.
        out = html.replace("Buy Now", "__TMP_BUY__")
        out = out.replace("Cancel", "Buy Now")
        out = out.replace("__TMP_BUY__", "Cancel")
        return out + "<!-- swapped:button-roles -->"
    if mode == "ab_variant_text":
        return (
            html.replace("Sign In", "Log In")
            .replace("Buy Now", "Purchase")
            .replace("Checkout", "Continue to Checkout")
        )
    raise ValueError(f"unknown drift mode: {mode}")
