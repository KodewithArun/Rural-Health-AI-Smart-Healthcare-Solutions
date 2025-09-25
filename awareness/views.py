from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from .models import Awareness

def awareness_list(request):
    awareness_items = Awareness.objects.all().order_by('-created_at')
    
    # Pagination (6 per page)
    paginator = Paginator(awareness_items, 6)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'awareness/awareness_list.html', {'page_obj': page_obj})

def awareness_detail(request, pk):
    awareness_item = get_object_or_404(Awareness, pk=pk)
    return render(request, 'awareness/awareness_detail.html', {'awareness_item': awareness_item})
