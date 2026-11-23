from django.utils.text import slugify

from .models import *

from .services import *

from datetime import datetime

from django.db import transaction

import requests

from django.core.files.base import ContentFile

from .services import get_artist_details, get_artist_image, get_commons_image_url


def _download_artist_image(artist, wikidata_id):

    if artist.image or not wikidata_id:
        return

    image_filename = get_artist_image(wikidata_id)

    if not image_filename:
        return

    image_url = get_commons_image_url(image_filename)

    if not image_url:
        return

    headers = {
        'User-Agent': 'PZT/0.1.0 (Django music catalog)',
    }

    try:
        response = requests.get(
            image_url,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '').split(';')[0]

        extensions = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/webp': '.webp',
        }

        extension = extensions.get(content_type)

        if not extension or not response.content:
            return

        filename = f'{artist.slug}-{artist.musicbrainz_id[:8]}{extension}'

        artist.image.save(
            filename,
            ContentFile(response.content),
            save=True
        )

    except requests.exceptions.RequestException:
        return



def import_artist(musicbrainz_id):

    data = get_artist_details(musicbrainz_id)

    name = data['name']

    artist_slug = slugify(name)

    if not artist_slug:
        artist_slug = f'artist-{musicbrainz_id[:8]}'

    slug_exists = (
        Artist.objects.filter(slug=artist_slug).exclude(musicbrainz_id=musicbrainz_id).exists()
     )

    if slug_exists:
        artist_slug = f'{artist_slug}-{musicbrainz_id[:8]}'

    artist, created = Artist.objects.get_or_create(
    musicbrainz_id=musicbrainz_id,
    defaults={
        'name': name,
        'slug': artist_slug
    }
)

    _download_artist_image(
        artist,
        data.get('wikidata_id')
    )

    return artist, created


def _get_release_type(data):
    primary_type = (data.get('primary_type') or '').lower()

    secondary_types = [
        item.lower()
        for item in data.get('secondary_types', [])
    ]

    if 'mixtape' in secondary_types:
        return Release.ReleaseType.MIXTAPE

    if 'compilation' in secondary_types:
        return Release.ReleaseType.COMPILATION

    release_types = {
        'album': Release.ReleaseType.ALBUM,
        'ep': Release.ReleaseType.EP,
        'single': Release.ReleaseType.SINGLE,
    }

    return release_types.get(
        primary_type,
        Release.ReleaseType.OTHER
    )

def _parse_release_date(date_string):

    if not date_string:
        return None

    try:
        return datetime.strptime(
            date_string,
            '%Y-%m-%d'
        ).date()
    except ValueError:
        return None



def _download_release_cover(release):

    if release.cover:
        return

    url = (
        f'https://coverartarchive.org/release/'
        f'{release.musicbrainz_id}/front-500'
    )

    headers = {
        'User-Agent': 'PZT/0.1.0 (Django music catalog)',
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')

        if not content_type.startswith('image/'):
            return

        if not response.content:
            return

        extensions = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/webp': '.webp'
        }

        extension = extensions.get(content_type.split(';')[0], '.jpg')

        if not extension or not response.content:
            return

        filename = (
            f'{release.slug}-{release.musicbrainz_id[:8]}{extension}'
        )

        release.cover.save(
            filename,
            ContentFile(response.content),
            save=True
        )

    except requests.exceptions.RequestException:
        return

def import_release(musicbrainz_id):

    data = get_release_details(musicbrainz_id)

    title = data['title']

    release_slug = slugify(title)

    if not release_slug:
        release_slug = f'release-{musicbrainz_id[:8]}'

    slug_exists = (
        Release.objects
        .filter(slug=release_slug)
        .exclude(musicbrainz_id=musicbrainz_id)
        .exists()
    )

    if slug_exists:
        release_slug = f'{release_slug}-{musicbrainz_id[:8]}'

    release_date = _parse_release_date(data.get('date'))
    release_type = _get_release_type(data)

    with transaction.atomic():

        release, created = Release.objects.get_or_create(
            musicbrainz_id=musicbrainz_id,
            defaults={
                'title': title,
                'slug': release_slug,
                'release_date': release_date,
                'release_type': release_type,
            }
        )

        for artist_data in data['artists']:

            artist_id = artist_data.get('id')

            if not artist_id:
                continue

            artist, artist_created = import_artist(artist_id)

            ReleaseArtist.objects.get_or_create(
                release=release,
                artist=artist,
                defaults={
                    'role': ReleaseArtist.Role.MAIN,
                }
            )
    _download_release_cover(release)
    
    return release, created



