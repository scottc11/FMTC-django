from django.shortcuts import render, get_object_or_404
from .models import Post

# Create your views here.
def home(request):
    posts = Post.objects.order_by('pub_date')
    context = { 'posts': posts }
    return render(request, 'posts/home.html', context)

def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    return render(request, 'posts/post_detail.html', {'post': post})
