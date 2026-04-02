"""Shared helpers for Django admin display methods across all apps."""
from django.utils.html import format_html


# Thresholds that mirror the PCEP passing threshold (70%) and a midpoint (40%).
_HIGH = 70
_MID  = 40

_COLOUR_HIGH   = "#198754"  # Bootstrap success green
_COLOUR_MID    = "#ffc107"  # Bootstrap warning amber
_COLOUR_LOW    = "#dc3545"  # Bootstrap danger red


def score_colour(value: float) -> str:
    """Return a green/amber/red hex colour for a 0–100 percentage."""
    if value >= _HIGH:
        return _COLOUR_HIGH
    if value >= _MID:
        return _COLOUR_MID
    return _COLOUR_LOW


def coloured_score(value: float, suffix: str = "%") -> str:
    """Return an HTML ``<span>`` with a colour-coded score value.

    Usage in an admin display method::

        @admin.display(description="Score")
        def score_badge(self, obj):
            return coloured_score(obj.score)
    """
    colour = score_colour(value)
    return format_html(
        '<span style="color:{};font-weight:600">{:.0f}{}</span>',
        colour, value, suffix,
    )
