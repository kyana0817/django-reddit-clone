from operator import ge
from re import template
from sys import flags
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.urls.base import reverse, reverse_lazy
from django.shortcuts import render, redirect
from django.db.models import Sum, Count,Prefetch
from django.views import generic
from communities.models import Communities
from users.models import User
from .models import NewsPosts, Comment, Notification, Vote, Replay
from .forms import CreateCommentForm, CreatePostForm, NewsPostEditForm, CreateReplayForm
from django.contrib.auth.decorators import login_required
from django.db import transaction
# Create your views here.

class IndexView(generic.ListView):
    model = NewsPosts
    template_name = 'news_posts/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_list'] = NewsPosts.objects.order_by('-created_at').annotate(vote_count=Sum('voted_post__flag'))
        context['vote_list'] = Vote.objects.filter(voted_user_id=self.request.user.id)
        context['communities_list'] = Communities.objects.order_by('-created_at')
        context['saved_posts'] = NewsPosts.objects.filter(saved_user=self.request.user.id)
        return context

class CreatePostView(LoginRequiredMixin, generic.View):
    model = NewsPosts
    form_class = CreatePostForm
    template_name = 'news_posts/create_post.html'
    success_url = reverse_lazy('news_posts:index')

    def get(self, request, *args, **kwargs):
        form = self.form_class(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = CreatePostForm(user=request.user, data=request.POST)

        post_data = form.save(commit=False)
        post_data.user = get_user_model().objects.get(id=request.user.id)
        post_data.photo = request.FILES.get('photo')
        post_data.save()
        return redirect('news_posts:index')

    def get_queryset(self):
        return Communities.objects.all()


class DeletePostView(LoginRequiredMixin, generic.DeleteView):
    model = NewsPosts
    success_url = reverse_lazy('news_posts:index')

class DeleteLoginUserPostView(LoginRequiredMixin, generic.DeleteView):
    model = NewsPosts
    def get_success_url(self):
        return reverse('users:detail', kwargs={'pk': self.request.user.id})

class DeleteNotificationView(LoginRequiredMixin, generic.DeleteView):
    model = Notification
    def get_success_url(self):
        return reverse('news_posts:notification', kwargs={'pk': self.request.user.id})

class DeleteCommentView(LoginRequiredMixin, generic.DeleteView):
    model = Comment
    def get_success_url(self):
        comment_pk = self.kwargs['pk']
        comment = get_object_or_404(Comment, pk=comment_pk)
        post_pk = comment.target.id
        return reverse('news_posts:post_detail', kwargs={'pk': post_pk})

class NewsPostDetailView(LoginRequiredMixin, generic.DetailView):
    model = NewsPosts
    template_name = 'news_posts/post_detail.html'
    def get_context_data(self, **kwargs):
        post_pk = self.kwargs['pk']
        post = NewsPosts.objects.get(id=post_pk)
        context = super().get_context_data(**kwargs)
        context['comment_list'] = Comment.objects.filter(target=post_pk)
        context['member_count'] = User.objects.filter(member=post.community).count()
        context['community_post_count'] = NewsPosts.objects.filter(community_id=post.community).count()
        context['saved_posts'] = NewsPosts.objects.filter(saved_user=self.request.user.id)
        return context


class NewsPostEditView(LoginRequiredMixin, generic.UpdateView):
    model = NewsPosts
    form_class = NewsPostEditForm
    template_name = 'news_posts/post_edit.html'
    def get_success_url(self):
        post_pk = self.kwargs['pk']
        return reverse('news_posts:post_detail', kwargs={'pk': post_pk})

    def get_context_data(self, **kwargs):
        post_pk = self.kwargs['pk']
        post = NewsPosts.objects.get(id=post_pk)
        context = super().get_context_data(**kwargs)
        context['member_count'] = User.objects.filter(member=post.community).count()
        context['community_post_count'] = NewsPosts.objects.filter(community_id=post.community).count()
        context['saved_posts'] = NewsPosts.objects.filter(saved_user=self.request.user.id)
        return context


class CreateCommentView(LoginRequiredMixin, generic.CreateView):
    template_name = 'news_posts/create_comment.html'
    form_class = CreateCommentForm
    model = Comment

    # def post(self, request):
    #     form = CreateCommentForm(request.POST)

    #     get_user_id = form.save(commit=False)
    #     get_user_id.user = get_user_model().objects.get(id=request.user.id)
    #     get_user_id.save()
    #     return redirect('news_posts:index')

    def form_valid(self, form):
        # このメソッドの中にあるコメントは対象のコメントを削除した時に通知も削除されるようにするための試みであったが、できなかったので今後実装するかもしれない
        post_pk = self.kwargs['pk']
        post = get_object_or_404(NewsPosts, pk=post_pk)
        comment = form.save(commit=False)
        notification = Notification
        title = self.request.user.username + "が      " + post.title + "      に対してコメントした"
        # comment_notification = notification.objects.filter(title=title, message=comment.content, destination=post.user)
        comment.target = post
        comment.user = get_user_model().objects.get(id=self.request.user.id)
        comment.save()
        # comment_query = Comment.objects.filter(
        #     target=post,
        #     user=get_user_model().objects.get(id=self.request.user.id),
        #     content=comment.content
        # )
        notification.objects.create(title=title, message=comment.content, destination=post.user)
        # if not comment_query:
        #     comment_notification.delete()
        return redirect('news_posts:post_detail', pk=post_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['target_post'] = get_object_or_404(NewsPosts, pk=self.kwargs['pk'])
        return context


@login_required
@transaction.atomic
def vote_up(request, pk):
    # print('up')
    post = NewsPosts.objects.get(pk=pk)
    vote = Vote.objects.filter(voted_user=request.user, voted_post=post).first()
    notification = Notification
    message = request.user.username + "が      " + post.title + "      を賛成した。"
    vote_notification = notification.objects.filter(title="vote通知", message=message, destination=post.user)
    if not vote:
        vote = Vote()
        # print('up, none')
        vote.voted_user = request.user
        vote.voted_post = post
        vote.flag = 0
    if vote.flag <= 0:
        # print('up, -1 or 0')
        vote.flag += 1
        post.vote += 1
        if not vote_notification:
            notification.objects.create(title="vote通知", message=message, destination=post.user)
    else:
        # print('up, 1')
        vote.flag -= 1
        post.vote -= 1
    vote.save()
    post.save()
    return redirect('news_posts:index')

@login_required
@transaction.atomic
def vote_down(request, pk):
    # print('down')
    post = NewsPosts.objects.get(pk=pk)
    vote = Vote.objects.filter(voted_user=request.user, voted_post=post).first()
    if not vote:
        # print('down, none')
        vote = Vote()
        vote.voted_user = request.user
        vote.voted_post = post
        vote.flag = 0
    if vote.flag >= 0:
        # print('down, 0 or 1')
        vote.flag -= 1
        post.vote -= 1
    else:
        # print('down, -1')
        vote.flag += 1
        post.vote += 1
    vote.save()
    post.save()
    return redirect('news_posts:index')

class CreateReplayView(LoginRequiredMixin, generic.CreateView):
    model = Replay
    form_class = CreateReplayForm
    template_name = "news_posts/create_replay.html"

    def form_valid(self, form):
        comment_pk = self.kwargs['pk']
        comment = get_object_or_404(Comment, pk=comment_pk)
        post_pk = comment.target.id
        replay = form.save(commit=False)
        replay.target = comment
        replay.user = get_user_model().objects.get(id=self.request.user.id)
        replay.save()
        comment.replay.add(replay)
        return redirect('news_posts:post_detail', pk=post_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['target_comment'] = get_object_or_404(Comment, pk=self.kwargs['pk'])
        return context

class NotificationListView(LoginRequiredMixin, generic.ListView):
    model = Notification
    template_name = 'notification/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notification_list'] = Notification.objects.filter(destination=self.request.user).order_by("-created_at")
        return context

class SavePostView(LoginRequiredMixin, generic.View):
    model = NewsPosts

    def get(self, request, *args, **kwargs):
        post = NewsPosts.objects.get(pk=self.kwargs['pk'])
        user = User.objects.get(id=request.user.id)
        user.saved_post.add(post)
        return redirect('users:saved_posts', pk=self.request.user.id)

class UnSavePostView(LoginRequiredMixin, generic.View):
    model = NewsPosts

    def get(self, request, *args, **kwargs):
        post = NewsPosts.objects.get(pk=self.kwargs['pk'])
        user = User.objects.get(id=request.user.id)
        user.saved_post.remove(post)
        return redirect('users:saved_posts', pk=self.request.user.id)

class DeleteReplayView(LoginRequiredMixin, generic.DeleteView):
    model = Replay
    success_url = reverse_lazy('news_posts:index')
    def get_success_url(self):
        replay_pk = self.kwargs['pk']
        replay = get_object_or_404(Replay, pk=replay_pk)
        comment_pk = replay.target.id
        comment = get_object_or_404(Comment, pk=comment_pk)
        post_pk = comment.target.id
        return reverse('news_posts:post_detail', kwargs={'pk': post_pk})
