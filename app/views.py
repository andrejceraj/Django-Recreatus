from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone

from .forms import ProfileForm, UserForm, CreateEventForm, UserCreationForm, CommentForm, RateForm
from .models import Event, Comment, Evaluation


@login_required
def index(request):
    events = Event.objects.filter(public_flag=True).order_by('-start_time')
    context = {
        "events": events
    }
    return render(request, 'index.html', context)


@login_required
def private_events(request):
    events = list(request.user.profile.events_invited_to.filter(public_flag=False))
    events.extend(list(request.user.profile.hosted_events.filter(public_flag=False)))
    events.sort(key=lambda event: event.start_time, reverse=True)
    context = {
        "events": events
    }
    return render(request, 'index.html', context)


@login_required
def event_detail(request, pk):
    event = Event.objects.get(pk=pk)

    if event.public_flag is False and event not in request.user.profile.events_invited_to.all() and \
            event not in request.user.profile.hosted_events.all():
        return redirect('app:index')

    comment_form = CommentForm()
    rate_form = RateForm()

    context = {
        "event": event,
        "comment_form": comment_form,
        "rate_form": rate_form
    }
    return render(request, 'event_detail.html', context)


@login_required
def user_detail(request, pk):
    user = User.objects.get(pk=pk)
    evaluations = Evaluation.objects.filter(event__owner=user.profile)
    count = 0
    rating = 0
    for e in evaluations:
        rating += e.grade
        count += 1

    if count > 0:
        rating = rating / count
    else:
        rating = "No rating to display"
    context = {
        "rating": rating,
        "user": user
    }
    return render(request, 'user_detail.html', context)


@login_required
def create_event(request):
    if request.method == 'POST':
        create_event_form = CreateEventForm(request.POST)
        if create_event_form.is_valid():
            title = create_event_form.cleaned_data['title']
            description = create_event_form.cleaned_data['description']
            start_time = create_event_form.cleaned_data['start_time']
            end_time = create_event_form.cleaned_data['end_time']
            public_flag = create_event_form.cleaned_data['public_flag']
            owner = request.user.profile
            new_event = Event.objects.create(title=title, description=description, start_time=start_time,
                                             end_time=end_time, public_flag=public_flag, owner=owner)
            return redirect('app:event_detail', new_event.id)
        else:
            return redirect('app:create_event')
    else:
        create_event_form = CreateEventForm()
        context = {
            "create_event_fomr": create_event_form
        }
    return render(request, 'create_event.html', context)


@login_required
@transaction.atomic
def edit_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('app:index')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
        context = {
            "user_form": user_form,
            "profile_form": profile_form
        }
    return render(request, 'edit_profile.html', context)


def signup(request):
    if request.method == 'POST':
        user_form = UserCreationForm(request.POST)
        if user_form.is_valid():
            user = user_form.save()
            login(request, user)
            return redirect('app:index')
    else:
        user_form = UserCreationForm()
        context = {
            "user_form": user_form
        }
    return render(request, 'registration/signup.html', context)


@login_required
def comment(request, pk):
    event = Event.objects.get(pk=pk)
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            content = comment_form.cleaned_data['content']
            owner = request.user.profile
            Comment.objects.create(content=content, owner=owner, event=event)

    return redirect('app:event_detail', event.id)


@login_required
def rate_event(request, pk):
    event = Event.objects.get(pk=pk)

    if request.user.profile not in event.participants.all():
        return redirect('app:index')

    if event.end_time > timezone.now():
        return redirect('app:index')

    if event in request.user.profile.hosted_events.all():
        return redirect('app:index')

    if request.method == 'POST':
        rate_form = RateForm(request.POST)
        if rate_form.is_valid():
            grade = rate_form.cleaned_data['grade']
            grader = request.user.profile
            Evaluation.objects.create(grade=grade, grader=grader, event=event)

    return redirect('app:event_detail', event.id)


@login_required
def participation(request, pk):
    event = Event.objects.get(pk=pk)

    if event.end_time < timezone.now():
        return redirect('app:index')

    if event.public_flag is False and request.user.profile not in event.invited_users.all():
        return redirect('app:index')

    participation = request.GET.get('participation', '')
    if participation == 'true':
        if request.user.profile not in event.participants.all():
            event.participants.add(request.user.profile)
    elif participation == 'false':
        if request.user.profile in event.participants.all():
            event.participants.remove(request.user.profile)
    else:
        return redirect('app:index')
    return redirect('app:event_detail', event.id)


@login_required
def follow_user(request, pk):
    user = User.objects.get(pk=pk)
    following = request.GET.get('follow', '')
    if following == 'true':
        if user.profile not in request.user.profile.following.all():
            request.user.profile.following.add(user.profile)
    elif following == 'false':
        if user.profile in request.user.profile.following.all():
            request.user.profile.following.remove(user.profile)
    else:
        return redirect('app:index')
    return redirect('app:user_detail', user.id)


@login_required
def invite_user(request, event_id):
    username = request.GET.get('user')
    user = User.objects.filter(username=username).first()

    if not user:
        return redirect('app:index')

    if user == request.user:
        return redirect('app:index')

    event = Event.objects.get(pk=event_id)
    invitation = request.GET.get('invitation', '')
    if invitation == 'true':
        if user.profile not in event.invited_users.all():
            event.invited_users.add(user.profile)
    elif invitation == 'false':
        if user.profile in event.invited_users.all():
            event.invited_users.remove(user.profile)
    else:
        return redirect('app:index')
    return redirect('app:event_detail', event_id)
