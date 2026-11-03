def format_price(cents):
    """Format an amount in cents as dollars, e.g. 400 -> '$4.00'."""
    return f"${cents / 100:.2f}"
