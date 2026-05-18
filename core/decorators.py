from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Only admin can access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
