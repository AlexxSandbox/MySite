from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group','title', 'text', 'image')
        labels = {'group': 'Group', 'title': 'Title', 'text': 'Description', 'image': 'Picture'}
        help_texts = {
            'group': 'Here you choose what your post will be about.',
            'title': 'Write title to you log.',
            'text': 'Write something interesting here and don’t forget to save.',
            'image': 'Add picture to your log.'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Comment text'}
        help_texts = {'text': 'Think about it well'}
