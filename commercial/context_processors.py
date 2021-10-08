from django.core.cache import cache
from commercial.models import Category, CategoryProperties


def root_sections(request):
    categories = []
    if request.user.is_authenticated:
        categories = CategoryProperties.objects.filter(published=True, department__id=request.user.profile.department_id).select_related('category').order_by('category__tree_id', 'category__lft')

    return {
        'categories': categories
    }
