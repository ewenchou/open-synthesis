"""Django Template Helper Methods.

For more information, please see:
    https://docs.djangoproject.com/en/1.10/howto/custom-template-tags/
"""
import logging
import collections
import math

from django.template.defaulttags import register
# NOTE: django.core.urlresolvers was deprecated in Django 1.10. Landscape is loading version 1.9.9 for some reason
from django.urls import reverse  # pylint: disable=no-name-in-module

from openach.models import Evaluation, Eval


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


@register.filter
def get_class(obj):
    """Return the class name of obj."""
    return obj.__class__.__name__


@register.filter
def dict_get(dictionary, key):
    """Return the value for key in dictionary or None."""
    return dictionary.get(key, None)


@register.simple_tag
def get_detail(dictionary, evidence_id, hypothesis_id):
    """Return the evaluation Eval for a given hypothesis and piece of evidence."""
    return dictionary.get((evidence_id, hypothesis_id))


@register.simple_tag
def anon_or_voted(request, vote):
    """Return true if user is not authenticated, or they have voted."""
    return not request.user.is_authenticated or vote


@register.filter
def detail_name(eval_):
    """Return the human-readable name for the given evaluation."""
    if eval_:
        return next(e[1] for e in Evaluation.EVALUATION_OPTIONS if e[0] == eval_.value)
    else:
        return 'No Assessments'


@register.filter
def detail_classname(eval_):
    """Return the CSS style associate with the given evaluation."""
    mapping = {
        None: "eval-no-assessments",
        Eval.consistent: "eval-consistent",
        Eval.inconsistent: "eval-inconsistent",
        Eval.very_inconsistent: "eval-very-inconsistent",
        Eval.very_consistent: "eval-very-consistent",
        Eval.not_applicable: "eval-not-applicable",
        Eval.neutral: "eval-neutral"
    }
    result = mapping.get(eval_)
    return result


@register.simple_tag
def get_source_tags(dictionary, source_id, tag_id):
    """Perform a dictionary lookup, returning None if the key is not in the dictionary."""
    return dictionary.get((source_id, tag_id))


DisputeLevel = collections.namedtuple('DisputeLevel', ['max_level', 'name', 'css_class'])
# NOTE: the levels here need to match the levels in _detail_icons
DISPUTE_LEVELS = [
    DisputeLevel(max_level=0.5, name='Consensus', css_class='disagree-consensus'),
    DisputeLevel(max_level=1.5, name='Mild Dispute', css_class='disagree-mild-dispute'),
    DisputeLevel(max_level=2.0, name='Large Dispute', css_class='disagree-large-dispute'),
    DisputeLevel(max_level=math.inf, name='Extreme Dispute', css_class='disagree-extreme-dispute'),
]


def _dispute_level(value):
    return next(level for level in DISPUTE_LEVELS if value < level.max_level)


@register.filter
def disagreement_category(value):
    """Return a human-readable description of the level of disagreement given by the value."""
    return 'No Assessments' if value is None else _dispute_level(value).name


@register.filter
def disagreement_style(value):
    """Return the CSS class name associated with the given level of disagreement."""
    return 'disagree-no-assessments' if value is None else _dispute_level(value).css_class


@register.simple_tag
def comparison_style(user, consensus):
    """Return the CSS class name for the analysis cell given a user evaluation and the consensus evaluation.

    Requires that the user disagrees with the consensus. If the user roughly agrees, return the weak consistent
    or inconsistent CSS class. Otherwise, return the dispute style depending on the distance between the evaluations.
    """
    if user == consensus:
        raise ValueError("user evaluation must differ from consensus")

    diff = abs(user.value - consensus.value)
    non_na = user.value > 0 and consensus.value > 0

    if non_na and user.value < 3 and consensus.value < 3:
        return 'eval-inconsistent'
    elif non_na and user.value > 3 and consensus.value > 3:
        return 'eval-consistent'
    elif user.value == 0 or consensus.value == 0:
        return 'disagree-mild-dispute'
    elif diff >= 3:
        return 'disagree-extreme-dispute'
    elif diff >= 2:
        return 'disagree-large-dispute'
    elif diff >= 1:
        return 'disagree-mild-dispute'
    else:
        return 'disagree-consensus'


@register.filter
def bootstrap_alert(tags):
    """Return the Bootstrap alert CSS class for the given Django message level tag.

    Requires the message to only contain a single tag. For more information, see:
        https://docs.djangoproject.com/en/1.10/ref/contrib/messages/#message-tags
    """
    mapping = {
        'debug': 'alert-info',
        'info': 'alert-info',
        'success': 'alert-success',
        'warning': 'alert-warning',
        'error': 'alert-error',
    }
    return mapping[tags] if tags in mapping else tags


@register.filter
def board_url(board):
    """Return the URL for the board, including the slug if available."""
    # In the future, we might just want to directly use get_absolute_url in the template. However, this extra level
    # of indirection gives us some additional flexibility
    return board.get_absolute_url() if board is not None else None


@register.filter
def canonical_reverse(request, url_name):
    """Return the canonical URI for url_name."""
    # this should probably be a tag that calls the url template method and then builds the absolute uri
    return request.build_absolute_uri(reverse(url_name))


@register.simple_tag
def canonical_reverse_arg(request, url_name, arg):
    """Return the canonical URI for url_name with arg."""
    return request.build_absolute_uri(reverse(url_name, args=(arg, )))


@register.filter
def full_url(request, model):
    """Return the URL of the model, including domain."""
    return request.build_absolute_uri(model.get_absolute_url())


@register.filter
def canonical_url(request, model):
    """Return the canonical URL of the model, including domain, and excluding slugs and parameters."""
    return request.build_absolute_uri(model.get_canonical_url())


@register.filter
def canonical_profile_url(request, user):
    """Return the canonical URL of the user's public profile."""
    return request.build_absolute_uri(reverse('profile', args=(user.id,)))


@register.simple_tag
def get_verbose_field_name(instance, field_name):
    """Return the verbose name for a field."""
    # https://stackoverflow.com/questions/14496978/fields-verbose-name-in-templates
    # _meta is a standard API in Django: https://docs.djangoproject.com/en/1.10/ref/models/meta/
    return instance._meta.get_field(field_name).verbose_name.title()  # pylint: disable=protected-access


@register.simple_tag
def url_replace(request, field, value):
    """Return a GET dictionary with field=value."""
    # taken from: https://stackoverflow.com/questions/2047622/how-to-paginate-django-with-other-get-variables
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()
