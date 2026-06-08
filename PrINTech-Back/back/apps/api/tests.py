from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
User = get_user_model()
import json
from .models import Request, File, Operation, Filament, Printer

class RequestViewSetTests(APITestCase):
    def setUp(self):
        self.initial_balance = 100
        
        self.user = User.objects.create_user(username='Celian', password='password123', email='celian@intech.com', credit=self.initial_balance)
        self.user2 = User.objects.create_user(username='Yanis', password='password123', email='yanis@intech.com', credit=self.initial_balance)

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        self.filament = Filament.objects.create(
            color='#FF0000',
            color_name='Rouge',
            type='PLA',
            quantity=5
        )

        test_file = SimpleUploadedFile(
            name='test.stl',
            content=b'blabla',
            content_type='model/stl'
        )
        
        file = File.objects.create(
                    path=test_file,
                    number_of_printing=1,
                    filament=self.filament
                )
        
        self.req_usr1 = Request.objects.create(
            user=self.user, status='AWAITING_PAYMENT', price=10, comment="Robotech", file=file
        )
        self.req_usr2 = Request.objects.create(
            user=self.user2, status='SUBMITTED', comment="Autotech", file=file
        )
        
        self.list_url = reverse('request-list')
        self.pay_url = reverse('request-pay', args=[self.req_usr1.id])
        self.cancel_url = reverse('request-cancel', args=[self.req_usr1.id])

    def test_list_requests_authenticated(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['comment'], "Robotech")
        
    def test_no_access_other_user_request(self):
        url = reverse('request-detail', args=[self.req_usr2.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_change_status(self):
        data = {'status': 'PRINTING'}
        response = self.client.patch(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


    def test_create_request(self):
        
        test_file = SimpleUploadedFile(
            name='test.stl',
            content=b'blabla',
            content_type='model/stl'
        )

        data = {
            "comment": "test",
            "path": test_file,
            "number_of_printing": 1,
            "para_slicer": json.dumps({"layer_height": 0.2, "infill": "20%"}),
            "filament": self.filament.id
        }
        response = self.client.post(self.list_url, data, format='multipart')
        #response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Request.objects.count(), 3)

    def test_missing_token(self):
        self.client.credentials()  # Clear the header
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_pay_request_success(self):
        response = self.client.post(self.pay_url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.req_usr1.refresh_from_db()
        self.user.refresh_from_db()
        
        self.assertEqual(self.req_usr1.status, 'PENDING')
        expected_balance = self.initial_balance - self.req_usr1.price
        self.assertEqual(self.user.credit, expected_balance)        
        self.assertEqual(self.req_usr1.operation_set.filter(operation_type='PAYMENT').count(), 1)

    def test_cancel_request_with_refund(self):
        self.client.post(self.pay_url)
        response = self.client.post(self.cancel_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.credit, self.initial_balance)
        self.req_usr1.refresh_from_db()
        self.assertEqual(self.req_usr1.status, 'CANCELED')
        self.assertEqual(self.req_usr1.operation_set.count(), 2)

    def test_cancel_request_multiple_payments_conflict(self):
        self.req_usr1.status = 'PENDING'
        self.req_usr1.save()
        
        for _ in range(2):
            Operation.objects.create(
                beneficiary=self.user, agent=self.user, amount=-10,
                operation_type='PAYMENT', request=self.req_usr1
            )

        response = self.client.post(self.cancel_url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_pay_request_insufficient_funds(self):
        USER_BALANCE = -1 #always insufficient
        self.user.credit = USER_BALANCE
        self.user.save()
        
        response = self.client.post(self.pay_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.req_usr1.refresh_from_db()
        self.assertEqual(self.req_usr1.status, 'AWAITING_PAYMENT')
        self.user.refresh_from_db()
        self.assertEqual(self.user.credit, USER_BALANCE)

    def test_pay_request_requires_price(self):
        self.req_usr1.price = 0
        self.req_usr1.save()

        response = self.client.post(self.pay_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Request price is not set.')
        
    def test_cannot_pay_other_user_request(self):
        usr2_pay_url = reverse('request-pay', args=[self.req_usr2.id])
        response = self.client.post(usr2_pay_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Operation.objects.filter(request=self.req_usr2).count(), 0)

    def test_cannot_cancel_other_user_request(self):
        usr2_cancel_url = reverse('request-cancel', args=[self.req_usr2.id])
        response = self.client.post(usr2_cancel_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.req_usr2.refresh_from_db()
        self.assertEqual(self.req_usr2.status, 'SUBMITTED')
            
class AdminRequestViewTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='william', 
            password='password123', 
            email='william@intech.com',
            is_staff=True
        )
        
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        self.filament = Filament.objects.create(
            color='#FF0000',
            color_name='Rouge',
            type='PLA',
            quantity=5
        )
        test_file = SimpleUploadedFile(name='test.stl', content=b'data', content_type='model/stl')
        self.file_obj = File.objects.create(path=test_file, number_of_printing=1, filament=self.filament)
        
        self.print_req = Request.objects.create(
            user=self.admin, 
            status='SUBMITTED', 
            comment="Admin Test", 
            file=self.file_obj
        )
        
        self.change_status_url = reverse('admin-request-change-status', args=[self.print_req.id])

    def test_staff_change_status_manually(self):
        data = {'status': 'PRINTING'}
        response = self.client.patch(self.change_status_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'New requests must move to awaiting payment first.')
        self.print_req.refresh_from_db()
        self.assertEqual(self.print_req.status, 'SUBMITTED')

    def test_staff_change_status_auto(self):
        expected_status = Request.Status.AWAITING_PAYMENT

        response = self.client.patch(self.change_status_url, {'price': 25}) 
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.print_req.refresh_from_db()
        self.assertEqual(self.print_req.status, expected_status)
        self.assertEqual(self.print_req.price, 25)

    def test_staff_cannot_auto_skip_payment(self):
        self.print_req.status = Request.Status.AWAITING_PAYMENT
        self.print_req.save()

        response = self.client.patch(self.change_status_url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Request is waiting for user payment.')

    def test_staff_must_set_price_for_awaiting_payment(self):
        response = self.client.patch(self.change_status_url, {'status': 'AWAITING_PAYMENT'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'A price is required before setting awaiting payment.')

    def test_staff_change_status_auto_limit(self):
        statuses = Request.Status.values
        self.print_req.status = statuses[-2] 
        self.print_req.save()

        response = self.client.patch(self.change_status_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Already Completed.')

    def test_non_staff_access(self):
        user = User.objects.create_user(username='Ilo', password='password123')
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.patch(self.change_status_url, {'status': 'PRINTING'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        
class UserOperationTests(APITestCase):
    def setUp(self):
        self.initial_balance = 100
        self.user1 = User.objects.create_user(
            username='Celian', 
            password='password123', 
            email='celian@intech.com',
            credit=self.initial_balance
        )
        self.user2 = User.objects.create_user(
            username='Yanis', 
            password='password123', 
            email='yanis@intech.com',
            credit=self.initial_balance
        )

        self.admin = User.objects.create_user(
            username='William', 
            password='password123', 
            email='william@intech.com',
            is_staff=True
        )

        refresh = RefreshToken.for_user(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        Operation.objects.create(
            beneficiary=self.user1, 
            agent=self.admin, 
            amount=20, 
            operation_type='CASH'
        )

        
        self.url = reverse('operation-list')

    def test_user_list_own_operations_only(self):
        Operation.objects.create(
            beneficiary=self.user2, 
            agent=self.admin, 
            amount=50, 
            operation_type='CASH'
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['amount'], 20)

    def test_user_cannot_create_operation(self):
        data = {"beneficiary": self.user1, "amount": 100, "operation_type": "CASH"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AdminOperationTests(APITestCase):
    def setUp(self):
        self.initial_balance = 100
        self.admin = User.objects.create_user(
            username='Celian', 
            password='password123', 
            email='celian@intech.com',
            is_staff=True
        )
        self.beneficiary = User.objects.create_user(
            username='Ilo', 
            password='password123', 
            email='ilo@test.com',
            credit=self.initial_balance
        )        

        refresh = RefreshToken.for_user(self.admin)
        self.access_token = str(refresh.access_token)        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        self.url = reverse('admin-operation-list')

    def test_admin_deposit_cash(self):
        change = 50
        data = {
            "beneficiary": self.beneficiary.id,
            "amount": change,
            "operation_type": "CASH"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.beneficiary.refresh_from_db()
        self.assertEqual(self.beneficiary.credit, self.initial_balance + change)

    def test_admin_insufficient_funds(self):
        data = {
            "beneficiary": self.beneficiary.id,
            "amount": -150,
            "operation_type": "PAYMENT"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_list(self):
        Operation.objects.create(
            beneficiary=self.beneficiary, 
            agent=self.admin, 
            amount=10, 
            operation_type='CASH'
        )
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
        

class FilamentTests(APITestCase):
    def setUp(self):
        self.initial_balance=100
        self.user = User.objects.create_user(
            username='Celian', 
            password='password123', 
            email='celian@intech.com',
            credit=self.initial_balance
        )

        self.admin = User.objects.create_user(
            username='William', 
            password='password123', 
            email='william@intech.com',
            is_staff=True
        )

        # Create initial data
        self.filament = Filament.objects.create(
            color='#FF0000',
            color_name='Rouge',
            type='PLA',
            quantity=5
        )

        self.public_list_url = reverse('filament-list')
        self.admin_list_url = reverse('filament-admin-list')
        self.admin_detail_url = reverse('filament-admin-detail', args=[self.filament.id])


    def test_user_can_list_filaments(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.get(self.public_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['color_name'], 'Rouge')

    def test_user_cannot_create_filament(self):
        """ReadOnlyModelViewSet should block POST requests from regular users."""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        data = {"color": "#00FF00", "color_name": "Green", "type": "PETG", "quantity": 10}
        response = self.client.post(self.public_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_user_cannot_access_admin_endpoint(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.get(self.admin_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_admin_create_filament(self):
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        data = {
            "color": "#0000FF",
            "color_name": "Bleu",
            "type": "PLA",
            "quantity": 5
        }
        response = self.client.post(self.admin_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Filament.objects.count(), 2)

    def test_admin_can_update_quantity(self):
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        data = {"quantity": 67}
        response = self.client.patch(self.admin_detail_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.filament.refresh_from_db()
        self.assertEqual(self.filament.quantity, 67)

    def test_invalid_hex_code(self):
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        data = {
            "color": "NOT A HEX CODE",
            "color_name": "blabla",
            "type": "PLA",
            "quantity": 1
        }
        response = self.client.post(self.admin_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_delete_filament(self):
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.delete(self.admin_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Filament.objects.count(), 0)
        
class PrinterViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='Celian', password='password123', email='celian@intech.com')
        self.admin = User.objects.create_user(username='William', password='password123', email='william@intech.com', is_staff=True)
 
        for printer in Printer.Name.values:
            Printer.objects.get_or_create(name=printer)
 
        self.public_list_url = reverse('printer-list')
        self.admin_list_url = reverse('admin-printer-list')
        self.printer = Printer.objects.first()
        self.admin_detail_url = reverse('admin-printer-detail', args=[self.printer.name])
 
    def test_list_printers(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        response = self.client.get(self.public_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
 
    def test_readonly(self):
        data = {'status': 'UP'}
        response = self.client.patch(self.public_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
 
    def test_admin_update_printer_status(self):
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        data = {'status': 'UP'}
        response = self.client.patch(self.admin_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.printer.refresh_from_db()
        self.assertEqual(self.printer.status, 'UP')
 
    def test_admin_access(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        data = {'status': 'UP'}
        response = self.client.patch(self.admin_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
 
    def test_admin_cannot_create_printer(self):
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        data = {'name': 'CREALITY_K1C', 'status': 'UP'}
        response = self.client.post(self.admin_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
 
    def test_admin_cannot_delete_printer(self):
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        response = self.client.delete(self.admin_detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)