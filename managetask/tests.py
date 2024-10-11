from django.test import TestCase, Client
from unittest.mock import patch
from django.urls import reverse
from .models import Task
import json


class CreateTaskViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('managetask.task_send_email.send_task_notification.delay')
    def test_create_task_success(self,  mock_send_task_notification_delay):
        """ Prueba que se crea una tarea correctamente y se redirige a /task/ """
        response = self.client.post(reverse('task_create'), {
            'title': 'Nueva Tarea',
            'email': 'usuario@test.com',
            'description': 'Descripción de la tarea'
        })

        # Verificar que la tarea fue creada en la base de datos
        self.assertEqual(Task.objects.count(), 1)
        task = Task.objects.first()
        self.assertEqual(task.title, 'Nueva Tarea')
        self.assertEqual(task.email, 'usuario@test.com')
        self.assertEqual(task.description, 'Descripción de la tarea')

        mock_send_task_notification_delay.assert_called_once_with('usuario@test.com', 'Nueva Tarea', 'creada')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/api/task/')

    def test_create_task_save_error(self):
        """Prueba que se devuelve un error 500 si falla el guardado de la tarea."""
        print("El module_ ", self.__module__)
        # Mock para simular un fallo en el guardado del objeto Task
        with patch(f'{self.__module__}.Task.save', side_effect=Exception("Error de prueba al guardar")):
            response = self.client.post(reverse('task_create'), {
                'title': 'Nueva Tarea',
                'email': 'usuario@test.com',
                'description': 'Descripción de la tarea'
            })

        # Verifica que la respuesta sea un error 500
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Error al guardar la tarea: Error de prueba al guardar", response.content)


class TaskListViewTest(TestCase):
    def setUp(self):
        for i in range(6):
            Task.objects.create(
                title=f"Tarea {i + 1}",
                email=f"tarea{i + 1}@test.com",
                description=f"Descripción de la tarea {i + 1}"
            )
        self.client = Client()

    def test_task_list_view_initial_page(self):
        """Prueba que se carga la primera página de resultados"""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks_manager.html')
        # Verificar que hay exactamente 5 tareas en la primera página
        self.assertEqual(len(response.context['page_obj']), 5)
        # Verificar que el primer elemento en la página es "Tarea 1"
        self.assertEqual(response.context['page_obj'][0].title, "Tarea 1")

    def test_task_list_view_middle_page(self):
        """Prueba que se carga correctamente una página intermedia"""
        response = self.client.get(reverse('task_list') + '?page=2')
        self.assertEqual(response.status_code, 200)
        # Verificar que hay 5 tareas en la segunda página
        self.assertEqual(len(response.context['page_obj']), 1)
        # Verificar que el primer elemento en la página es "Tarea 6"
        self.assertEqual(response.context['page_obj'][0].title, "Tarea 6")

    def test_task_list_invalid_page(self):
        """Prueba que se carga la primera página al solicitar una página inválida"""
        response = self.client.get(reverse('task_list') + '?page=invalid')
        self.assertEqual(response.status_code, 200)
        # Verificar que la primera página se carga con 5 tareas
        self.assertEqual(len(response.context['page_obj']), 5)
        self.assertEqual(response.context['page_obj'][0].title, "Tarea 1")


class DeleteTaskTest(TestCase):
    def setUp(self):
        """ Crear una tarea de ejemplo para pruebas """
        self.task = Task.objects.create(title="Test Task delete", email="test@test.com", description="Test Description")

    def test_delete_task_success(self):
        """ Prueba: eliminar la tarea existente """
        response = self.client.post(reverse('task_delete', args=[self.task.id]))

        """ Comprobar redirección a la lista de tareas y que la tarea ya no existe """
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/api/task/')

        with self.assertRaises(Task.DoesNotExist):
            Task.objects.get(id=self.task.id)

    def test_delete_task_not_found(self):
        """  Prueba: intentar eliminar una tarea que no existe """
        response = self.client.post(reverse('task_delete', args=[9999]))
        print("delete id no exist: ", response)
        self.assertEqual(response.status_code, 500)
        self.assertIn("Tarea con id: 9999 no encontrada", response.content.decode())

    def test_delete_task_unexpected_error(self):
        """ Prueba: simular un error inesperado """
        with self.assertRaises(Exception):
            with self.settings(DEBUG=True):
                response = self.client.post(reverse('task_delete', args=[self.task.id]))

            self.assertEqual(response.status_code, 500)
            self.assertIn("Error al borrar la tarea", response.content.decode())


class TaskViewTests(TestCase):

    def setUp(self):
        self.task = Task.objects.create(
            title="Test Task",
            email="test@example.com",
            description="This is a test task."
        )

    def test_get_all_tasks(self):
        """Prueba el método GET sin ID para obtener todos los registros"""
        response = self.client.get(reverse('task_view'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), Task.objects.count())

    def test_get_single_task(self):
        """Prueba el método GET con ID para obtener un solo registro"""
        response = self.client.get(reverse('task_detail', args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsInstance(data, dict)
        self.assertEqual(data["id"], self.task.id)
        self.assertEqual(data["title"], self.task.title)
        self.assertEqual(data["email"], self.task.email)
        self.assertEqual(data["description"], self.task.description)

    def test_post_create_task(self):
        """Prueba el método POST para crear un nuevo registro"""
        data = {
            "title": "New Task",
            "email": "new@example.com",
            "description": "New task description"
        }
        response = self.client.post(
            reverse('task_view'),
            data=json.dumps(data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertIn("id", response_data)
        self.assertEqual(response_data["message"], "Task created successfully.")
        self.assertTrue(Task.objects.filter(title="New Task").exists())

    @patch('managetask.views.send_task_notification.delay')
    def test_put_update_task(self, mock_send_task_notification_delay):
        """Prueba el método PUT para actualizar un registro existente"""
        data = {
            "title": "Updated Task",
            "email": "updated@example.com",
            "description": "Updated description"
        }
        response = self.client.put(
            reverse('task_detail', args=[self.task.id]),
            data=json.dumps(data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["message"], "Task updated successfully.")

        # Verificar que la tarea fue actualizada en la base de datos
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Updated Task")
        self.assertEqual(self.task.email, "updated@example.com")
        self.assertEqual(self.task.description, "Updated description")

        # Verificar que send_task_notification.delay fue llamado correctamente
        mock_send_task_notification_delay.assert_called_once_with(self.task.email, self.task.title, 'actualizada')

    def test_delete_task(self):
        print("quinto test")
        """Prueba el método DELETE para eliminar un registro existente"""
        response = self.client.delete(reverse('task_detail', args=[self.task.id]))
        print("task delete: ", response)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["message"], "Task deleted successfully.")
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    def test_method_not_allowed(self):
        """Prueba una solicitud con un método HTTP no permitido"""
        response = self.client.patch(reverse('task_view'))
        self.assertEqual(response.status_code, 405)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["error"], "Method not allowed")