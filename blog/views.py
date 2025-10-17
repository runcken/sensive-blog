from django.shortcuts import render
from blog.models import Post, Tag, Comment
from django.db.models import Count, Prefetch


def serialize_post(post):
    tags_list = list(post.tags.all())
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in tags_list],
        'first_tag_title': tags_list[0].title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_count,
    }


def index(request):
    tags_with_counts = Tag.objects.annotate(posts_count=Count('posts'))
    most_popular_posts = Post.objects.popular() \
                                     .prefetch_related('author') \
                                     .prefetch_related(
                                        Prefetch(
                                            'tags', queryset=tags_with_counts
                                            )
                                        )[:5] \
                                     .fetch_with_comments_count()

    most_fresh_posts = Post.objects.prefetch_related('author') \
                                   .prefetch_related(
                                        Prefetch(
                                            'tags', queryset=tags_with_counts
                                            )
                                        ).annotate(comments_count=Count(
                                            'comments'
                                        )
                                   ).order_by('-published_at')[:5]

    most_popular_tags = tags_with_counts.popular()[:5]

    context = {
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    tags_with_counts = Tag.objects.annotate(posts_count=Count('posts'))
    post = Post.objects.select_related('author') \
                       .prefetch_related(
                            Prefetch('tags', queryset=tags_with_counts)) \
                       .prefetch_related(
                            Prefetch(
                                'comments',
                                queryset=Comment.objects.select_related(
                                    'author'
                                    )
                                )
                        ).annotate(likes_count=Count('likes')).get(slug=slug)

    serialized_comments = []
    for comment in post.comments.all():
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': post.likes_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
    }

    most_popular_tags = tags_with_counts.popular()[:5]

    most_popular_posts = Post.objects.popular() \
                                     .prefetch_related('author') \
                                     .prefetch_related(
                                        Prefetch(
                                            'tags',
                                            queryset=tags_with_counts
                                            )
                                        )[:5].fetch_with_comments_count()

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tags_with_counts = Tag.objects.annotate(posts_count=Count('posts'))
    tag = tags_with_counts.get(title=tag_title)

    most_popular_tags = tags_with_counts.popular()[:5]

    most_popular_posts = Post.objects.popular() \
                                     .prefetch_related('author') \
                                     .prefetch_related(
                                        Prefetch(
                                            'tags',
                                            queryset=tags_with_counts
                                            )
                                        )[:5].fetch_with_comments_count()

    related_posts = tag.posts.select_related('author') \
                             .prefetch_related(
                                Prefetch(
                                    'tags',
                                    queryset=tags_with_counts
                                    )
                                ) \
                             .annotate(comments_count=Count('comments'))[:20]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
