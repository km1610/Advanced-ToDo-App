from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import *
from .models import *
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

@api_view(['POST'])
def register_user(request):
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def user_login(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')

        user = None
        if '@' in username:
            try:
                user = User.objects.get(email=username)
            except ObjectDoesNotExist:
                pass

        if not user:
            user = authenticate(username=username, password=password)

        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    if request.method == 'POST':
        try:
            request.user.auth_token.delete()
            return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def usersViewSet(request):
    if request.method == 'GET':
        try:
            Users = User.objects.all().order_by('-date_joined')
            serializer = UserSerializer(Users, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST', 'GET'])
def project(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            serializer = ProjectSerializer(data=request.data, context={'request':request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        try:
            projects = Project.objects.all()
            serializer = ProjectSerializer(projects, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST', 'GET', 'PUT'])
@permission_classes([IsAuthenticated])
def task(request):
    if request.method == 'POST':
        try:
            serializer = TaskSerializer(data=request.data, context={'request':request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if request.method == 'GET':
        try:
            assigned_tasks = Assignment.objects.filter(assignee = request.user).values_list('task_id', flat=True)
            tasks = Task.objects.filter(parentTask=None, owner=request.user) | Task.objects.filter(parentTask=None, visibility=True) | Task.objects.filter(parentTask=None, task_id__in = assigned_tasks)
            serializer = TaskSerializer(tasks, many=True, context={'request':request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    if request.method == 'PUT':
        if len(request.data)==2 and 'completed' in request.data and 'task_id' in request.data:
            task_id = request.data['task_id']
            task = Task.objects.get(task_id=task_id)
            assigned = False
            assigned_users = Assignment.objects.filter(task=task)
            for user in assigned_users:
                if user.assignee == request.user:
                    assigned = True
                    break
            if request.user!=task.owner and not assigned:
                return Response({'error': 'Unauthorized access to task completion'}, status=status.HTTP_400_BAD_REQUEST)
        
            if request.data['completed']:
                subtasks = Task.objects.filter(parentTask=task)
                for subtask in subtasks:
                    if not subtask.completed:
                        return Response({'error': 'Cannot complete task with subtasks incomplete'}, status=status.HTTP_400_BAD_REQUEST)

            dependecies = Dependency.objects.filter(task=task)
            for dependency in dependecies:
                dependants = dependency.dependent_tasks.all()
                for dependant in dependants:
                    if not dependant.completed:
                        return Response({'error': 'Cannot complete task with dependents incomplete'}, status=status.HTTP_400_BAD_REQUEST)


            task.completed = request.data['completed']
            task.save()

            parent_task = task.parentTask

            visited_tasks = set()
            
            while parent_task:
               
                subtasks = Task.objects.filter(parentTask=parent_task)
                parent_task_complete = True
                
                for subtask in subtasks:
                    if not subtask.completed:
                        parent_task_complete = False

                if parent_task_complete:
                    parent_task.completed = True
                    parent_task.save()

                parent_task = parent_task.parentTask

            return Response({'response': 'Data for task ' + str(task_id) + ' was successfully updated'}, status=status.HTTP_201_CREATED)
        return Response({"error: This method is only for setting task completion"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_dependency(request):
    if request.method == 'POST':
        try:
            serializer = DependencySerializer(data=request.data, context={'request':request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST', 'PUT'])
@permission_classes([IsAuthenticated])
def assign_task(request):
    if request.method == 'POST':
        try:
            serializer = AssignmentSerializer(data=request.data, context={'request':request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from collections import defaultdict
from collections import deque
def build_dag(tasks):
    graph = defaultdict(list)
    in_degree = defaultdict(int)

    for dep in Dependency.objects.filter(task__in=tasks):
        for dependent_task in dep.dependent_tasks.all():

            graph[dependent_task.task_id].append(dep.task_id)
            in_degree[dep.task_id] += 1
            in_degree[dependent_task.task_id] += 0
    return graph, in_degree


def topological_sort(tasks, graph, in_degree):
    queue = deque()
    sorted_task_ids = []

    for task in tasks:
        if in_degree[task.task_id] == 0:
            queue.append(task.task_id)

    while queue:
        task_id = queue.popleft()
        sorted_task_ids.append(task_id)

        for dependent_task_id in graph[task_id]:
            in_degree[dependent_task_id] -= 1

            if in_degree[dependent_task_id] == 0:
                queue.append(dependent_task_id)

    if len(sorted_task_ids) != len(tasks):
        raise ValueError("A cycle was detected in the task dependencies.")

    return sorted_task_ids

def calculate_schedule(tasks, sorted_task_ids, graph):
    task_map = {task.task_id: task for task in tasks}
    for task_id in sorted_task_ids:
        task = task_map[task_id]
        dependencies = Dependency.objects.filter(task=task)
        if dependencies.exists():
            dependency_end_date = task.start_date

            for dep in dependencies:
                condition = dep.condition
                dependent_end_dates = [
                    dependency_task.end_date
                    for dependency_task in dep.dependent_tasks.all()
                    if dependency_task.end_date
                ]

                if condition == "AND":
                    dependency_end_date = max(dependent_end_dates)
                elif condition == "OR":
                    dependency_end_date = min(dependent_end_dates)

                task.start_date = max(task.start_date, dependency_end_date)

        task.end_date = task.start_date + timedelta(days=task.duration)
        task.save()

def adjust_subtasks(task):

    subtasks = Task.objects.filter(parentTask=task)

    for subtask in subtasks:
        subtask.start_date = max(task.start_date, subtask.start_date)
        subtask.end_date = subtask.start_date + timedelta(days=subtask.duration)
        subtask.save()
        adjust_subtasks(subtask)

def adjust_parent_tasks(task):

    parent_task = task.parentTask
    ed = task.end_date

    while parent_task:
        parent_task.end_date = max(parent_task.end_date, ed)
        parent_task.save() 
        ed = parent_task.end_date
        parent_task = parent_task.parentTask


def schedule(project_id):
    tasks = Task.objects.filter(project=project_id)

    graph, in_degree = build_dag(tasks)

    sorted_task_ids = topological_sort(tasks, graph, in_degree)

    calculate_schedule(tasks, sorted_task_ids, graph)

    for task in tasks:
        adjust_subtasks(task)
        adjust_parent_tasks(task)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def assigned_task(request):

    if request.method == 'GET':
        try:
            assigned_tasks = Assignment.objects.filter(assignee = request.user).values_list('task_id', flat=True)
            projects = set()
            for task_id in assigned_tasks:
                task = Task.objects.get(task_id=task_id)
                projects.add(task.project.project_id)

            for project in projects:
                schedule(project)

            tasks = Task.objects.filter(parentTask=None, task_id__in = assigned_tasks) | Task.objects.filter(task_id__in = assigned_tasks)
            serializer = AssignedTaskSerializer(tasks, many=True, context={'request':request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_schedule(request):

    if request.method == 'GET':
        try:
            assigned_tasks = Assignment.objects.filter(assignee = request.user).values_list('task_id', flat=True)
            projects = set()
            for task_id in assigned_tasks:
                task = Task.objects.get(task_id=task_id)
                projects.add(task.project.project_id)
            for project in projects:
                schedule(project)


            end_date_duration = []
            for project in projects:
                time = []
                tasks = Task.objects.filter(project=project)
                end_dates = []
                duration = []
                for task in tasks:
                    duration.append(task.duration)
                    end_dates.append(task.end_date)
                time.append(max(end_dates))
                time.append(max(duration))
                time.append(project)
                end_date_duration.append(time)

            end_date_duration.sort()
            view_data = {}
            proj_ind = 1

            for edd in end_date_duration:
                end_date, duration, project_id = edd
                project = Project.objects.get(project_id = project_id)
                serializer = ScheduleSerializer(project, context={'request':request, 'duration':duration, 'end_date':end_date})
                view_data[proj_ind] = serializer.data
                proj_ind += 1

            return Response(view_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
