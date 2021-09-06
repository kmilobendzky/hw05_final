from django.utils import timezone


def year(request):
    """Добавляет в контекст переменную greeting с приветствием."""
    now = timezone.now()
    return {'now': now, }
