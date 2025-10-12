import json
import traceback
from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import ChatHistory
from .forms import ChatForm
# from rag_components.rag_chain import get_rag_response
from rag_components.llm_and_rag import get_rag_response
from accounts.models import Account as User


@login_required
def index(request):
    # if hasattr(request.user, "is_health_worker") and request.user.is_health_worker:
    #     return redirect('documents:dashboard')

    chat_form = ChatForm()
    recent_chats = ChatHistory.objects.filter(user=request.user).order_by('-timestamp')[:10]

    context = {
        'chat_form': chat_form,
        'recent_chats': recent_chats,
    }
    return render(request, 'chat/index.html', context)


@login_required
@require_POST
def send_message(request):
    # if hasattr(request.user, "is_health_worker") and request.user.is_health_worker:
    #     return JsonResponse({'error': 'Health workers cannot chat with the bot'}, status=403)

    form = ChatForm(request.POST)
    if form.is_valid():
        question = form.cleaned_data['message']
        try:
            # Fixed: ensure RAG chain returns correctly
            response = get_rag_response(question)

            chat_history = ChatHistory.objects.create(
                user=request.user,
                question=question,
                answer=response['answer']
            )

            return JsonResponse({
                'success': True,
                'question': question,
                'answer': response['answer'],
                'timestamp': chat_history.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'sources': response.get('sources', [])
            })
        except Exception as e:
            print("Error in send_message:", str(e))
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': "I'm sorry, I encountered an error while processing your question. Please try again later."
            }, status=500)

    return JsonResponse({'error': 'Invalid form'}, status=400)


@login_required
def chat_history(request):
    # if hasattr(request.user, "is_health_worker") and request.user.is_health_worker:
    #     return redirect('documents:dashboard')

    chats = ChatHistory.objects.filter(user=request.user).order_by('-timestamp')

    search_query = request.GET.get('search', '')
    if search_query:
        chats = chats.filter(Q(question__icontains=search_query) | Q(answer__icontains=search_query))

    date_filter = request.GET.get('date', '')
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            next_day = filter_date + timedelta(days=1)
            chats = chats.filter(timestamp__gte=filter_date, timestamp__lt=next_day)
        except ValueError:
            pass

    context = {
        'chats': chats,
        'search_query': search_query,
        'date_filter': date_filter,
    }
    return render(request, 'chat/chat_history.html', context)


@login_required
@require_POST
def delete_chat(request, chat_id):
    chat = get_object_or_404(ChatHistory, id=chat_id, user=request.user)
    chat.delete()
    messages.success(request, 'Chat deleted successfully.')
    return redirect('chat:chat_history')


@login_required
@require_POST
def clear_chat_history(request):
    # if hasattr(request.user, "is_health_worker") and request.user.is_health_worker:
    #     return JsonResponse({'error': 'Health workers cannot clear chat history'}, status=403)

    ChatHistory.objects.filter(user=request.user).delete()
    messages.success(request, 'Chat history cleared successfully.')
    return redirect('chat:chat_history')


@login_required
def export_chat_history(request):
    # if hasattr(request.user, "is_health_worker") and request.user.is_health_worker:
    #     return redirect('documents:dashboard')

    chats = ChatHistory.objects.filter(user=request.user).order_by('timestamp')
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="chat_history_{request.user.username}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.txt"'

    for chat in chats:
        response.write(f"\n{'='*50}\n")
        response.write(f"Date: {chat.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
        response.write(f"You: {chat.question}\n")
        response.write(f"Bot: {chat.answer}\n")

    return response


@login_required
def villager_history(request):
    if not hasattr(request.user, "is_health_worker") or not request.user.is_health_worker:
        return redirect('chat:index')

    villagers = User.objects.filter(role='villager')
    chats = ChatHistory.objects.all().order_by('-timestamp')

    villager_id = request.GET.get('villager', '')
    date_filter = request.GET.get('date', '')
    search_query = request.GET.get('search', '')

    if villager_id:
        chats = chats.filter(user_id=villager_id)

    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            next_day = filter_date + timedelta(days=1)
            chats = chats.filter(timestamp__gte=filter_date, timestamp__lt=next_day)
        except ValueError:
            pass

    if search_query:
        chats = chats.filter(Q(question__icontains=search_query) | Q(answer__icontains=search_query))

    context = {
        'villagers': villagers,
        'chats': chats,
        'villager_id': villager_id,
        'date_filter': date_filter,
        'search_query': search_query,
    }
    return render(request, 'chat/villager_history.html', context)


@login_required
def export_villager_history(request):
    if not hasattr(request.user, "is_health_worker") or not request.user.is_health_worker:
        return redirect('chat:index')

    villager_id = request.GET.get('villager', '')
    date_filter = request.GET.get('date', '')
    search_query = request.GET.get('search', '')

    chats = ChatHistory.objects.all().order_by('timestamp')

    if villager_id:
        chats = chats.filter(user_id=villager_id)

    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            next_day = filter_date + timedelta(days=1)
            chats = chats.filter(timestamp__gte=filter_date, timestamp__lt=next_day)
        except ValueError:
            pass

    if search_query:
        chats = chats.filter(Q(question__icontains=search_query) | Q(answer__icontains=search_query))

    response = HttpResponse(content_type='text/plain')
    filename = f"villager_chat_history_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
    if villager_id:
        try:
            villager = User.objects.get(id=villager_id)
            filename = f"{villager.username}_chat_history_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        except User.DoesNotExist:
            pass
    response['Content-Disposition'] = f'attachment; filename="{filename}.txt"'

    for chat in chats:
        response.write(f"\n{'='*50}\n")
        response.write(f"User: {chat.user.username}\n")
        response.write(f"Date: {chat.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
        response.write(f"Question: {chat.question}\n")
        response.write(f"Answer: {chat.answer}\n")

    return response
