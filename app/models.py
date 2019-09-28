from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=200, blank=True)
    last_online = models.DateTimeField(default=timezone.now)

    following = models.ManyToManyField('Profile', related_name='followers', blank=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Event(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    public_flag = models.BooleanField(default=True)

    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='hosted_events')
    participants = models.ManyToManyField('Profile', related_name='events_participating', blank=True)
    invited_users = models.ManyToManyField('Profile', related_name='events_invited_to', blank=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    content = models.TextField()
    posted_on = models.DateTimeField(default=timezone.now)

    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='comments')

    def __str__(self):
        return self.content


class Evaluation(models.Model):
    grade = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])

    grader = models.ForeignKey(Profile, on_delete=models.DO_NOTHING)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):
        return self.grader.user.username + '->' + self.event.owner.user.username + '->' + self.grade


