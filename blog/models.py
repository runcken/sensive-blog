from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch


class TagQuerySet(models.QuerySet):
    def with_posts_count(self):
        return self.annotate(posts_count=Count('posts'))

    def popular(self):
        return self.with_posts_count().order_by('-posts_count')


class PostQuerySet(models.QuerySet):
    def popular(self):
        return self.annotate(likes_count=Count('likes', distict=True)) \
                   .order_by('-likes_count')

    def fetch_with_comments_count(self):
        # return self.annotate(comments_count=Count('comments', distinct=True))
        posts_ids = [post.id for post in self]
        comments_prefetch = Prefetch(
            'comments',
            queryset=Comment.objects.only('id', 'post')
        )
        posts_with_comments = Post.objects.filter(
            id__in=posts_ids
        ).prefetch_related(comments_prefetch)
        for post in posts_with_comments:
            post.comments_count = post.comments.count()
        comments_count_dict = {
            post.id: post.comments_count for post in posts_with_comments
        }
        for post in self:
            post.comments_count = comments_count_dict[post.id]
        return self

    def prefetch_tags_with_posts_count(self):
        return self.prefetch_related(
            Prefetch('tags', queryset=Tag.objects.with_posts_count())
        )

    def prefetch_comments_with_authors(self):
        return self.prefetch_related(
            Prefetch(
                'comments',
                queryset=Comment.objects.select_related('author')
            )
        )

    def select_author(self):
        return self.select_related('author')

    def with_optimized_prefetch(self):
        return self.select_related('author').prefetch_tags_with_posts_count()


class PostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model)

    def popular(self):
        return self.get_queryset().popular()

    def fetch_with_comments_count(self):
        return self.get_queryset().fetch_with_comments_count()

    def select_author(self):
        return self.get_queryset().select_author()

    def with_optimized_prefetch(self):
        return self.get_queryset().with_optimized_prefetch()


class CommentQuerySet(models.QuerySet):
    def select_author(self):
        return self.select_related('author')


class CommentManager(models.Manager):
    def get_queryset(self):
        return CommentQuerySet(self.model)

    def select_author(self):
        return self.get_queryset().select_author()


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')
    objects = PostManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)
    objects = TagQuerySet.as_manager()

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        verbose_name='Пост, к которому написан',
        related_name='comments'
        )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')
    objects = CommentManager()

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
