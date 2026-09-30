from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from .forms import ComplaintForm
from .models import Complaint
from .ai import verify_image


@login_required
def report_complaint(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()

            # CNN verification
            if complaint.image:
                verified, confidence = verify_image(complaint.image.path)
                complaint.ai_verified = verified
                complaint.ai_confidence = confidence
                complaint.save(update_fields=['ai_verified', 'ai_confidence'])

            messages.success(request, f'Complaint #{complaint.id} submit ho gayi.')
            return redirect('complaint_detail', pk=complaint.pk)
    else:
        form = ComplaintForm()
    return render(request, 'complaints/report.html', {'form': form})


@login_required
def my_complaints(request):
    complaints = Complaint.objects.filter(user=request.user)
    return render(request, 'complaints/my_complaints.html', {'complaints': complaints})


@login_required
def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    if complaint.user != request.user and not request.user.is_staff:
        raise PermissionDenied
    return render(request, 'complaints/detail.html', {'complaint': complaint})