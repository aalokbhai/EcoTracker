from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.i18n import tr
from accounts.roles import citizen_required
from complaints.task_views import build_task_context, load_task

from .forms import PickupForm
from .models import PickupRequest


@citizen_required
def request_pickup(request):
    if request.method == 'POST':
        form = PickupForm(request.POST)
        if form.is_valid():
            pickup = form.save(commit=False)
            pickup.user = request.user
            pickup.save()
            messages.success(request, tr('Pickup request #{id} submitted successfully.').format(id=pickup.id))
            messages.info(request, tr('The MC office will review your request shortly.'))
            return redirect('pickup_detail', pk=pickup.pk)
    else:
        profile = request.user.profile
        form = PickupForm(initial={'city': profile.city, 'state': profile.state, 'pincode': profile.pincode})
    return render(request, 'pickups/request.html', {'form': form})


@citizen_required
def my_pickups(request):
    pickups = PickupRequest.objects.filter(user=request.user)
    return render(request, 'pickups/my_pickups.html', {'pickups': pickups})


@login_required
def pickup_detail(request, pk):
    pickup = load_task(request, 'pickup', pk)
    return render(request, 'pickups/detail.html', build_task_context(request, pickup))
