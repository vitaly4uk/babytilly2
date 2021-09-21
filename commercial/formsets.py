from django.forms.models import BaseInlineFormSet

from commercial.models import CategoryProperties


class CategoryPropertyFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(CategoryPropertyFormSet, self).__init__(*args, **kwargs)
        self.queryset = CategoryProperties.objects.all()
        if not self.user.is_superuser:
            self.queryset = CategoryProperties.objects.filter(department_id=self.user.profile.department_id)
