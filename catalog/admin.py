from django.contrib import admin
from .models import *
# Register your models here.


class ReleaseArtistInLine(admin.TabularInline):
    model = ReleaseArtist
    extra = 1

class RatingInLine(admin.StackedInline):
    model = Rating
    extra = 0
    max_num = 1
    readonly_fields = ('total_score',)

@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_type', 'release_date') 
    list_filter = ('release_type', 'release_date', 'genres')
    search_fields = ('title', 'artists__name')
    prepopulated_fields = {'slug': ('title',)}

    filter_horizontal = ('genres',)

    inlines = [ReleaseArtistInLine, RatingInLine]


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = (
        'release',
        'rhymes',
        'structure',
        'style',
        'individuality',
        'vibe',
        'total_score'
    )

    readonly_fields = ('total_score', )

@admin.register(ReleaseArtist)
class ReleaseArtistAdmin(admin.ModelAdmin):
    list_display = ('release', 'artist', 'role')
    list_filter = ('role',)
