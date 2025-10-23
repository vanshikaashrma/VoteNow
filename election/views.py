from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages

from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from .models import Election, Position, Candidate, Voter
from django.utils import timezone



@login_required(login_url='/login/')
def home(request):
    now = timezone.now()
    active_elections = Election.objects.filter(start_time__lte=now, end_time__gte=now)
    completed_elections = Election.objects.filter(end_time__lt=now)
    return render(request, 'home.html', {
        'active_elections': active_elections,
        'completed_elections': completed_elections,
        'now': now
    })


def register(request):
    if request.method == 'POST':
        username = request.POST['username'].strip()
        password = request.POST['password']
        if not username:
            messages.error(request, "Username cannot be empty.")
            return render(request, 'register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken. Choose another one.")
            return render(request, 'register.html')

        user = User.objects.create_user(username=username, password=password)
        Voter.objects.create(user=user)
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='/login/')
def vote(request, position_id):
    position = get_object_or_404(Position, pk=position_id)
    election = position.election
    voter = Voter.objects.get(user=request.user)
    now = timezone.now()

    if now < election.start_time or now > election.end_time:
        return render(request, 'error.html', {'msg': 'Election not active.'})

    # NEW: Only block if user voted for this POSITION
    if position in voter.has_voted_positions.all():
        return render(request, 'error.html', {'msg': 'You already voted for this position.'})

    candidates = Candidate.objects.filter(position=position)

    if request.method == 'POST':
        candidate_id = request.POST.get('candidate')
        candidate = Candidate.objects.get(id=candidate_id)
        candidate.votes += 1
        candidate.save()
        voter.has_voted_positions.add(position)
        return redirect('home')

    return render(request, 'vote.html', {'position': position, 'candidates': candidates})


@login_required(login_url='/login/')
def results(request, election_id):
    election = get_object_or_404(Election, pk=election_id)
    now = timezone.now()
    if now < election.end_time:
        return render(request, 'error.html', {'msg': 'Results will be available after the election ends.'})

    positions = Position.objects.filter(election=election)
    data = {}
    for pos in positions:
        candidates = list(Candidate.objects.filter(position=pos))
        if candidates:
            max_votes = max(c.votes for c in candidates)
        else:
            max_votes = 0
        data[pos] = {
            'candidates': candidates,
            'max_votes': max_votes
        }
    return render(request, 'results.html', {'election': election, 'positions': data})

