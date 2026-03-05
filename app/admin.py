from django.contrib import admin
from .models import *

admin.site.register(Patient)
admin.site.register(Information)
admin.site.register(Event)
# admin.site.register(Study)
admin.site.register(Extraction)
admin.site.register(SelectionReduction)
admin.site.register(Classification)
admin.site.register(Notification)
admin.site.register(Comment)
admin.site.register(hasaccess)
admin.site.register(ExternalFeature)
admin.site.register(Feature)
admin.site.register(Normalization)


@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = (
        "idstudy",
        "name",
        "type",
        "completed",
        "user",
    )
    list_filter = ("completed", "type",)
