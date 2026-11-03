from utils import format_price


def total_label(prices):
    """Return the formatted total of a list of prices in cents."""
    return format_price(sum(prices))
