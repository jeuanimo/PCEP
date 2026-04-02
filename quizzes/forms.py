"""Quiz configuration forms."""
from django import forms

from learning.models import Domain, Topic


class DomainQuizForm(forms.Form):
    """Lets the user pick a domain and how many questions to answer."""

    domain = forms.ModelChoiceField(
        queryset=Domain.objects.filter(is_active=True).order_by("order"),
        empty_label="— Choose a domain —",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    count = forms.IntegerField(
        label="Number of questions",
        min_value=5,
        max_value=30,
        initial=15,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": 5}),
    )


class TopicQuizForm(forms.Form):
    """Lets the user pick a topic for a focused drill."""

    topic = forms.ModelChoiceField(
        queryset=Topic.objects.filter(is_active=True).select_related("domain").order_by(
            "domain__order", "order"
        ),
        empty_label="— Choose a topic —",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    count = forms.IntegerField(
        label="Number of questions",
        min_value=3,
        max_value=20,
        initial=10,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": 1}),
    )
