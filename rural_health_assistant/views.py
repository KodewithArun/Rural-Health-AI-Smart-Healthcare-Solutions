from django.shortcuts import render
from awareness.models import Awareness


def home(request):
    awareness = Awareness.objects.all().order_by('-created_at')[:6]
    context = {'awareness': awareness}
    return render(request, 'home.html', context)

