from django.contrib import admin
from .models import Election, Position, Candidate, Voter

class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 1

class PositionAdmin(admin.ModelAdmin):
    inlines = [CandidateInline]

class PositionInline(admin.StackedInline):
    model = Position
    extra = 1

class ElectionAdmin(admin.ModelAdmin):
    inlines = [PositionInline]

admin.site.register(Election, ElectionAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(Candidate)
admin.site.register(Voter)
