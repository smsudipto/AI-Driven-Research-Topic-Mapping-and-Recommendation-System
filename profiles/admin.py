from django.contrib import admin

from .models import StudentProfile, SupervisorProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
	raw_id_fields = ('user',)
	list_display = ('user', 'student_id', 'department', 'cgpa')
	search_fields = ('user__username', 'user__email', 'student_id')


@admin.register(SupervisorProfile)
class SupervisorProfileAdmin(admin.ModelAdmin):
	readonly_fields = ('user',)
	list_display = ('user', 'department', 'designation', 'status', 'max_student_capacity', 'current_student_count')
	search_fields = ('user__username', 'user__email', 'designation', 'department', 'research_interests', 'expertise_areas')
	list_filter = ('department', 'status')
