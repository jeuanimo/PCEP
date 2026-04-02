"""Template filters for safe HTML rendering via bleach."""
from django import template
from django.utils.safestring import mark_safe

import bleach

register = template.Library()

# Tags and attributes allowed in admin-authored rich-text fields
# (lesson content, challenge descriptions).
_ALLOWED_TAGS = [
    "p", "br", "strong", "em", "b", "i", "u", "s",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "blockquote", "pre", "code",
    "a", "img",
    "table", "thead", "tbody", "tr", "th", "td",
    "hr", "span", "div",
]

_ALLOWED_ATTRIBUTES = {
    "a":   ["href", "title", "rel", "target"],
    "img": ["src", "alt", "width", "height", "class"],
    "*":   ["class"],
}


@register.filter(name="bleach_safe", is_safe=True)
def bleach_safe(value):
    """Sanitize HTML from trusted-but-not-verified sources (admin-authored content).

    Strips any tags or attributes not in the allowlist, preventing XSS even if
    an admin account is compromised or content is imported from an external source.
    """
    if not value:
        return ""
    cleaned = bleach.clean(
        value,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        strip=True,
    )
    return mark_safe(cleaned)
