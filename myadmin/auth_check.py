from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'lid' not in request.session or request.session['lid'] == 'out':
            messages.error(request, 'Please login again to continue.')
            return redirect('login_return')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
