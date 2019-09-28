from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.forms import EmailField, CharField, PasswordInput
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Event, Comment, Evaluation


class UserCreationForm(UserCreationForm):
    email = EmailField(label="Email: ", required=True, help_text="This field is required")

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('bio',)


class CreateEventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ('title', 'description', 'start_time', 'end_time', 'public_flag')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content', )


class RateForm(forms.ModelForm):
    grade = forms.IntegerField(label="Rate event", required=True, validators=[MinValueValidator(1), MaxValueValidator(10)])

    class Meta:
        model = Evaluation
        fields = ('grade', )
