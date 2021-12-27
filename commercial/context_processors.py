from commercial.models import CategoryProperties


def root_sections(request):
    categories = []
    if request.user.is_authenticated and request.user.profile:
        categories = CategoryProperties.objects.filter(
            published=True, departament__id=request.user.profile.departament_id
        ).select_related('category').order_by('name', 'category__tree_id', 'category__lft')

    return {
        'categories': categories
    }
