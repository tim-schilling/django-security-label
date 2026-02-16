from __future__ import annotations

from django.contrib import admin

from .models import MaskedColumn


@admin.register(MaskedColumn)
class MaskedColumnAdmin(admin.ModelAdmin):
    list_display = ["uuid", "text", "confidential", "number"]
