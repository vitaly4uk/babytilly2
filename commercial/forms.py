from django import forms
from django.core.validators import validate_image_file_extension
from django.utils.translation import gettext, gettext_lazy

from .models import Article, ArticleImage, Order, OrderItem, Message, Complaint


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = (
            "id",
            "category",
            "property",
            "vendor_code",
        )

    images = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"allow_multiple_selected": True}),
        label=gettext("Add images"),
        required=False,
    )

    def clean_images(self):
        """Make sure only images can be uploaded."""
        for upload in self.files.getlist("images"):
            validate_image_file_extension(upload)

    def save_images(self, article):
        """Process each uploaded image."""
        for upload in self.files.getlist("images"):
            image = ArticleImage(article=article, image=upload, departament_id=self.request.user.profile.departament_id)
            image.save()


class EditOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('delivery', 'comment')
        widgets = {
            'comment': forms.Textarea(attrs={'cols': 40}),
            'delivery': forms.Select(
                attrs={
                    'class': 'custom-select custom-select-sm d-inline-block',
                    'onchange': 'document.getElementById("cartform").submit()',
                }
            )
        }


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['id', 'count']
        widgets = {
            'id': forms.HiddenInput(),
            'count': forms.NumberInput(attrs={'size': '5', 'style': 'width: 50px;'}),
        }


class ComplaintForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea, label=gettext_lazy('Description'))
    attachments = MultipleFileField(
        label=gettext_lazy('Attachments'), help_text=gettext_lazy('Only video and photos are allowed.')
    )
    class Meta:
        model = Complaint
        exclude = ['user', 'status']


class MessageForm(forms.ModelForm):
    attachments = MultipleFileField(
        label=gettext_lazy('Attachments'), help_text=gettext_lazy('Only video and photos are allowed.'), required=False
    )

    class Meta:
        model = Message
        fields = ['text']
