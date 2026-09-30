from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .forms import PickupForm
from .models import PickupRequest


@login_required
def request_pickup(request):
    if request.method == 'POST':
        form = PickupForm(request.POST)
        if form.is_valid():
            pickup = form.save(commit=False)
            pickup.user = request.user
            pickup.save()
            messages.success(request, f'Pickup request #{pickup.id} submit ho gayi.')
            return redirect('my_pickups')
    else:
        form = PickupForm()
    return render(request, 'pickups/request.html', {'form': form})


@login_required
def my_pickups(request):
    pickups = PickupRequest.objects.filter(user=request.user)
    return render(request, 'pickups/my_pickups.html', {'pickups': pickups})


@login_required
@require_POST
def cancel_pickup(request, pk):
    pickup = get_object_or_404(PickupRequest, pk=pk, user=request.user)
    if pickup.status == 'pending':
        pickup.status = 'cancelled'
        pickup.save(update_fields=['status'])
        messages.info(request, f'Pickup #{pickup.id} cancel ho gayi.')
    return redirect('my_pickups')