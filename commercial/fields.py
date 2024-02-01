from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy


ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            if data:
                result = [single_file_clean(d, initial) for d in data]
            else:
                result = single_file_clean(None, initial)
        else:
            result = single_file_clean(data, initial)
        if isinstance(result, (list, tuple)):
            for r in result:
                content_type = r.content_type.split("/")[0]
                if content_type == "image":
                    if r.size > 5242880:
                        raise ValidationError(
                            gettext_lazy(
                                "Please keep filesize under 5Mb for images and 50Mb for videos."
                            )
                        )
                elif content_type == "video":
                    if r.size > 52428800:
                        raise ValidationError(
                            gettext_lazy(
                                "Please keep filesize under 5Mb for images and 50Mb for videos."
                            )
                        )
                elif r.content_type not in ALLOWED_MIME_TYPES:
                    raise ValidationError(
                        gettext_lazy(
                            "Only video, photos, word, excel and pdf files are allowed."
                        )
                    )
        return result


class ArticleChoiceByNameField(forms.ModelChoiceField):
    pass
