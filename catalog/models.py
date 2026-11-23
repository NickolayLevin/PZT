from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal, ROUND_HALF_UP

# Create your models here.
class Artist(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Имя артиста'
    )
    slug = models.SlugField(unique=True, verbose_name='URL-идентификатор')
    
    musicbrainz_id = models.CharField(
        max_length=36,
        unique=True,
        null=True,
        blank=True,
        verbose_name='MusicBrainz ID'
    )
        
    image = models.ImageField(
        upload_to='artists/',
        verbose_name='Фотография артиста',
        blank = True,
        null=True
    )
    
    def __str__(self):
        return self.name




class Release(models.Model):

    class ReleaseType(models.TextChoices):
        ALBUM = 'album', 'Альбом'
        EP = 'ep', 'EP'
        SINGLE = 'single', 'сингл'
        MIXTAPE = 'mixtape', 'Микстейп'
        COMPILATION = 'compilation', 'сборник'
        OTHER = 'other', 'Другое'


    title = models.CharField(
        max_length=100,
        verbose_name='Название релиза'
    )
    slug = models.SlugField(
        max_length=150,
        verbose_name="URL-идентификатор", 
        unique=True
        )

    musicbrainz_id = models.CharField(
        max_length=36,
        unique=True,
        null=True,
        blank=True,
        verbose_name='MusicBrainz ID'
    )
    release_date = models.DateField(
        blank=True, 
        null=True, 
        verbose_name='Дата релиза'
        )
    release_type = models.CharField(
        max_length=20,
        verbose_name='Тип релиза',
        choices=ReleaseType.choices,
        default=ReleaseType.ALBUM)

    cover = models.ImageField(
        upload_to='covers/',
        verbose_name='Обложка релиза',
        blank = True,
        null=True
    )

    artists = models.ManyToManyField(
        Artist,
        through='ReleaseArtist',
        related_name='releases',
        verbose_name='Исполнители'
    )

    genres = models.ManyToManyField(
        'Genre',
        related_name='releases',
        verbose_name='Жанры',
        blank=True
    )

   

    def __str__(self):
        return self.title

class Genre(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Название жанра'
    )
    slug = models.SlugField(
        verbose_name='URL-идентификатор',
        max_length=100,
        unique=True
    )

    def __str__(self):
        return self.name


class Rating(models.Model):

    release = models.OneToOneField(
        Release,
        on_delete=models.CASCADE,
        related_name='rating',
        verbose_name='Релиз'
    )
    
    rhymes = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ],
        verbose_name='Рифмы/Образы'
    )
    
    structure = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ],
        verbose_name='Структура/Ритмика'
    )

    style = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ],
        verbose_name='Реализация стиля'
    )
    
    individuality = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ],
        verbose_name='Индивидуальность/Харизма'
    )

    vibe = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ],
        verbose_name='Атмосфера/Вайб'
    )

    @property
    def total_score(self):

        values = (
            self.rhymes,
            self.structure,
            self.style,
            self.individuality,
            self.vibe
        )

        if any(value is None for value in values):
            return None

        multipliers = {
            1: Decimal('1.0000'),
            2: Decimal('1.0675'),
            3: Decimal('1.1349'),
            4: Decimal('1.2024'),
            5: Decimal('1.2699'),
            6: Decimal('1.3373'),
            7: Decimal('1.4048 '),
            8: Decimal('1.4723'),
            9: Decimal('1.5397'),
            10: Decimal('1.6072'),
        }

        criteria_sum = (
            self.rhymes
            + self.structure
            + self.style
            + self.individuality
        )

        result = (
            Decimal(criteria_sum)
            * Decimal('1.4')
            * multipliers[self.vibe]
        )

        return result.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    
    
    def __str__(self):
        return f'Оценка: {self.release.title}'
   


class ReleaseArtist(models.Model):

    class Role(models.TextChoices):
        MAIN = 'main', 'Основной исполнитель'
        FEATURED = 'featured', 'Приглашенный исполнитель'
        OTHER = 'other', 'Другой участник'

    release = models.ForeignKey(
        Release,
        on_delete=models.CASCADE,
        related_name='artists_links'
        )

    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        related_name='releases_links'
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MAIN,
        verbose_name='Роль исполнителя'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['release', 'artist'],
                name = 'unique_release_artist'
            )
        ]

    def __str__(self):
        return f'{self.artist.name} - {self.release.title}'