import datetime
import io

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import path
from django.utils.timezone import now
from django.utils.translation import gettext_lazy
from mptt.admin import MPTTModelAdmin
from sorl.thumbnail.admin import AdminImageMixin

from commercial.filters import ArticlePublishedFilter, CategoryPublishedFilter, ArticleNewFilter, ArticleSaleFilter
from commercial.forms import ArticleAdminForm
from commercial.functions import export_department_to_xml
from commercial.models import Profile, CategoryProperties, ArticleProperties, ArticleImage, OrderItem, DepartamentSale, \
    UserDebs, Departament, Message
from commercial.tasks import send_message_mail


class ProfileAdmin(admin.StackedInline):
    model = Profile
    autocomplete_fields = ['departament']
    can_delete = False
    min_num = 1
    max_num = 1


class DebsAdmin(admin.TabularInline):
    model = UserDebs


class DepartamentSaleAdmin(admin.TabularInline):
    model = DepartamentSale
    extra = 1


class CategoryPropertyAdmin(admin.TabularInline):
    model = CategoryProperties
    min_num = 1
    autocomplete_fields = ['departament']

    def get_queryset(self, request):
        queryset = super(CategoryPropertyAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(
                departament_id=request.user.profile.departament_id)
        return queryset

    def get_max_num(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            return 1
        return super(CategoryPropertyAdmin, self).get_max_num(request, obj=obj, **kwargs)


class StartPageImageAdmin(AdminImageMixin, admin.ModelAdmin):
    list_display = ['pk', 'image', 'order']


class DepartamentAdmin(admin.ModelAdmin):
    inlines = [DepartamentSaleAdmin]
    list_display = ['country', 'email']
    search_fields = ['country']
    actions = None

    def get_queryset(self, request):
        queryset = super(DepartamentAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(id=request.user.profile.departament_id)
        return queryset

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_urls(self):
        urls = super().get_urls()
        department_urls = [
            path('<int:pk>/export_to_xml/', self.export_xml,
                 name='commercial_departament_export_to_xml')
        ]
        return department_urls + urls

    def export_xml(self, request, pk: int):
        departament = get_object_or_404(Departament, pk=pk)
        buffer = io.BytesIO()
        tree = export_department_to_xml(departament)

        tree.write(buffer, encoding='utf-8')
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f'department-{departament.country.name}.xml')


class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['country', 'price']
    search_fields = ['country']


class CategoryAdmin(MPTTModelAdmin):
    inlines = [CategoryPropertyAdmin]
    list_display = ['id', 'category_name']
    search_fields = ['id', 'categoryproperties__name']
    list_filter = [CategoryPublishedFilter]
    autocomplete_fields = ['parent']

    @admin.display(description=gettext_lazy('name'))
    def category_name(self, obj):
        property = obj.categoryproperties_set.filter(
            departament_id=self.request.user.profile.departament_id
        ).only('name').first()
        if property:
            return property.name

    def get_queryset(self, request):
        self.request = request
        queryset = super(CategoryAdmin, self).get_queryset(request)
        # queryset = queryset.select_related('categoryproperties').filter(categoryproperties__departament_id=request.user.profile.departament_id)
        return queryset.order_by('categoryproperties__name')


class ArticlePropertyAdmin(AdminImageMixin, admin.StackedInline):
    model = ArticleProperties
    min_num = 1
    autocomplete_fields = ['departament']
    extra = 0

    def get_queryset(self, request):
        queryset = super(ArticlePropertyAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(
                departament_id=request.user.profile.departament_id)
        return queryset

    def get_max_num(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            return 1
        return super(ArticlePropertyAdmin, self).get_max_num(request, obj=obj, **kwargs)


class ArticleImageInline(AdminImageMixin, admin.StackedInline):
    model = ArticleImage
    extra = 0

    def get_queryset(self, request):
        queryset = super(ArticleImageInline, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(
                departament_id=request.user.profile.departament_id)
        return queryset


class ArticleAdmin(admin.ModelAdmin):
    inlines = [ArticlePropertyAdmin, ArticleImageInline]
    list_display = ['id', 'article_name', 'article_order']
    search_fields = ['id', 'articleproperties__name']
    list_filter = [ArticlePublishedFilter, ArticleNewFilter, ArticleSaleFilter]
    autocomplete_fields = ['category']
    form = ArticleAdminForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(ArticleAdmin, self).get_form(request, obj=obj, **kwargs)
        form.request = request
        return form

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.save_images(form.instance)

    @admin.display(description=gettext_lazy('name'))
    def article_name(self, obj):
        property = obj.articleproperties_set.filter(
            departament_id=self.request.user.profile.departament_id
        ).only('name').first()
        if property:
            return property.name

    @admin.display(description=gettext_lazy('order'))
    def article_order(self, obj):
        property = obj.articleproperties_set.filter(
            departament_id=self.request.user.profile.departament_id
        ).only('order').first()
        if property:
            return property.order

    def get_queryset(self, request):
        queryset = super(ArticleAdmin, self).get_queryset(request)
        self.request = request
        return queryset  # .prefetch_related('property')


class UserAdmin(DefaultUserAdmin):
    inlines = [ProfileAdmin, DebsAdmin]
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'is_staff'),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(
            UserAdmin, self).get_readonly_fields(request, obj=obj)
        if not request.user.is_superuser:
            readonly_fields += ('is_superuser', 'is_staff')
        return readonly_fields + ('date_joined', 'last_login')

    def get_queryset(self, request):
        queryset = super(UserAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(
                profile__departament_id=request.user.profile.departament_id)
        return queryset


class ImportPriceAdmin(admin.ModelAdmin):
    readonly_fields = ['imported_at', 'user']
    list_display = ['imported_at', 'user', 'departament']
    list_filter = ['user', 'departament']
    autocomplete_fields = ['departament', 'user']
    ordering = ['-imported_at']

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super(ImportPriceAdmin, self).save_model(request, obj, form, change)


class ImportDebtsAdmin(admin.ModelAdmin):
    readonly_fields = ['imported_at', 'user']
    list_display = ['imported_at', 'user']
    list_filter = ['user']
    ordering = ['-imported_at']

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super(ImportDebtsAdmin, self).save_model(request, obj, form, change)


class OrderItemInline(admin.StackedInline):
    model = OrderItem
    readonly_fields = ['article']
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(
            OrderItemInline, self).get_readonly_fields(request, obj)
        if obj and not request.user.is_superuser:
            return readonly_fields + ['count', 'price']
        return readonly_fields


class OrderAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    inlines = [OrderItemInline]
    readonly_fields = ['date', 'sum']
    ordering = ['-date']
    list_filter = ['is_closed', ('user', admin.RelatedOnlyFieldListFilter)]
    actions = None
    search_fields = ['id']
    list_display = ['id', 'user', 'date', 'is_closed']
    fields = ['user', 'date', 'comment', 'is_closed', 'sum']
    autocomplete_fields = ['user']

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(
            OrderAdmin, self).get_readonly_fields(request, obj)
        if obj and not request.user.is_superuser:
            return readonly_fields + ['user', 'date', 'comment', 'is_closed']
        return readonly_fields

    def get_queryset(self, request):
        queryset = super(OrderAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(
                user__profile__departament_id=request.user.profile.departament_id)
        return queryset


class PageAdmin(admin.ModelAdmin):
    list_display = ['slug']

    def get_list_display(self, request):
        list_display = super(PageAdmin, self).get_list_display(request)
        if request.user.is_superuser:
            return list_display + ['departament']
        return list_display

    def get_queryset(self, request):
        queryset = super(PageAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(
                departament_id=request.user.profile.departament_id)
        return queryset


class MessageInlineAdmin(admin.TabularInline):
    model = Message
    extra = 1
    readonly_fields = ['user']

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class ComplaintAdmin(admin.ModelAdmin):
    list_filter = ['status', 'user']
    inlines = [MessageInlineAdmin]
    autocomplete_fields = ['user']
    readonly_fields = ['user', 'date_of_purchase', 'product_name', 'invoice', 'description', 'image', 'video']

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False

    def save_formset(self, request, form, formset, change):
        complaint = form.instance
        messages = formset.save(commit=False)
        for message in messages:
            message.user = request.user
            message.save()
            if True or now() - complaint.user.last_login > datetime.timedelta(hours=1):
                send_message_mail.delay(complaint.user_id, message.id)
        formset.save()
