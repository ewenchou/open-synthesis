"""Analysis of Competing Hypotheses View Decorators for managing caching and authorization."""
from functools import wraps

from django.views.decorators.cache import cache_page
from django.utils.decorators import available_attrs
from django.contrib.auth.decorators import user_passes_test, REDIRECT_FIELD_NAME
from django.conf import settings
from django.contrib import messages


ACCOUNT_REQUIRED = getattr(settings, 'ACCOUNT_REQUIRED', False)


def account_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """Require that the (1) the user is logged in, or (2) that an account is not required to view the page.

    If the user fails the test, redirect the user to the log-in page. See also
    django.contrib.auth.decorators.login_required
    """
    actual_decorator = user_passes_test(
        lambda u: not ACCOUNT_REQUIRED or u.is_authenticated(),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def cache_on_auth(timeout):
    """Cache the response based on whether or not the user is authenticated.

    Do NOT use on views that include user-specific information, e.g., CSRF tokens.
    """
    # https://stackoverflow.com/questions/11661503/django-caching-for-authenticated-users-only
    def _decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            key_prefix = "_auth_%s_" % request.user.is_authenticated()
            return cache_page(timeout, key_prefix=key_prefix)(view_func)(request, *args, **kwargs)
        return _wrapped_view
    return _decorator


def cache_if_anon(timeout):
    """Cache the view if the user is not authenticated and there are no messages to display."""
    # https://stackoverflow.com/questions/11661503/django-caching-for-authenticated-users-only
    def _decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated() or messages.get_messages(request):
                return view_func(request, *args, **kwargs)
            else:
                return cache_page(timeout)(view_func)(request, *args, **kwargs)
        return _wrapped_view
    return _decorator
