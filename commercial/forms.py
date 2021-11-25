from django import forms
from django.core.validators import validate_image_file_extension
from django.utils.translation import gettext


from .models import Article, ArticleImage


class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = (
            "id",
            "category",
            "image",
            "property",
        )

    images = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
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
            image = ArticleImage(article=article, image=upload)
            image.save()
