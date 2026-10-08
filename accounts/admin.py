from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from profiles.models import SupervisorProfile

from .models import Accounts


class SupervisorProfileInline(admin.StackedInline):
	model = SupervisorProfile
	fk_name = 'user'
	extra = 0
	max_num = 1
	can_delete = False


@admin.register(Accounts)
class AccountsAdmin(UserAdmin):
	model = Accounts
	inlines = [SupervisorProfileInline]
	list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
	list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
	search_fields = ('username', 'email', 'first_name', 'last_name')
	ordering = ('username',)

	fieldsets = UserAdmin.fieldsets + (
		('ThesisBridge Profile', {'fields': ('role',)}),
	)
	add_fieldsets = UserAdmin.add_fieldsets + (
		('ThesisBridge Profile', {'fields': ('role',)}),
	)

	def get_inline_instances(self, request, obj=None):
		if obj is None or obj.role != 'supervisor':
			return []
		return super().get_inline_instances(request, obj)