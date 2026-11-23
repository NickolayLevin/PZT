
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count
import requests
from .models import Release, Genre, Artist, Rating
from .services import *
from .importers import import_artist, import_release
from .models import Artist, Release
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def home(request):
    recently_added = (
        Release.objects
        .prefetch_related('artists')
        .order_by('-id')[:4]
    )

    rated_releases = (
        Release.objects
        .filter(rating__isnull=False)
        .select_related('rating')
        .prefetch_related('artists')
    )

    least_rated = sorted(
        rated_releases,
        key=lambda release: release.rating.total_score
    )[:4]

    context = {
        'recently_added': recently_added,
        'least_rated': least_rated,
    }

    return render(request, 'catalog/index.html', context)


def release_list(request):
    releases = (
        Release.objects
        .select_related('rating')
        .prefetch_related('artists', 'genres')
    )

    genres = (
        Genre.objects
        .filter(releases__isnull=False)
        .distinct()
        .order_by('name')
    )

    years = (
        Release.objects
        .exclude(release_date__isnull=True)
        .dates('release_date', 'year', order='DESC')
    )

    context = {
        'releases': releases,
        'genres': genres,
        'years': years,
    }

    return render(request, 'catalog/releases.html', context)


def release_detail(request, slug):
    release = get_object_or_404(
        Release.objects
        .select_related('rating')
        .prefetch_related('artists', 'genres'),
        slug=slug
    )

    more_releases = (
        Release.objects
        .exclude(id=release.id)
        .prefetch_related('artists')
        .order_by('-id')[:4]
    )

    context = {
        'release': release,
        'more_releases': more_releases,
    }

    return render(request, 'catalog/release_detail.html', context)


def artist_list(request):
    artists = (
        Artist.objects
        .annotate(release_count=Count('releases_links'))
        .order_by('name')
    )

    context = {
        'artists': artists,
    }

    return render(request, 'catalog/artists.html', context)


def artist_detail(request, slug):
    artist = get_object_or_404(Artist, slug=slug)

    releases = (
        Release.objects
        .filter(artists=artist)
        .select_related('rating')
        .prefetch_related('artists', 'genres')
        .order_by('-release_date', '-id')
    )

    first_release = (
        releases
        .exclude(release_date__isnull=True)
        .order_by('release_date')
        .first()
    )

    context = {
        'artist': artist,
        'releases': releases,
        'first_release': first_release,
    }

    return render(request, 'catalog/artist-detail.html', context)



@login_required(login_url='/admin/login/')
def musicbrainz_search(request):

    if not request.user.is_superuser:
        return HttpResponseForbidden(
            'You do not have permission to access this page.'
        )

    if request.method == "POST":
        musicbrainz_id = request.POST.get('musicbrainz_id')
        entity_type = request.POST.get('entity_type')

        if musicbrainz_id:
            if entity_type == 'artist':
                artist, created = import_artist(musicbrainz_id)

                return redirect(
                    'artist_detail',
                    slug=artist.slug
                )

            elif entity_type == 'release':
                release, created = import_release(musicbrainz_id)

                return redirect(
                    'release_detail',
                    slug=release.slug
                )

    query = request.GET.get('q', '').strip()

    artists = []
    releases = []
    error = None

    if query:
        try:
            artists = search_artists(query)
            releases = search_releases(query)

            for item in artists:
                artist = Artist.objects.filter(
                    musicbrainz_id=item['id']
                ).first()

                item['in_pzt'] = artist is not None

            for item in releases:
                release = Release.objects.filter(
                    musicbrainz_id=item['id']
                ).first()

                item['in_pzt'] = release is not None

        except requests.exceptions.RequestException:
            error = (
                'MusicBrainz is temporarily unavailable. '
                'Please try again later.'
            )

    context = {
        'query': query,
        'artists': artists,
        'releases': releases,
        'error': error,
    }

    return render(
        request,
        'catalog/musicbrainz_search.html',
        context
    )


def rate_release(request, slug):
    if not request.user.is_superuser:
        return HttpResponseForbidden(
            'You do not have permission to rate releases.'
        )
    release = get_object_or_404(Release, slug=slug)

    # Если оценка уже существует, возвращаемся к релизу
    if Rating.objects.filter(release=release).exists():
        return redirect('release_detail', slug=release.slug)

    if request.method == 'POST':
        fields = [
            'rhymes',
            'structure',
            'style',
            'individuality',
            'vibe',
        ]

        scores = {}
        error = None

        for field in fields:
            try:
                value = int(request.POST.get(field))
            except (TypeError, ValueError):
                error = 'Please provide a score for every criterion.'
                break

            if not 1 <= value <= 10:
                error = 'Scores must be between 1 and 10.'
                break

            scores[field] = value

        if not error:
            Rating.objects.create(
                release=release,
                **scores
            )

            return redirect(
                'release_detail',
                slug=release.slug
            )

        return render(
            request,
            'catalog/rate_release.html',
            {
                'release': release,
                'error': error,
            }
        )

    return render(
        request,
        'catalog/rate_release.html',
        {
            'release': release,
        }
    )


