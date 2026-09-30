from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.i18n import tr
from accounts.roles import citizen_required

from .ai import verify_image
from .forms import ComplaintForm
from .models import Complaint
from .task_views import build_task_context, load_task


@citizen_required
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

            messages.success(request, tr('Complaint #{id} submitted successfully.').format(id=complaint.id))
            messages.info(request, tr('The MC office will review your complaint shortly.'))
            if complaint.ai_verified is False:
                messages.warning(
                    request,
                    tr('Our AI could not clearly detect waste in this photo, '
                       'so the complaint was flagged for manual review.')
                )
            return redirect('complaint_detail', pk=complaint.pk)
    else:
        profile = request.user.profile
        form = ComplaintForm(initial={'city': profile.city, 'state': profile.state, 'pincode': profile.pincode})
    return render(request, 'complaints/report.html', {'form': form})


@citizen_required
def my_complaints(request):
    complaints = Complaint.objects.filter(user=request.user)
    return render(request, 'complaints/my_complaints.html', {'complaints': complaints})


@login_required
def complaint_detail(request, pk):
    complaint = load_task(request, 'complaint', pk)
    return render(request, 'complaints/detail.html', build_task_context(request, complaint))
