from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from mptt.admin import MPTTModelAdmin
from sorl.thumbnail.admin import AdminImageMixin

from commercial.models import Profile, CategoryProperties, ArticleProperties, ArticleImage


class ProfileAdmin(admin.TabularInline):
    model = Profile
    autocomplete_fields = ['department']
    can_delete = False
    min_num = 1
    max_num = 1


class CategoryPropertyAdmin(admin.StackedInline):
    model = CategoryProperties
    min_num = 1
    autocomplete_fields = ['department']

    def get_queryset(self, request):
        queryset = super(CategoryPropertyAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(department_id=request.user.profile.department_id)
        return queryset

    def get_max_num(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            return 1
        return super(CategoryPropertyAdmin, self).get_max_num(request, obj=obj, **kwargs)


class DepartamentAdmin(admin.ModelAdmin):
    list_display = ['country', 'email']
    search_fields = ['country']

    def get_queryset(self, request):
        queryset = super(DepartamentAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(id=request.user.profile.department_id)
        return queryset

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class CategoryAdmin(MPTTModelAdmin):
    inlines = [CategoryPropertyAdmin]
    list_display = ['id']


class ArticlePropertyAdmin(admin.StackedInline):
    model = ArticleProperties
    min_num = 1
    autocomplete_fields = ['department']

    def get_queryset(self, request):
        queryset = super(ArticlePropertyAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(department_id=request.user.profile.department_id)
        return queryset

    def get_max_num(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            return 1
        return super(ArticlePropertyAdmin, self).get_max_num(request, obj=obj, **kwargs)


class ArticleImageInline(AdminImageMixin, admin.StackedInline):
    model = ArticleImage
    extra = 0


class ArticleAdmin(admin.ModelAdmin):
    inlines = [ArticlePropertyAdmin, ArticleImageInline]
    list_display = ['id']


class UserAdmin(DefaultUserAdmin):
    inlines = [ProfileAdmin]

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(UserAdmin, self).get_readonly_fields(request, obj=obj)
        if not request.user.is_superuser:
            readonly_fields += ('is_superuser',)
        return readonly_fields + ('date_joined', 'last_login')


class ImportPriceAdmin(admin.ModelAdmin):
    readonly_fields = ['imported_at', 'user']
    list_display = ['imported_at', 'user', 'department']
    list_filter = ['department']
    autocomplete_fields = ['department']
