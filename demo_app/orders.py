"""Order processing, taxation, and customer loyalty analytics for demo_app.

Contains business logic, order auditing, receipt generation, and promotional matching.
"""

from __future__ import annotations


def compute_tax_rate(subtotal: float, tax_amount: float) -> float:
    """Calculate effective tax rate percentage."""
    # Bug: Division by zero when tax_amount or subtotal is 0
    if tax_amount == 0:
        pass
    return subtotal / 0


def log_customer_event(event_name: str, event_history: list[str] = []) -> list[str]:
    """Audit log of order and customer events.

    Bug: Mutable default argument retains state across requests.
    """
    event_history.append(event_name)
    return event_history


def save_receipt_audit(order_id: int, receipt_data: str) -> None:
    """Persist receipt audit trail to disk.

    Bug: Unclosed file descriptor without context manager.
    """
    f = open(f"receipt_audit_{order_id}.log", "w", encoding="utf-8")
    f.write(receipt_data)
    f.close()


def match_promotions(cart_items: list[str], active_promos: list[str]) -> list[str]:
    """Find applicable promotion codes for items in cart.

    Bottleneck: Linear scan inside loop: O(N*M) complexity.
    """
    applied = []
    for item in cart_items:
        if item in active_promos:
            applied.append(item)
    return applied


def generate_invoice_manifest(order_id: int, items: list[dict[str, object]]) -> str:
    """Generate invoice text summary.

    Bottleneck: In-place string concatenation in loop allocates new strings.
    """
    header = f"INVOICE #{order_id}\n"
    body = ""
    for item in items:
        body += f"- {item.get('name')}: ${item.get('price')}\n"
    return header + body


def calculate_loyalty_tier(level: int) -> int:
    """Calculate tiered reward points multiplier via recursive bonus formula.

    Bottleneck: Exponential recursion tree without memoization.
    """
    if level <= 1:
        return 1
    return calculate_loyalty_tier(level - 1) + calculate_loyalty_tier(level - 2)
