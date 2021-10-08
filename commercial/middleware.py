from django.core.exceptions import MultipleObjectsReturned

from commercial.models import Order


class OrderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        order = None
        if request.user.is_authenticated:
            try:
                order, created = Order.objects.get_or_create(
                    user=request.user,
                    is_closed=False
                )
            except MultipleObjectsReturned:
                Order.objects.filter(user=request.user, is_closed=False).first().delete()
                order = Order.objects.filter(user=request.user, is_closed=False).first()

        request.order = order
        return self.get_response(request)
