from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Election(models.Model):
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    description = models.TextField()

    def is_active(self):
        return self.start_time <= timezone.now() <= self.end_time

    def __str__(self):
        return self.title

class Position(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.title} ({self.election.title})"

class Candidate(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    votes = models.IntegerField(default=0)
    image = models.ImageField(upload_to='candidates/', blank=True, null=True)   # If you support candidate images

    def __str__(self):
        return self.name

class Voter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    has_voted_positions = models.ManyToManyField(Position, blank=True)   # change here!

    def __str__(self):
        return self.user.username

