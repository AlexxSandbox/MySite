from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('', views.index, name='index'),
    path('new/', views.new_post, name='new_post'),

    path('api/v1/posts/', views.api_posts),
    path('api/v1/posts/<int:id>/', views.api_posts_detail),
    path('api/v1/api-token-auth/', obtain_auth_token),

    path('group/<slug:slug>/', views.group_posts, name='group'),
    path('follow/', views.follow_index, name='follow_index'),
    path('<str:username>/', views.profile, name='profile'),
    path('<str:username>/follow/', views.profile_follow, name='profile_follow'),
    path('<str:username>/unfollow/', views.profile_unfollow, name='profile_unfollow'),
    path('<str:username>/<int:post_id>/', views.post_view, name='post'),
    path('<str:username>/<int:post_id>/edit', views.post_edit, name='post_edit'),
    path('<str:username>/<int:post_id>/comment', views.add_comment, name='add_comment'),
    path('<str:username>/<int:post_id>/delete', views.post_delete, name='post_delete'),
]
