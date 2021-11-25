from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.translation import gettext_lazy
from mptt.admin import MPTTModelAdmin
from sorl.thumbnail.admin import AdminImageMixin

from commercial.filters import ArticlePublishedFilter, CategoryPublishedFilter
from commercial.models import Profile, CategoryProperties, ArticleProperties, ArticleImage, OrderItem


class ProfileAdmin(admin.TabularInline):
    model = Profile
    autocomplete_fields = ['departament']
    can_delete = False
    min_num = 1
    max_num = 1


class CategoryPropertyAdmin(admin.StackedInline):
    model = CategoryProperties
    min_num = 1
    autocomplete_fields = ['departament']

    def get_queryset(self, request):
        queryset = super(CategoryPropertyAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(departament_id=request.user.profile.departament_id)
        return queryset

    def get_max_num(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            return 1
        return super(CategoryPropertyAdmin, self).get_max_num(request, obj=obj, **kwargs)


class StartPageImageAdmin(AdminImageMixin, admin.ModelAdmin):
    list_display = ['pk', 'image', 'order']


class DepartamentAdmin(admin.ModelAdmin):
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


class CategoryAdmin(MPTTModelAdmin):
    inlines = [CategoryPropertyAdmin]
    list_display = ['id', 'category_name']
    search_fields = ['id']
    list_filter = [CategoryPublishedFilter]

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
        return queryset  # .prefetch_related('property')


class ArticlePropertyAdmin(admin.StackedInline):
    model = ArticleProperties
    min_num = 1
    autocomplete_fields = ['departament']

    def get_queryset(self, request):
        queryset = super(ArticlePropertyAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(departament_id=request.user.profile.departament_id)
        return queryset

    def get_max_num(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            return 1
        return super(ArticlePropertyAdmin, self).get_max_num(request, obj=obj, **kwargs)


class ArticleImageInline(AdminImageMixin, admin.StackedInline):
    model = ArticleImage
    extra = 0


class ArticleAdmin(AdminImageMixin, admin.ModelAdmin):
    inlines = [ArticlePropertyAdmin, ArticleImageInline]
    list_display = ['id', 'article_name']
    search_fields = ['id']
    list_filter = [ArticlePublishedFilter]

    def save_model(self, request, obj, form, change):
        obj.save()

        for afile in request.FILES.getlist('images_multiple'):
            obj.images.create(image=afile)

    @admin.display(description=gettext_lazy('name'))
    def article_name(self, obj):
        property = obj.articleproperties_set.filter(
            departament_id=self.request.user.profile.departament_id
        ).only('name').first()
        if property:
            return property.name

    def get_queryset(self, request):
        queryset = super(ArticleAdmin, self).get_queryset(request)
        self.request = request
        return queryset  # .prefetch_related('property')


class UserAdmin(DefaultUserAdmin):
    inlines = [ProfileAdmin]
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'is_staff'),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(UserAdmin, self).get_readonly_fields(request, obj=obj)
        if not request.user.is_superuser:
            readonly_fields += ('is_superuser',)
        return readonly_fields + ('date_joined', 'last_login')


class ImportPriceAdmin(admin.ModelAdmin):
    readonly_fields = ['imported_at', 'user']
    list_display = ['imported_at', 'user', 'departament']
    list_filter = ['departament']
    autocomplete_fields = ['departament']
    ordering = ['imported_at']

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super(ImportPriceAdmin, self).save_model(request, obj, form, change)


class OrderItemInline(admin.StackedInline):
    model = OrderItem
    readonly_fields = []
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(OrderItemInline, self).get_readonly_fields(request, obj)
        if obj and not request.user.is_superuser:
            return readonly_fields + ['article', 'count', 'price']
        return readonly_fields


class OrderAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    inlines = [OrderItemInline]
    readonly_fields = []
    ordering = ['date']
    list_filter = ['is_closed', ('user', admin.RelatedOnlyFieldListFilter)]
    actions = None
    search_fields = ['id']
    list_display = ['id', 'user', 'date', 'is_closed']

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(OrderAdmin, self).get_readonly_fields(request, obj)
        if obj and not request.user.is_superuser:
            return readonly_fields + ['user', 'date', 'comment', 'is_closed']
        return readonly_fields

    def get_queryset(self, request):
        queryset = super(OrderAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(user__profile__departament_id=request.user.profile.department_id)
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
            queryset = queryset.filter(departament_id=request.user.profile.departament_id)
        return queryset
