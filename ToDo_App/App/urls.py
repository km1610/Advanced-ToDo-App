from django.urls import path
from .views import *

urlpatterns = [
    path('register/', register_user, name='register'),
    path('login/', user_login, name='login'), # Save Auth Token when generated
    path('logout/', user_logout, name='logout'), # Auth Token required to put in Header as shown
    path('users/', usersViewSet, name='getusers'), # Auth Token required to put in Header as shown
    path('projects/', project, name='projects'),  # Auth Token required to put in Header as shown
    path('tasks/', task, name='tasks'),  # Auth Token required to put in Header as shown
    path('add_dependency/', add_dependency, name='add_dependency'), # Auth Token required to put in Header as shown
    path('assign_task/', assign_task, name='assign_task'), # Auth Token required to put in Header as shown
    path('tasks/assigned/', assigned_task, name='assigned_task'), # Auth Token required to put in Header as shown
    path('view_schedule/', view_schedule, name='view_schedule'), # Auth Token required to put in Header as shown
]