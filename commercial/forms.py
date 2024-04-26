from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_image_file_extension
from django.utils.timezone import now
from django.utils.translation import gettext, gettext_lazy

from .fields import MultipleFileField
from .models import (
    Article,
    ArticleImage,
    Order,
    OrderItem,
    Message,
    Complaint,
)


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
            image = ArticleImage(
                article=article,
                image=upload,
                departament_id=self.request.user.profile.departament_id,
            )
            image.save()


class EditOrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data.get("send") != "true":
            self.fields["delivery"].required = False

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    class Meta:
        model = Order
        fields = ("delivery", "comment")
        widgets = {
            "comment": forms.Textarea(attrs={"cols": 40}),
            "widget": forms.Select(
                attrs={
                    "class": "custom-select custom-select-sm d-inline-block",
                    "onchange": 'document.getElementById("cartform").submit()',
                }
            ),
        }


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ["id", "count"]
        widgets = {
            "id": forms.HiddenInput(),
            "count": forms.NumberInput(attrs={"size": "5", "style": "width: 50px;"}),
        }


class ComplaintForm(forms.ModelForm):
    description = forms.CharField(
        widget=forms.Textarea, label=gettext_lazy("Description")
    )
    attachments = MultipleFileField(
        label=gettext_lazy("Attachments"),
        help_text=gettext_lazy(
            "Only video, photos, word, excel and pdf files are allowed. Max allowed sizes are 50Mb for videos and 5Mb for all other."
        ),
        required=True,
    )
    article = forms.ModelChoiceField(
        Article.objects.filter(articleproperties__departamet_id=4),
        label=gettext_lazy("Product name"),
        to_field_name="articleproperties__name",
        help_text=gettext_lazy(
            "Please, start enter product name like Bravo, Alfa, etc and select one from list."
        ),
        widget=forms.TextInput(),
    )

    def clean_date_of_purchase(self):
        date_of_purchase = self.cleaned_data["date_of_purchase"]
        if date_of_purchase > now().date():
            raise ValidationError(
                gettext_lazy("The date must be less or equal to today's")
            )
        return date_of_purchase

    def clean_receipt(self):
        r = self.cleaned_data["receipt"]
        content_type = r.content_type.split("/")[0]
        if content_type == "image":
            if r.size > 5242880:
                raise ValidationError(gettext_lazy("Please keep filesize under 5Mb."))
        return r

    class Meta:
        model = Complaint
        exclude = ["user", "status"]
        help_texts = {
            "receipt": gettext_lazy("Only photos are allowed. Max allowed size is 5Mb.")
        }


class MessageForm(forms.ModelForm):
    attachments = MultipleFileField(
        label=gettext_lazy("Attachments"),
        help_text=gettext_lazy(
            "Only video, photos, word, excel and pdf files are allowed. Max allowed sizes are 50Mb for videos and 5Mb for all other."
        ),
        required=False,
    )

    class Meta:
        model = Message
        fields = ["text"]
