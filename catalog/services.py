
import requests
import time

from threading import Lock


MUSICBRAINZ_URL = 'https://musicbrainz.org/ws/2/'

HEADERS = {
    'User-Agent': 'PZT/0.1.0 (Django music catalog)',
}

_REQUEST_LOCK = Lock()
_LAST_REQUEST_TIME = 0
_REQUEST_INTERVAL = 1.1


def _musicbrainz_get(entity_type, params, entity_id=None):
    global _LAST_REQUEST_TIME

    url = f'{MUSICBRAINZ_URL}{entity_type}/'

    if entity_id:
        url += f'{entity_id}'

    for attempt in range(3):
        with _REQUEST_LOCK:
            elapsed = time.monotonic() - _LAST_REQUEST_TIME

            if elapsed < _REQUEST_INTERVAL:
                time.sleep(_REQUEST_INTERVAL - elapsed)

            _LAST_REQUEST_TIME = time.monotonic()

            response = requests.get(
                url, 
                params=params,
                headers=HEADERS,
                timeout=10
            )

        
        if response.status_code in (429, 502, 503, 504):

            if attempt < 2:

                retry_after = response.headers.get('Retry-After')

                try:
                    delay = float(retry_after)
                except (TypeError, ValueError):
                    delay = 2 ** (attempt + 1)

                time.sleep(max(delay, 1.1))
                continue

        response.raise_for_status()
        
        return response


def _format_artist_credit(artist_credit):

    artist_names = []
    artists = []

    for item in artist_credit or []:

        if not isinstance(item, dict):
            continue

        artist = item.get('artist', {})

        if not artist:
            continue

        name = artist.get('name', '')

        if name:
            artist_names.append(name)

            artists.append({
                'id': artist.get('id'),
                'name': name,
            })

        joinphrase = item.get('joinphrase', '')
        if joinphrase and artist_names:
            artist_names[-1] += joinphrase

    return {
        'artist_names': ''.join(artist_names),
        'artists': artists,
    }



def _search_musicbrainz(
    entity_type,
    query,
    limit=100,
    offset=0,
    with_count=False
):

    if entity_type not in ('release', 'recording', 'artist'):
        raise ValueError("Неподдерживаемый тип поиска")

    if not query or not query.strip():
        return ([], 0) if with_count else []

    limit = max(1, min(int(limit), 100))
    offset = max(0, int(offset))

    params = {
        'query': query.strip(),
        'fmt': 'json',
        'limit': limit,
        'offset': offset,
    }

    response = _musicbrainz_get(entity_type, params)
    data = response.json()

    if entity_type == 'release':
        items = data.get('releases', [])
    elif entity_type == 'recording':
        items = data.get('recordings', [])
    else:
        items = data.get('artists', [])

    count = data.get('count', len(items))

    results = []

    for item in items:

        credit = _format_artist_credit(
            item.get('artist-credit', [])
        )

        result = {
            'id': item.get('id'),
            'title': item.get('title'),
            'artists': credit['artists'],
            'artist_names': credit['artist_names'],
            'url': f"https://musicbrainz.org/{entity_type}/{item.get('id')}",
        }

        if entity_type == 'release':

            release_group = item.get('release-group') or {}

            result.update({
                'date': item.get('date'),
                'country': item.get('country'),
                'status': item.get('status'),
                'primary_type': release_group.get('primary-type'),
                'secondary_types': release_group.get(
                    'secondary-types', []
                ),
            })

        elif entity_type == 'recording':

            result.update({
                'length': item.get('length'),
                'first_release_date': item.get(
                    'first-release-date'
                ),
            })

        else:

            life_span = item.get('life-span') or {}

            result.update({
                'name': item.get('name'),
                'sort_name': item.get('sort-name'),
                'type': item.get('type'),
                'country': item.get('country'),
                'disambiguation': item.get('disambiguation'),
                'begin': life_span.get('begin'),
                'end': life_span.get('end'),
            })

        results.append(result)

    if with_count:
        return results, count

    return results


def search_releases(
    query,
    limit=100,
    offset=0,
    with_count=False
):

    return _search_musicbrainz(
        'release',
        query,
        limit,
        offset,
        with_count
    )


def search_recordings(
    query,
    limit=100,
    offset=0,
    with_count=False
):

    return _search_musicbrainz(
        'recording',
        query,
        limit,
        offset,
        with_count
    )


def search_artists(
    query,
    limit=100,
    offset=0,
    with_count=False
):

    return _search_musicbrainz(
        'artist',
        query,
        limit,
        offset,
        with_count
    )


def get_artist_details(musicbrainz_id):

    response = _musicbrainz_get(
        'artist',
        {
            'fmt': 'json',
            'inc': 'url-rels',
        },
        entity_id=musicbrainz_id
    )

    item = response.json()
    life_span = item.get('life-span') or {}

    wikidata_id = None

    for relation in item.get('relations', []):
        if relation.get('type') == 'wikidata':
            resource = relation.get('url', {}).get('resource', '')
            wikidata_id = resource.rstrip('/').split('/')[-1]
            break

    return {
        'id': item.get('id'),
        'name': item.get('name'),
        'sort_name': item.get('sort-name'),
        'type': item.get('type'),
        'country': item.get('country'),
        'disambiguation': item.get('disambiguation'),
        'begin': life_span.get('begin'),
        'end': life_span.get('end'),
        'wikidata_id': wikidata_id,
    }

def get_release_details(musicbrainz_id):
    response = _musicbrainz_get(
            'release',
            {'fmt': 'json', 'inc': 'artists+release-groups'},
            entity_id=musicbrainz_id
        )
    
    
    item = response.json()
    credit = _format_artist_credit(item.get('artist-credit', []))
    release_group = item.get('release-group') or {}
    return {
        'id': item.get('id'),
        'title': item.get('title'),
        'date': item.get('date'),
        'country': item.get('country'),
        'status': item.get('status'),
        'barcode': item.get('barcode'),

        'primary_type': release_group.get('primary-type'),
        'secondary_types': release_group.get(
            'secondary-types', []
        ),

        'artist_names': credit['artist_names'],
        'artists': credit['artists'],

        'url': f"https://musicbrainz.org/release/{item.get('id')}",
    }


def get_artist_image(wikidata_id):

    if not wikidata_id:
        return None

    url = 'https://www.wikidata.org/w/api.php'

    params = {
        'action': 'wbgetentities',
        'ids': wikidata_id,
        'props': 'claims',
        'format': 'json'
    }

    headers = {
        'User-Agent': 'PZT/0.1.0 (Django music catalog)',
    }

    try: 
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        entity = data['entities'].get(wikidata_id, {})
        claims = entity.get('claims', {})
        images = claims.get('P18', [])

        if not images:
            return None

        return images[0]['mainsnak']['datavalue']['value']

    except (requests.exceptions.RequestException, KeyError, IndexError, TypeError):
        return None


def get_commons_image_url(filename):

    url = 'https://commons.wikimedia.org/w/api.php'

    params = {
        'action': 'query',
        'titles': f'File:{filename}',
        'prop': 'imageinfo',
        'iiprop': 'url',
        'iiurlwidth': 600,
        'format': 'json',
    }

    headers = {
        'User-Agent': 'PZT/0.1.0 (Django music catalog)',
    }

    try: 
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        pages = data['query']['pages']

        for page in pages.values():
            image_info = page.get('imageinfo', [])

            if image_info:
                return image_info[0].get('thumburl')
        return None
    
    except (requests.exceptions.RequestException, KeyError, TypeError):
        return None



def get_release_cover_url(musicbrainz_id):

    if not musicbrainz_id:
        return None

    url = (
        f'https://coverartarchive.org/release/'
        f'{musicbrainz_id}/front-500'
    )

    headers = {
        'User-Agent': 'PZT/0.1.0 (Django music catalog)',
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=15,
            allow_redirects=True
        )

        response.raise_for_status()

        content_type = response.headers.get(
            'Content-Type', ''
        ).split(';')[0]

        if content_type not in (
            'image/jpeg',
            'image/png',
            'image/webp',
        ):
            return None

        return response.url

    except requests.exceptions.RequestException:
        return None
