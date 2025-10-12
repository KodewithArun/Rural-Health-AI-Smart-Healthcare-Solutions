import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.models import Account as User
from .models import Document
from .forms import DocumentUploadForm, DocumentUpdateForm
# from rag_components.vector_store_update import update_vector_db


def is_health_worker(user):
    return user.is_authenticated and user.is_health_worker

@login_required
@user_passes_test(is_health_worker)
def dashboard(request):
    # Get statistics for the dashboard
    total_documents = Document.objects.count()
    total_villagers = User.objects.filter(role='villager').count()
    
    # Get recent documents
    recent_documents = Document.objects.order_by('-updated_at')[:5]
    
    context = {
        'total_documents': total_documents,
        'total_villagers': total_villagers,
        'recent_documents': recent_documents,
    }
    return render(request, 'documents/dashboard.html', context)

@login_required
@user_passes_test(is_health_worker)
def document_list(request):
    documents = Document.objects.all().order_by('-updated_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        documents = documents.filter(title__icontains=search_query)
    
    context = {
        'documents': documents,
        'search_query': search_query,
    }
    return render(request, 'documents/document_list.html', context)

@login_required
@user_passes_test(is_health_worker)
def upload_document(request):
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            
            # Update vector database
            # try:
            #     update_vector_db()
            #     messages.success(request, 'Document uploaded successfully and vector database updated.')
            # except Exception as e:
            #     messages.error(request, f'Document uploaded but vector database update failed: {str(e)}')
            
            return redirect('documents:document_list')
    else:
        form = DocumentUploadForm()
    
    return render(request, 'documents/upload_document.html', {'form': form})

@login_required
@user_passes_test(is_health_worker)
def update_document(request, pk):
    document = get_object_or_404(Document, pk=pk)
    
    if request.method == 'POST':
        form = DocumentUpdateForm(request.POST, instance=document)
        if form.is_valid():
            form.save()
            
            # Update vector database
            # try:
            #     update_vector_db()
            #     messages.success(request, 'Document updated successfully and vector database updated.')
            # except Exception as e:
            #     messages.error(request, f'Document updated but vector database update failed: {str(e)}')
            
            return redirect('documents:document_list')
    else:
        form = DocumentUpdateForm(instance=document)
    
    return render(request, 'documents/update_document.html', {'form': form, 'document': document})

@login_required
@user_passes_test(is_health_worker)
@require_POST
def delete_document(request, pk):
    document = get_object_or_404(Document, pk=pk)
    
    # Delete the file from storage
    if document.file:
        document.file.delete()
    
    document.delete()
    
    # Update vector database
    # try:
    #     update_vector_db()
    #     messages.success(request, 'Document deleted successfully and vector database updated.')
    # except Exception as e:
    #     messages.error(request, f'Document deleted but vector database update failed: {str(e)}')
    
    return redirect('documents:document_list')

@login_required
@user_passes_test(is_health_worker)
def document_stats(request):
    # Get document statistics
    documents = Document.objects.annotate(query_count=Count('chathistory')).order_by('-query_count')
    
    context = {
        'documents': documents,
    }
    return render(request, 'documents/document_stats.html', context)



# documents/views.py (snippet)
@login_required
@user_passes_test(is_health_worker)
def upload_document(request):
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.uploaded_by = request.user
            doc.save()   # model.save will call add_file_to_vector_db
            messages.success(request, "Document uploaded and vector DB updated.")
            return redirect("documents:document_list")
    else:
        form = DocumentUploadForm()
    return render(request, "documents/upload_document.html", {"form": form})