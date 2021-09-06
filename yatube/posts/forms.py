from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta():
        model = Post
        fields = ('text', 'group', 'image',)
        labels = {'text': 'Текст поста', 'group': 'Группа',
                  'image': 'Картинка', }
        help_texts = {'text': 'Введите текст вашего поста в этом поле.',
                      'group': 'Выберете группу из списка.',
                      'image': 'Выберите картинку для вашего поста,'}


class CommentForm(forms.ModelForm):
    class Meta():
        model = Comment
        fields = ('text',)
        labels = {'text': 'Текст комментария', }
        help_texts = {
            'text': 'Введите текст вашего комментария в этом поле.', }
