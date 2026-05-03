from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# 🏢 NGO Model
class NGO(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(null=True, blank=True)
    location = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.name


# 🎉 Event Model
class Event(models.Model):
    manager = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=200)
    date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# 🍱 Food Donation Model
class FoodDonation(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Picked', 'Picked'),
        ('Delivered', 'Delivered'),
    ]
   
    description = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="donations")
    quantity = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    available_until = models.DateTimeField()
    image = models.ImageField(upload_to='donations/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    assigned_volunteer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="deliveries"
    )

    assigned_ngo = models.ForeignKey(
        NGO, on_delete=models.SET_NULL, null=True, blank=True
    )

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.event.name} - {self.description}"


# 👤 Profile Model
class Profile(models.Model):
    ROLE_CHOICES = [
        ('donor', 'Donor'),
        ('volunteer', 'Volunteer'),
        ('ngo', 'NGO'),
        ('manager', 'Manager'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"