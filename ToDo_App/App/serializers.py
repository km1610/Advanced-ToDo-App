from rest_framework import serializers
from .models import *
from datetime import date, timedelta

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id','username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}, 'user_id': {'read_only': True}}

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['project_id','title', 'description', 'start_date']
        extra_kwargs = {'project_id': {'read_only': True}}
    def create(self, validated_data):
        project = Project(
            title=validated_data['title'],
            description=validated_data['description'],
            start_date=validated_data['start_date'],
            owner=self.context['request'].user
        )
        project.save()
        return project

class TaskSerializer(serializers.ModelSerializer):
    subtasks = serializers.SerializerMethodField()
    class Meta:
        model = Task
        fields = ['task_id','parentTask','project','title', 'description', 'duration', 'completed', 'subtasks', 'visibility']
        extra_kwargs = {
            'task_id': {'read_only': True},
            'completed': {'required': False},
            'project': {'required': False},
            'parentTask': {'required': False},
            }

    def get_subtasks(self, obj):
        user = self.context['request'].user
        assigned_tasks = Assignment.objects.filter(assignee = user).values_list('task_id', flat=True)    
        visible_tasks = obj.subtasks.filter(owner=user) | obj.subtasks.filter(visibility=True) | obj.subtasks.filter(task_id__in = assigned_tasks)
        return TaskSerializer(visible_tasks, many=True, read_only=True, context=self.context).data

    def create(self, validated_data):
        if 'project' not in validated_data:
            if 'parentTask' not in validated_data:
                raise ValueError("You must provide either project or parent task")
            pt = validated_data['parentTask']
            if validated_data['duration']>pt.duration:
                raise ValueError("Sub Task duration cannot be greater than Parent Task duration")
            while pt.parentTask:
                pt = pt.parentTask
            validated_data['project'] = pt.project

        project = Project.objects.get(project_id = validated_data['project'].project_id)
        sd = max(date.today(), project.start_date)
        ed = sd + timedelta(days=validated_data['duration'])

        task = Task(
            title=validated_data['title'],
            description=validated_data['description'],
            duration=validated_data['duration'],
            completed = False,
            project=validated_data['project'],
            parentTask=validated_data['parentTask'] if 'parentTask' in validated_data else None,
            visibility=validated_data['visibility'],
            owner=self.context['request'].user,
            start_date=sd,
            end_date=ed
        )
        task.save()
        
        parent_task = validated_data['parentTask'] if 'parentTask' in validated_data else None

        while parent_task:
            parent_task.end_date = max(parent_task.end_date, ed)
            parent_task.save() 
            ed = parent_task.end_date
            parent_task = parent_task.parentTask

        return task

class AssignedTaskSerializer(serializers.ModelSerializer):
    subtasks = serializers.SerializerMethodField()
    class Meta:
        model = Task
        fields = ['task_id','project','title','completed', 'subtasks','start_date', 'end_date',]
        extra_kwargs = {
            'task_id': {'read_only': True},
            'completed': {'required': False},
            'project': {'required': False},
            'start_date': {'read_only': False},
            'end_date': {'read_only': False},
            }

    def get_subtasks(self, obj):
        user = self.context['request'].user
        assigned_tasks = Assignment.objects.filter(assignee = user).values_list('task_id', flat=True)    
        visible_tasks = obj.subtasks.filter(task_id__in = assigned_tasks)
        return AssignedTaskSerializer(visible_tasks, many=True, read_only=True, context=self.context).data


class DependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Dependency
        fields = ['dependency_id','task','dependent_tasks','condition']
        extra_kwargs = {
            'dependency_id': {'read_only': True}
            }

    def create(self, validated_data):
        user = self.context['request'].user
        task = Task.objects.get(task_id=validated_data['task'].task_id)
        project = task.project
        for dependent_task in validated_data['dependent_tasks']:
            task_dependent_task = Task.objects.get(task_id=dependent_task.task_id)
            if task_dependent_task.project!=project:
                raise Exception('Dependent tasks must be of the same project as the depencies')

        dependent_tasks = set(validated_data['dependent_tasks'])
        parent_task = task.parentTask
        while parent_task:
            if parent_task in dependent_tasks:
                raise Exception('Parent task cannot be dependent on a sub-task')
            parent_task = parent_task.parentTask
        
        dependent_tasks = set(validated_data['dependent_tasks'])
        for dependent_task in dependent_tasks:
            parent_task = dependent_task.parentTask
            while parent_task:
                if parent_task == task:
                    raise Exception('Sub Task cannon be dependent on Parent Task. That is a given by default :(')
        
        if task.owner == user:
            dependency = Dependency(
                task=validated_data['task'],
                condition=validated_data['condition']
            )
            dependency.save()
            for dependent_task in validated_data['dependent_tasks']:
                dependency.dependent_tasks.add(dependent_task)

            

            if validated_data['condition'] == "AND":
                max_start_date = task.start_date
                for dependent_task in dependent_tasks:
                    max_start_date = max(max_start_date, dependent_task.end_date)
                task.start_date = max_start_date
                task.save()

            if validated_data['condition'] == "OR":
                min_start_date = task.start_date
                for dependent_task in dependent_tasks:
                    max_start_date = min(max_start_date, dependent_task.end_date)
                task.start_date = min_start_date
                task.save()

            return dependency

        raise Exception('Unauthorized access to create task dependency')

class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ['assignment_id','task','assignee']
        extra_kwargs = {
            'assignment_id': {'read_only': True}
            }

    def create(self, validated_data):
        user = self.context['request'].user
        task = Task.objects.get(task_id=validated_data['task'].task_id)
        if task.owner == user:
            assignment = Assignment(
                task=validated_data['task'],
                assignee=validated_data['assignee']
            )
            assignment.save()

            subtasks = Task.objects.filter(parentTask = task)

            def assign(subtasks):
                if subtasks:
                    for subtask in subtasks:
                        assignment = Assignment(
                            task=subtask,
                            assignee=validated_data['assignee']
                        )
                        assignment.save()
                        sts = Task.objects.filter(parentTask = subtask)
                        assign(sts)
                return
            assign(subtasks)
            
            return assignment

        raise Exception('Unauthorized access to task')

class ScheduleSerializer(serializers.ModelSerializer):
    tasks = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['project_id','title','start_date','end_date','duration','tasks']
        extra_kwargs = {
            'title': {'read_only': True},
            'start_date': {'read_only': True},
            }

    def get_tasks(self, obj):
        user = self.context['request'].user
        assigned_tasks = Assignment.objects.filter(assignee=user).values_list('task_id', flat=True)
        visible_tasks = Task.objects.filter(task_id__in=assigned_tasks,project=obj.project_id, completed=False).order_by('start_date')
        return AssignedTaskSerializer(visible_tasks,many=True,read_only=True,context=self.context).data

    def get_end_date(self, obj):
        return self.context['end_date']

    def get_duration(self, obj):
        return (self.context['end_date'] - obj.start_date).days
