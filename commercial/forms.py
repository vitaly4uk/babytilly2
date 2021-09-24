from django import forms
from django.utils.translation import ugettext_lazy
from commercial.models import StartPageImage


class StartPageImageAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwards):
        super(StartPageImageAdminForm, self).__init__(*args, **kwards)

    def clean_departament(self):
        user = self.user
        departament = self.cleaned_data.get('departament')
        if not departament and not user.is_superuser:
            raise forms.ValidationError(ugettext_lazy('field is required'))
        return departament

    class Meta:
        model = StartPageImage
        exclude = []
