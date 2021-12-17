# Create your views here.
from functools import wraps

from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator


def is_active(redirect_url):
    """
    Decorator for views that checks that user is authenticated and his property is_active set to True.
    Otherwise redirect to redirect_url
    """
    def _dec(view_func):
        @wraps(view_func)
        def _check_user(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.is_active:
                return view_func(request, *args, **kwargs)
            else:
                logout(request)
                return HttpResponseRedirect(redirect_url)

        return _check_user
    return _dec

class ActiveRequiredMixin(object):
    """Ensure that user must have active status in order to access view."""

    @method_decorator(is_active('/'))
    def dispatch(self, *args, **kwargs):
        return super(ActiveRequiredMixin, self).dispatch(*args, **kwargs)
