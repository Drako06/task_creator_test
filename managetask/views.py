from django.shortcuts import render, redirect
from .models import Task
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from .task_send_email import send_task_notification
from drf_spectacular.utils import extend_schema, OpenApiParameter

import json
# Create your views here.

def create_task(request):
    try:
        title = request.POST.get('title')
        email = request.POST.get('email')
        description = request.POST.get('description')

        task = Task(title=title, email=email, description=description)
        task.save()

        send_task_notification.delay(email, title, 'creada')

    except Exception as e:
        return HttpResponseServerError(f"Error al guardar la tarea: {str(e)}")

    return redirect('/api/task/')


def task_list(request):
    tasks = Task.objects.all().order_by('id')
    paginator = Paginator(tasks, 5)

    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    print("page obj_ ", page_obj)
    print(tasks)

    # Renderizar la plantilla con los datos paginados
    return render(request, 'tasks_manager.html', {
        'task_list': tasks,
        'page_obj': page_obj
    })


def delete_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        task.delete()
    except ObjectDoesNotExist:
        return HttpResponseServerError(f"Tarea con id: {task_id} no encontrada.")
    except Exception as e:
        return HttpResponseServerError(f"Error al borrar la tarea: {str(e)}")

    return redirect('/api/task/')


""" función para peticiones externas """
@extend_schema(
    methods=['GET'],
    parameters=[
        OpenApiParameter(name='id', description='ID de la tarea para obtener un solo registro', required=False, type=int)
    ],
    responses={
        200: {
            "id": "integer",
            "title": "string",
            "email": "string",
            "description": "string"
        },
        404: {"description": "Task not found"}
    },
    description="Obtener una o todas las tareas"
)
@extend_schema(
    methods=['POST'],
    request={
        "application/json": {
            "title": "string",
            "email": "string",
            "description": "string"
        }
    },
    responses={201: {"id": "integer", "message": "Task created successfully."}},
    description="Crear una nueva tarea"
)
@extend_schema(
    methods=['PUT'],
    parameters=[
        OpenApiParameter(name='id', description='ID de la tarea para actualizar', required=True, type=int)
    ],
    request={
        "application/json": {
            "title": "string",
            "email": "string",
            "description": "string"
        }
    },
    responses={200: {"message": "Task updated successfully."}},
    description="Actualizar una tarea existente"
)
@extend_schema(
    methods=['DELETE'],
    parameters=[
        OpenApiParameter(name='id', description='ID de la tarea para eliminar', required=True, type=int)
    ],
    responses={200: {"message": "Task deleted successfully."}},
    description="Eliminar una tarea"
)
@csrf_exempt
def task_view(request, id=None):
    if request.method == "GET":
        if id:
            # Obtener un solo registro
            task = get_object_or_404(Task, id=id)
            data = {
                "id": task.id,
                "title": task.title,
                "email": task.email,
                "description": task.description,
            }
        else:
            # Obtener todos los registros
            tasks = Task.objects.all()
            data = [
                {"id": task.id, "title": task.title, "email": task.email, "description": task.description}
                for task in tasks
            ]
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        # Crear un nuevo registro
        data = json.loads(request.body)
        task = Task.objects.create(
            title=data.get("title"),
            email=data.get("email"),
            description=data.get("description", "")
        )
        return JsonResponse({"id": task.id, "message": "Task created successfully."}, status=201)

    elif request.method == "PUT" and id:
        print("dentro del PUT")
        # Actualizar un registro existente
        task = get_object_or_404(Task, id=id)
        data = json.loads(request.body)
        task.title = data.get("title", task.title)
        task.email = data.get("email", task.email)
        task.description = data.get("description", task.description)
        task.save()

        send_task_notification.delay(task.email, task.title, 'actualizada')

        return JsonResponse({"message": "Task updated successfully."})

    elif request.method == "DELETE" and id:
        # Eliminar un registro existente
        task = get_object_or_404(Task, id=id)
        print("tenemros el task delete: ", task)
        task.delete()
        return JsonResponse({"message": "Task deleted successfully."})

    # Responder en caso de un método HTTP no permitido
    return JsonResponse({"error": "Method not allowed"}, status=405)
