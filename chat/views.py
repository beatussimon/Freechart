from django.views.generic import ListView, DetailView, FormView, CreateView, UpdateView, TemplateView
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Chat, Message, ReadReceipt, UserProfile, UserProfile
from .forms import MessageForm, SearchForm, RegisterForm, GroupCreateForm, UserProfileForm
from django.forms import forms

class LandingPageView(TemplateView):
    template_name = 'chat/landing_page.html'

class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('auth:login')  # Updated from 'login'

    def form_valid(self, form):
        response = super().form_valid(form)
        UserProfile.objects.create(user=self.object)
        return response

class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'chat/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        queryset = User.objects.exclude(id=self.request.user.id)
        query = self.request.GET.get('query')
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) | Q(email__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET)
        return context

class ChatListView(LoginRequiredMixin, ListView):
    model = Chat
    template_name = 'chat/chat_list.html'
    context_object_name = 'chats'

    def get_queryset(self):
        return self.request.user.chats.all().prefetch_related('messages', 'participants__profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET)
        query = self.request.GET.get('query')
        if query:
            context['chats'] = context['chats'].filter(
                Q(name__icontains=query) | Q(messages__content__icontains=query)
            ).distinct()
        for chat in context['chats']:
            if not chat.is_group:
                chat.other_user = chat.participants.exclude(id=self.request.user.id).first()
        return context

class ChatDetailView(LoginRequiredMixin, DetailView, FormView):
    model = Chat
    template_name = 'chat/chat_detail.html'
    context_object_name = 'chat'
    form_class = MessageForm

    def get_queryset(self):
        return Chat.objects.filter(participants=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = self.object.messages.filter(is_deleted=False).select_related('sender__profile')
        context['read_receipts'] = {rr.message_id: rr.user.username for rr in ReadReceipt.objects.filter(message__chat=self.object)}
        if not self.object.is_group:
            other_user = self.object.participants.exclude(id=self.request.user.id).first()
            context['other_user'] = other_user if other_user else None
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            msg = form.save(commit=False)
            msg.chat = self.object
            msg.sender = request.user
            msg.save()
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse('chat:chat_detail', kwargs={'pk': self.object.pk})

class StartChatView(LoginRequiredMixin, CreateView):
    model = Chat
    fields = []
    template_name = 'chat/user_list.html'

    def post(self, request, *args, **kwargs):
        other_user = get_object_or_404(User, id=self.kwargs['user_id'])
        chat = Chat.objects.filter(is_group=False, participants=self.request.user).filter(participants=other_user).first()
        if not chat:
            chat = Chat.objects.create(is_group=False)
            chat.participants.set([request.user, other_user])
        return redirect('chat:chat_detail', pk=chat.pk)

class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Chat
    form_class = GroupCreateForm
    template_name = 'chat/group_create.html'
    success_url = reverse_lazy('chat:chat_list')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.is_group = True
        self.object.save()
        self.object.participants.add(self.request.user)
        self.object.admins.add(self.request.user)
        for participant in form.cleaned_data['participants']:
            self.object.participants.add(participant)
        return super().form_valid(form)

class GroupInviteView(LoginRequiredMixin, UpdateView):
    model = Chat
    fields = ['participants']
    template_name = 'chat/group_invite.html'
    success_url = reverse_lazy('chat:chat_list')

    def get_form(self, **kwargs):
        form = super().get_form(**kwargs)
        form.fields['participants'].queryset = User.objects.exclude(id__in=self.object.participants.all())
        form.fields['participants'].widget = forms.CheckboxSelectMultiple(attrs={'class': 'mt-2'})
        return form

    def form_valid(self, form):
        self.object = form.save(commit=False)
        for participant in form.cleaned_data['participants']:
            self.object.participants.add(participant)
        self.object.save()
        return super().form_valid(form)

    def get_queryset(self):
        return Chat.objects.filter(admins=self.request.user, is_group=True)
    

class ProfileView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = 'chat/profile.html'
    context_object_name = 'profile'

    def get_object(self):
        return self.request.user.profile

class EditProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'chat/edit_profile.html'
    success_url = reverse_lazy('chat:profile')

    def get_object(self):
        return self.request.user.profile