from django.shortcuts import render, get_object_or_404
from blog.models import Post, Tag, Comment
from django.db.models import Count


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
        'first_tag_title': tags_list[0].title if tags_list else None,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_count,
    }


def index(request):
    tags_with_counts = Tag.objects.annotate(posts_count=Count('posts'))
    most_popular_posts = Post.objects.popular() \
                                     .select_author() \
                                     .prefetch_tags_with_posts_count()[:5] \
                                     .fetch_with_comments_count()

    most_fresh_posts = Post.objects.select_author() \
                                   .prefetch_tags_with_posts_count() \
                                   .annotate(comments_count=Count('comments')) \
                                   .order_by('-published_at')[:5]

    most_popular_tags = Tag.objects.with_posts_count().popular()[:5]

    context = {
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.with_optimized_prefetch()\
                    .prefetch_comments_with_authors() \
                    .annotate(likes_count=Count('likes')),
                    slug=slug
        )

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

    most_popular_tags = Tag.objects.with_posts_count().popular()[:5]

    most_popular_posts = Post.objects.popular() \
                                     .with_optimized_prefetch()[:5] \
                                     .fetch_with_comments_count()

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
    tag = get_object_or_404(tags_with_counts, title=tag_title)

    most_popular_tags = Tag.objects.with_posts_count().popular()[:5]

    most_popular_posts = Post.objects.popular() \
                                     .select_author() \
                                     .prefetch_tags_with_posts_count()[:5] \
                                     .fetch_with_comments_count()

    related_posts = tag.posts.select_author() \
                             .prefetch_tags_with_posts_count() \
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
