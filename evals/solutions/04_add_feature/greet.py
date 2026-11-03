def greet(name, shout=False):
    """Return a greeting for name, in capitals if shout is True."""
    message = f"Hello, {name}!"
    return message.upper() if shout else message
