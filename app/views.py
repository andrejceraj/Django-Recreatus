from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import Http404
from django.core.paginator import Paginator
from django.db.models import Q

from .forms import ProfileForm, UserForm, CreateEventForm, UserCreationForm, CommentForm, RateForm
from .models import Event, Comment, Evaluation

EVENTS_PER_PAGE = 2


@login_required
def index(request):
    page = request.GET.get('page', default='1')
    events = Event.objects.filter(public_flag=True).order_by('-start_time')
    paginator = Paginator(events, EVENTS_PER_PAGE)
    context = {
        "events_page": paginator.page(page)
    }
    return render(request, 'index.html', context)


@login_required
def private_events(request):
    page = request.GET.get('page', default='1')
    events = list(request.user.profile.events_invited_to.filter(public_flag=False))
    events.extend(list(request.user.profile.hosted_events.filter(public_flag=False)))
    events.sort(key=lambda event: event.start_time, reverse=True)
    paginator = Paginator(events, EVENTS_PER_PAGE)
    context = {
        "events_page": paginator.page(page)
    }
    return render(request, 'index.html', context)


@login_required
def event_detail(request, pk):
    event = Event.objects.get(pk=pk)
    if not event:
        raise Http404("Event not found!")

    if event.public_flag is False and event not in request.user.profile.events_invited_to.all() and \
            event not in request.user.profile.hosted_events.all():
        return redirect('app:index')

    users_to_invite = request.user.profile.following
    for u in event.invited_users.all():
        users_to_invite.remove(u)

    comment_form = CommentForm()
    rate_form = RateForm()
    should_rate = True
    if timezone.now() < event.end_time or event.owner == request.user.profile or request.user.profile not in event.participants.all():
        should_rate = False

    evaluated = Evaluation.objects.filter(grader=request.user.profile).filter(event=event).first()
    if evaluated:
        should_rate = False

    event_ended = timezone.now() > event.end_time

    context = {
        "event": event,
        "comment_form": comment_form,
        "should_rate": should_rate,
        "rate_form": rate_form,
        "users_to_invite": users_to_invite,
        "event_ended": event_ended
    }
    return render(request, 'event_detail.html', context)


@login_required
def user_detail(request, pk):
    user = User.objects.get(pk=pk)
    if not user:
        raise Http404("User not found!")

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
            messages.success(request, 'Event created successfully')
            return redirect('app:event_detail', new_event.id)
        else:
            messages.error(request, 'Failed to create event')
            return redirect('app:create_event')
    else:
        create_event_form = CreateEventForm()
        context = {
            "create_event_form": create_event_form
        }
    return render(request, 'create_event.html', context)


@login_required
@transaction.atomic
def edit_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile_form.save()
            messages.success(request, 'Profile edited successfully.')
            return redirect('app:user_detail', user.id)
        else:
            messages.error('Inserted data is invalid')

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
            messages.success(request, 'You have successfully signed up')
            return redirect('app:index')
        messages.error(request, 'Failed to sign up.')
    else:
        user_form = UserCreationForm()
        context = {
            "user_form": user_form
        }
    return render(request, 'registration/signup.html', context)


@login_required
def comment(request, pk):
    event = Event.objects.get(pk=pk)
    if not event:
        raise Http404("Event not found!")

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            content = comment_form.cleaned_data['content']
            owner = request.user.profile
            Comment.objects.create(content=content, owner=owner, event=event)
            messages.success(request, 'Comment posted')
        else:
            messages.error(request, "Failed to post comment.")

    return redirect('app:event_detail', event.id)


@login_required
def rate_event(request, pk):
    event = Event.objects.get(pk=pk)
    if not event:
        raise Http404("Event not found!")

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
            messages.success(request, 'You have successfully rated the event')
        else:
            messages.error(request, 'Failed to rate event')

    return redirect('app:event_detail', event.id)


@login_required
def participation(request, pk):
    event = Event.objects.get(pk=pk)
    if not event:
        raise Http404("Event not found!")

    if event.end_time < timezone.now():
        return redirect('app:index')

    if event.public_flag is False and request.user.profile not in event.invited_users.all():
        return redirect('app:index')

    participation = request.GET.get('participation', '')
    if participation == 'true':
        if request.user.profile not in event.participants.all():
            event.participants.add(request.user.profile)
            messages.success(request, 'You are now participating this event')
    elif participation == 'false':
        if request.user.profile in event.participants.all():
            event.participants.remove(request.user.profile)
            messages.info(request, 'You no longer participate this event')
    else:
        return redirect('app:index')
    return redirect('app:event_detail', event.id)


@login_required
def follow_user(request, pk):
    user = User.objects.get(pk=pk)
    if not user:
        raise Http404("User not found!")

    following = request.GET.get('follow', '')
    if following == 'true':
        if user.profile not in request.user.profile.following.all():
            request.user.profile.following.add(user.profile)
            messages.success(request, 'User followed')
    elif following == 'false':
        if user.profile in request.user.profile.following.all():
            request.user.profile.following.remove(user.profile)
            messages.success(request, 'You no longer follow this user')
    else:
        return redirect('app:index')
    return redirect('app:user_detail', user.id)


@login_required
def invite_users(request, event_id):
    event = Event.objects.get(pk=event_id)
    if not event:
        raise Http404("Event not found!")

    if request.method == 'POST':
        invited_users_ids = request.POST.getlist('invited_users')
        for user_id in invited_users_ids:
            user = User.objects.get(pk=user_id)
            if user and user.profile not in event.invited_users.all():
                event.invited_users.add(user.profile)
        messages.success(request, 'Users invited')
    return redirect('app:event_detail', event_id)


@login_required
def search(request):
    query = request.GET.get('query', '')
    type = request.GET.get('type', '')
    page = request.GET.get('page', default='1')
    if query == '' or type == '':
        return redirect('app:index')

    if type == 'events':
        events = Event.objects.filter(public_flag=True).filter(Q(title__icontains=query) | Q(description__icontains=query)).order_by('-start_time')
        paginator = Paginator(events, EVENTS_PER_PAGE)
        url_params = "query=" + query.replace(' ', "+", -1)
        url_params += "&type=events"
        context = {
            "page": paginator.page(page),
            "type": "events",
            "url_params": url_params
        }
        return render(request, 'search.html', context)
    elif type == 'users':
        users = User.objects.filter(Q(username__icontains=query))
        paginator = Paginator(users, EVENTS_PER_PAGE)
        url_params = "query=" + query.replace(' ', "+", -1)
        url_params += "&type=users"
        context = {
            "page": paginator.page(page),
            "type": "users",
            "url_params": url_params
        }
        return render(request, 'search.html', context)
    else:
        print("nista")
        return redirect('app:index')

