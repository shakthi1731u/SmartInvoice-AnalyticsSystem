def to_int(value, default=0):
    """
    Safely convert value to int.
    Handles: '2', '2.0', 2.0, None, ''
    """
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def to_float(value, default=0.0):
    """
    Safely convert value to float.
    Handles: '2', '2.0', None, ''
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
