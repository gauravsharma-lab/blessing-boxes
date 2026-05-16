from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages

from .models import FoodDonation, Profile, NGO
from .forms import FoodDonationForm, SignupForm, LoginForm, NGOForm, ProfileForm
from .models import Event 
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

# 🏠 Homepage (ALWAYS LOAD — NO REDIRECT)
def homepage(request):
    return render(request, 'core/homepage.html')


# 🔐 Login View
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            # We keep the error for invalid login but it will be shown via form errors usually
            pass

    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})


# 🚪 Logout View
@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('homepage')


# 🎯 Select Role (from homepage buttons)
def select_role(request, role):
    request.session['selected_role'] = role
    return redirect('signup')   # go to signup after selecting role


# 📝 Signup (Single clean signup)
from django.contrib.auth.models import User

def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    role = request.session.get('selected_role')

    if not role:
        messages.warning(request, "Please select a role first.")
        return redirect('homepage')

    if request.method == 'POST':
        form = SignupForm(request.POST)

        if form.is_valid():
            #  CREATE USER
            user = form.save()

            # CREATE PROFILE WITH ROLE
            profile, created = Profile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()

            # SUCCESS MESSAGE
            messages.success(request, f"Your {role} account has been created successfully! Please login to continue.")

            # CLEAR SESSION ROLE
            request.session.pop('selected_role', None)

            return redirect('login')

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = SignupForm()

    return render(request, 'core/signup.html', {'form': form})

# 📊 Dashboard (Role-based)
@login_required(login_url='login')
def dashboard(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'role': 'donor'}
    )

    role = profile.role.strip().lower()
    print("User:", request.user)
    print("ROLE:", role)

    # 🟢 DONOR
    if role == 'donor':
        donations = FoodDonation.objects.filter(donor=request.user)
        profile_form = ProfileForm(instance=profile)
        return render(request, 'core/donor_dashboard.html', {'donations': donations, 'profile_form': profile_form})

    # 🔵 VOLUNTEER
    elif role == 'volunteer':
        available_tasks = FoodDonation.objects.filter(
            status='Approved',
            assigned_volunteer__isnull=True,
            available_until__gt=timezone.now()
        )
        my_deliveries = FoodDonation.objects.filter(
            assigned_volunteer=request.user
        ).exclude(status='Delivered')
        
        completed_deliveries = FoodDonation.objects.filter(
            assigned_volunteer=request.user,
            status='Delivered'
        )

        profile_form = ProfileForm(instance=profile)

        return render(request, 'core/volunteer.html', {
            'available_tasks': available_tasks,
            'my_deliveries': my_deliveries,
            'completed_deliveries': completed_deliveries,
            'profile_form': profile_form
        })

    # 🟡 NGO
    elif role == 'ngo':
        ngo, created = NGO.objects.get_or_create(
            user=request.user,
            defaults={
                'name': request.user.username,
                'location': 'Not Provided'
            }
        )

        pending_donations = FoodDonation.objects.filter(
            status='Pending', 
            available_until__gt=timezone.now()
        )

        approved_donations = FoodDonation.objects.filter(
            status='Approved',
            assigned_ngo=ngo
        )

        form = NGOForm(instance=ngo)

        return render(request, 'core/ngo_dashboard.html', {
            'pending_donations': pending_donations,
            'approved_donations': approved_donations,
            'ngo': ngo,
            'form': form
        })

    # 🔴 MANAGER
    elif role == 'manager':
        donations = FoodDonation.objects.all()
        return render(request, 'core/manager_dashboard.html', {'donations': donations})

    return redirect('homepage')

# 🍱 Donate Food
 


@login_required(login_url='login')
def donate_food(request):
    if request.method == 'POST':
        form = FoodDonationForm(request.POST, request.FILES)

        if form.is_valid():

            # 🔥 CREATE EVENT FROM FORM INPUT
            event_name = request.POST.get('event_name')
            location = request.POST.get('location')

            event = Event.objects.create(
                manager=request.user,
                name=event_name,
                location=location,
                date=timezone.now()
            )

            donation = form.save(commit=False)
            donation.donor = request.user
            donation.event = event
            donation.status = 'Pending'

            #  phone number 
            donation.phone_number = request.POST.get('phone_number')
            donation.latitude = request.POST.get('latitude')
            donation.longitude = request.POST.get('longitude')

            donation.save()

            # 📧 NOTIFY ALL NGOs
            ngo_emails = User.objects.filter(profile__role='ngo').values_list('email', flat=True)
            if ngo_emails:
                try:
                    from .utils import send_sendgrid_email
                    send_sendgrid_email(
                        subject="[Blessing Boxes] New Food Donation Available Near You",
                        message=(
                            f"Greetings,\n\n"
                            f"A new food donation for '{event_name}' has just been posted at {location}.\n"
                            f"Quantity: {request.POST.get('quantity')}\n\n"
                            f"Please log in to your NGO dashboard to review and claim this donation:\n"
                            f"http://127.0.0.1:8000/dashboard/\n\n"
                            f"Thank you for your service,\n"
                            f"The Blessing Boxes Team"
                        ),
                        recipient_list=list(ngo_emails)
                    )
                except Exception as e:
                    print(f"Email sending failed (donate_food): {e}")

            messages.success(request, "Donation submitted successfully!")
            return redirect('dashboard')

        else:
            print(form.errors)  # 👈 DEBUG (VERY IMPORTANT)
            messages.error(request, "Fix errors below")

    else:
        form = FoodDonationForm()

    return render(request, 'core/donate.html', {'form': form})

# 🚚 Accept Delivery (Volunteer)

@login_required
def accept_delivery(request, donation_id):
    donation = get_object_or_404(FoodDonation, id=donation_id)

    try:
        ngo = NGO.objects.get(user=request.user)
    except NGO.DoesNotExist:
        messages.error(request, "You are not registered as NGO!")
        return redirect('dashboard')

    if donation.available_until < timezone.now():
        messages.error(request, "This food donation has expired and cannot be claimed.")
        return redirect('dashboard')

    donation.assigned_ngo = ngo
    donation.status = 'Approved'
    donation.save()

    # 📧 NOTIFY ALL VOLUNTEERS
    volunteer_emails = User.objects.filter(profile__role='volunteer').values_list('email', flat=True)
    if volunteer_emails:
        try:
            from .utils import send_sendgrid_email
            send_sendgrid_email(
                subject="[Blessing Boxes] New Pickup Task Available",
                message=(
                    f"Greetings,\n\n"
                    f"A food donation for '{donation.event.name}' has been approved by {ngo.name}.\n"
                    f"It is now ready for pickup at:\n"
                    f"📍 {donation.event.location}\n\n"
                    f"Please log in to your Volunteer dashboard to accept this task:\n"
                    f"http://127.0.0.1:8000/dashboard/\n\n"
                    f"Thank you for helping us reduce food waste!\n"
                    f"The Blessing Boxes Team"
                ),
                recipient_list=list(volunteer_emails)
            )
        except Exception as e:
            print(f"Email sending failed (accept_delivery): {e}")

    messages.success(request, "Food claimed successfully!")
    return redirect('dashboard')


# 🚲 Volunteer: Accept Pickup Task
@login_required
def volunteer_accept_task(request, donation_id):
    donation = get_object_or_404(FoodDonation, id=donation_id)
    
    # Ensure it's approved and not already assigned
    if donation.status != 'Approved' or donation.assigned_volunteer:
        messages.error(request, "Task is no longer available.")
        return redirect('dashboard')

    donation.assigned_volunteer = request.user
    donation.save()

    messages.success(request, "Task accepted! It is now in your deliveries.")
    return redirect('dashboard')


# 🏁 Volunteer: Complete Delivery
@login_required
def volunteer_complete_delivery(request, donation_id):
    donation = get_object_or_404(FoodDonation, id=donation_id)
    
    if donation.assigned_volunteer != request.user:
        messages.error(request, "You are not assigned to this task.")
        return redirect('dashboard')

    donation.status = 'Delivered'
    donation.save()

    messages.success(request, "Delivery marked as completed. Thank you for your help!")
    return redirect('dashboard')


 #contact us
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        full_message = f"""
        Name: {name}
        Email: {email}

        Message:
        {message}
        """

        try:
            from .utils import send_sendgrid_email
            send_sendgrid_email(
                subject="New Contact Message - BlessingBoxes",
                message=full_message,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
            )
        except Exception as e:
            print(f"Email sending failed (contact): {e}")

        messages.success(request, "Message sent successfully!")
        return redirect('contact')

    return render(request, 'core/contact.html')

 #privacy policy
def privacy(request):
    return render(request, 'core/privacy.html')
    
    # edit 
@login_required(login_url='login')
def edit_donation(request, id):
    donation = get_object_or_404(FoodDonation, id=id)

    # 🔒 Security: only donor can edit
    if donation.donor != request.user:
        messages.error(request, "You are not allowed to edit this donation.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = FoodDonationForm(request.POST, instance=donation)
        if form.is_valid():
            form.save()
            messages.success(request, "Donation updated successfully!")
            return redirect('dashboard')
    else:
        form = FoodDonationForm(instance=donation)

    return render(request, 'core/edit_donation.html', {'form': form})

    # delete
@login_required(login_url='login')
def delete_donation(request, id):
    donation = get_object_or_404(FoodDonation, id=id)

    # 🔒 Only owner can delete
    if donation.donor != request.user:
        messages.error(request, "You are not allowed to delete this donation.")
        return redirect('dashboard')

    # 🔒 Prevent delete after pickup/delivery
    if donation.status in ['Picked', 'Delivered']:
        messages.error(request, "Cannot delete after pickup/delivery.")
        return redirect('dashboard')

    if request.method == 'POST':
        donation.delete()
        messages.success(request, "Donation deleted successfully!")
        return redirect('dashboard')

    return render(request, 'core/delete_confirm.html', {'donation': donation})

  #map
def add_donation(request):
    if request.method == "POST":

        # 📍 Get data from form
        event_name = request.POST.get("event_name")
        location = request.POST.get("location")
        phone = request.POST.get("phone_number")

        lat = request.POST.get("latitude")
        lng = request.POST.get("longitude")

        # ✅ CREATE EVENT (PUT IT HERE 👇)
        event = Event.objects.create(
            manager=request.user,   # IMPORTANT
            name=event_name,
            location=location,
            date=timezone.now()     # or from form
        )

        # ✅ CREATE FOOD DONATION
        FoodDonation.objects.create(
            event=event,
            donor=request.user,
            latitude=lat,
            longitude=lng,
            description=request.POST.get("description"),
            quantity=request.POST.get("quantity"),
            phone_number=phone,
            available_until=request.POST.get("available_until"),
        )

        return redirect("dashboard")

    return render(request, "core/add_donation.html")

@login_required(login_url='login')
def my_donations(request):
    donations = FoodDonation.objects.filter(donor=request.user)
    return render(request, 'core/my_donations.html', {'donations': donations})


# 🏢 NGO: Update Profile
@login_required
def update_ngo_profile(request):
    ngo = get_object_or_404(NGO, user=request.user)
    if request.method == 'POST':
        form = NGOForm(request.POST, instance=ngo)
        if form.is_valid():
            form.save()
            messages.success(request, "NGO profile updated successfully!")
            return redirect('dashboard')
    return redirect('dashboard')

# ?? Update Profile (Volunteer/Donor)
@login_required
def update_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
    return redirect('dashboard')


# 🧪 Test Email View (Using SendGrid API)
def test_email(request):
    from django.http import HttpResponse
    from .utils import send_sendgrid_email
    from django.conf import settings
    
    success = send_sendgrid_email(
        subject="Blessing Boxes API Test",
        message="If you see this, the SendGrid HTTP API is working!",
        recipient_list=[settings.DEFAULT_FROM_EMAIL]
    )
    
    if success:
        return HttpResponse("✅ SUCCESS: Test email sent via API! Check your inbox.")
    else:
        return HttpResponse("❌ FAILED: Check Render logs for the SendGrid API error.")
