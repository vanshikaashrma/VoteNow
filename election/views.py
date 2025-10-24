import random
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.core.mail import send_mail
from .models import Election, Position, Candidate, Voter


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
        email = request.POST['email'].strip()

        if not username:
            messages.error(request, "Username cannot be empty.")
            return render(request, 'register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken. Choose another one.")
            return render(request, 'register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'register.html')

        # Create user account
        user = User.objects.create_user(username=username, password=password, email=email)

        # Generate OTP
        otp = f"{random.randint(100000, 999999)}"
        voter = Voter.objects.create(user=user, otp=otp)

        # Send verification email
        send_mail(
            subject="Votenow Registration OTP",
            message=f"Your OTP for email verification is: {otp}",
            from_email=None,
            recipient_list=[email],
        )

        # Store pending ID in current session
        request.session['pending_user_id'] = user.id
        messages.info(request, "A verification OTP has been sent to your email. Please verify to complete registration.")
        return redirect('verify_otp')

    return render(request, 'register.html')


def verify_otp(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.error(request, "No registration in progress. Please register again.")
        return redirect('register')

    voter = get_object_or_404(Voter, user__id=user_id)

    if request.method == 'POST':
        otp = request.POST['otp']

        if otp == voter.otp:
            voter.is_verified = True
            voter.otp = ''
            voter.save()
            login(request, voter.user)
            request.session.pop('pending_user_id', None)
            messages.success(request, "Your email has been verified! Registration complete.")
            return redirect('home')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'verify_otp.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            try:
                voter = user.voter
            except Voter.DoesNotExist:
                from election.models import Voter
                voter = Voter.objects.create(user=user, is_verified=True)
            # Always allow login for superuser/staff/developer
            if not voter.is_verified and not user.is_staff:
                messages.error(request, "Please verify your email before logging in.")
                return render(request, 'login.html')
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
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

    # Restrict user to one vote per position
    if position in voter.has_voted_positions.all():
        return render(request, 'error.html', {'msg': 'You already voted for this position.'})

    candidates = Candidate.objects.filter(position=position)

    if request.method == 'POST':
        candidate_id = request.POST.get('candidate')
        candidate = Candidate.objects.get(id=candidate_id)
        candidate.votes += 1
        candidate.save()
        voter.has_voted_positions.add(position)
        messages.success(request, "Your vote has been recorded successfully.")
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
        max_votes = max((c.votes for c in candidates), default=0)
        data[pos] = {'candidates': candidates, 'max_votes': max_votes}

    return render(request, 'results.html', {'election': election, 'positions': data})
