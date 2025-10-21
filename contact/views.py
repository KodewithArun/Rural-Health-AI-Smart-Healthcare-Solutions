from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ContactEnquiry


@login_required
def my_enquiries(request):
    """View for users to see their own enquiries"""
    enquiries = ContactEnquiry.objects.filter(user=request.user)
    
    context = {
        'enquiries': enquiries,
    }
    return render(request, 'contact/my_enquiries.html', context)
