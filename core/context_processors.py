from .models import StoreSetting


def store_settings(request):
    store = StoreSetting.objects.first()
    return {'store': store}
