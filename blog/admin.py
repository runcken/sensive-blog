from django.contrib import admin
from blog.models import Post, Tag, Comment


class PostAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'text',
        'author',
    ]
    raw_id_fields = ['likes']
    list_per_page = 10


class CommentAdmin(admin.ModelAdmin):
    list_display = [
        'post',
        'author',
        'text'
    ]
    raw_id_fields = ['author']
    list_per_page = 15


admin.site.register(Post, PostAdmin)
admin.site.register(Tag)
admin.site.register(Comment, CommentAdmin)
