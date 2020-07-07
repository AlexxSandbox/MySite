from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group','title', 'text', 'image')
        labels = {'group': 'Сообщество', 'title': 'Заголовок', 'text': 'Текст поста', 'image': 'Изображение'}
        help_texts = {
            'group': 'Здесь ты выбираешь о чем будет твой пост',
            'title': 'Придумай заголовок',
            'text': 'Напиши здесь что-то интересное и не забудь сохранить',
            'image': 'Добавь изображение для своего поста'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Текст комментария'}
        help_texts = {'text': 'Если только вам есть что написать'}
