from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import FoodDonation, NGO, Profile


@receiver(post_save, sender=FoodDonation)
def notify_ngos(sender, instance, created, **kwargs):
    if created:
        ngos = NGO.objects.all()
        emails = [ngo.email for ngo in ngos if ngo.email]

        # 📍 Google Maps link
        map_link = f"https://www.google.com/maps?q={instance.latitude},{instance.longitude}"

        send_mail(
            subject="New Food Donation Available 🍱",
            message=f"""
A new food donation is available!

📍 Location: {instance.event.location}

🗺️ View on Map:
{map_link}

📦 Quantity: {instance.quantity}

Please log in to accept the donation.
""",
            from_email="your_email@gmail.com",
            recipient_list=emails,
            fail_silently=True
        )


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()


from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=FoodDonation)
def notify_ngos(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "notifications",
            {
                "type": "send_notification",
                "message": f"New donation at {instance.event.location}"
            }
        )