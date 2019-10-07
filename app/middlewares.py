from django.utils import timezone
from .models import Profile
import pytz


class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        if request.user.is_authenticated:
            Profile.objects.filter(user__id=request.user.id).update(last_online=timezone.now())

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = 'Europe/Zagreb'
        if tzname:
            timezone.activate(pytz.timezone(tzname))
        else:
            timezone.deactivate()
        return self.get_response(request)
