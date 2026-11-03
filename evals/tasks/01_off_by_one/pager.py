def paginate(items, page_size):
    """Split items into pages of page_size items each."""
    return [items[i:i + page_size] for i in range(0, len(items) - page_size, page_size)]
