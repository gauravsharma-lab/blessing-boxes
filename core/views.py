from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages

from .models import FoodDonation, Profile, NGO
from .forms import FoodDonationForm, SignupForm, LoginForm
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
            messages.success(request, f"Welcome {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password")

    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})


# 🚪 Logout View
@login_required(login_url='login')
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
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

            #  CHECK EMAIL HERE (CORRECT PLACE)
            email = form.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                messages.error(request, "Account already exists with this email.")
                return redirect('login')

            #  CREATE USER
            user = form.save()

            # CREATE PROFILE WITH ROLE
            profile, created = Profile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()

            # LOGIN USER
            login(request, user)

            # CLEAR SESSION ROLE
            request.session.pop('selected_role', None)

            return redirect('dashboard')

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = SignupForm()

    return render(request, 'core/signup.html', {'form': form})

# 📊 Dashboard (Role-based)
@login_required(login_url='login')
def dashboard(request):

    # ✅ FIX: Ensure profile exists for all users
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'role': 'donor'}
    )

    role = profile.role

    if role == 'donor':
        donations = FoodDonation.objects.filter(donor=request.user)
        return render(request, 'core/donor_dashboard.html', {'donations': donations})

    elif role == 'volunteer':
        donations = FoodDonation.objects.all()
        return render(request, 'core/volunteer_dashboard.html', {'donations': donations})

    elif role == 'ngo':
        donations = FoodDonation.objects.all()
        return render(request, 'core/ngo_dashboard.html', {'donations': donations})

    elif role == 'manager':
        donations = FoodDonation.objects.all()
        return render(request, 'core/manager_dashboard.html', {'donations': donations})

    return redirect('homepage')


# 🍱 Donate Food
 


@login_required(login_url='login')
def donate_food(request):
    if request.method == 'POST':
        form = FoodDonationForm(request.POST)

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

            #  phone number 
            donation.phone_number = request.POST.get('phone_number')

            donation.save()

            messages.success(request, "Donation submitted successfully!")
            return redirect('dashboard')

        else:
            print(form.errors)  # 👈 DEBUG (VERY IMPORTANT)
            messages.error(request, "Fix errors below")

    else:
        form = FoodDonationForm()

    return render(request, 'core/donate.html', {'form': form})

# 🚚 Accept Delivery (Volunteer)
@login_required(login_url='login')
def accept_delivery(request, donation_id):
    donation = get_object_or_404(FoodDonation, id=donation_id)

    profile = request.user.profile

   
    if profile.role == 'ngo':
        ngo = NGO.objects.filter(user=request.user).first()

        pending_donations = FoodDonation.objects.filter(status='Pending')
        accepted_donations = FoodDonation.objects.filter(assigned_ngo=ngo)

        return render(request, 'core/ngo_dashboard.html', {
            'pending_donations': pending_donations,
            'accepted_donations': accepted_donations
        })
    elif profile.role == 'volunteer':
        donation.assigned_volunteer = request.user
        donation.status = "Picked"

    donation.save()

    messages.success(request, "Donation accepted successfully!")
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
            send_mail(
                subject="New Contact Message - BlessingBoxes",
                message=full_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.EMAIL_HOST_USER],
            )
        except:
            # If email fails, still continue (for now)
            pass

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

        return redirect("ngo_dashboard")

    return render(request, "core/add_donation.html")