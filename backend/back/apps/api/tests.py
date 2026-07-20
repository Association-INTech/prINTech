from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from PIL import Image
import io

User = get_user_model()
import json
from .models import Request, File, Operation, Filament, Printer

class UserMeTests(APITestCase):
    
    def setUp(self):
        self.initial_balance = 100
        self.user = User.objects.create_user(
            username='scammerrr', 
            password='password123', 
            email='scammer67@intech.com',
            credit=self.initial_balance
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        self.me_url = reverse('user_info')

    def test_user_cannot_update_credit_manually(self):
        response = self.client.patch(self.me_url, {'credit': 9999})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.credit, self.initial_balance)  

    def test_delete_profile_picture_when_none_exists(self):
        self.user.profile_picture = None
        self.user.save()

        response = self.client.delete(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Aucune photo de profil à supprimer.")


class UserChangePasswordDetailedTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='Billy', password='VeryySecure2!', email='mod@intech.com')
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        self.password_url = reverse('change-password') 

    def test_change_password_mismatched_confirmation(self):
        data = {
            "old_password": "VeryySecure2!",
            "new_password": "Passworddd7676767!",
            "confirm_password": "DifferentPassworddd7676767!"
        }
        response = self.client.put(self.password_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_change_password_wrong_old_password(self):
        data = {
            "old_password": "WrongPassword1!",
            "new_password": "BrandNewPassword67!",
            "confirm_password": "BrandNewPassword67!"
        }
        response = self.client.put(self.password_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("old_password", response.data)

class AdminUserViewSetTests(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username='WilliamPrez', 
            password='Adminn123!', 
            email='william@intech.com',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='subordinate', 
            password='UserPassword123!', 
            email='zzz@intech.com',
            credit=10
        )
        
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        self.list_url = reverse('admin-user-list') 
        self.detail_url = reverse('admin-user-detail', args=[self.regular_user.id])

    def test_admin_can_list_all_users_sorted_by_email(self):
        """Admin should get a list of all users, ordered by email address."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['email'], self.admin.email) # car w > z

    def test_admin_can_manually_adjust_user_credit(self):
        """Admin uses AdminUserSerializer which allows direct credit modification."""
        data = {"credit": 500}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.credit, 500)

    def test_admin_can_deactivate_user(self):
        """Admin can change account status flags like is_active."""
        data = {"is_active": False}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)

    def test_admin_can_create_user_with_explicit_password(self):
        """Admin can explicitly create a new valid user profile."""
        data = {
            "username": "created_by_admin",
            "email": "created@intech.com",
            "password": "ValidPassword123!",
            "credit": 6767
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        new_user = User.objects.get(email="created@intech.com")
        self.assertTrue(new_user.check_password("ValidPassword123!"))

    def test_regular_user_cannot_access_admin_user_endpoints(self):
        """Non-staff users must be rejected immediately."""
        refresh = RefreshToken.for_user(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class UserProfilePictureTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='CelianTest', password='password123', email='celiantest@intech.com')
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        self.me_url = reverse('user_info') 
        
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0) # Avoid blank file read
        self.test_image = SimpleUploadedFile(
            name='pp.jpg',
            content=img_bytes.read(),
            content_type='image/jpeg'
        )
        
    def test_upload_profile_picture(self):
        response = self.client.patch(self.me_url, {'profile_picture': self.test_image}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_picture)

    def test_modify_profile_picture(self):
        self.client.patch(self.me_url, {'profile_picture': self.test_image}, format='multipart')
        self.user.refresh_from_db()
        old_name = self.user.profile_picture.name

        new_img = Image.new('RGB', (100, 100), color='blue')
        new_img_bytes = io.BytesIO()
        new_img.save(new_img_bytes, format='JPEG')
        new_image_file = SimpleUploadedFile(name='new_avatar.jpg', content=new_img_bytes.getvalue(), content_type='image/jpeg')

        response = self.client.patch(self.me_url, {'profile_picture': new_image_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        
        self.assertNotEqual(self.user.profile_picture.name, old_name)

    def test_delete_profile_picture(self):
        self.client.patch(self.me_url, {'profile_picture': self.test_image}, format='multipart')
        
        response = self.client.delete(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile_picture)
        self.assertTrue(User.objects.filter(id=self.user.id).exists())

    def test_unauthenticated_cannot_upload(self):
        self.client.credentials()
        response = self.client.patch(self.me_url, {'profile_picture': self.test_image}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class UserRoleAndPriorityTests(APITestCase):

    def setUp(self):
        # Create an Admin to access admin endpoints
        self.admin = User.objects.create_user(
            username='admin_boss', 
            password='Password123!', 
            email='admin@intech.com', 
            is_staff=True
        )
        
        # Create users with different roles
        self.user_bureau = User.objects.create_user(
            username='bureau_member', password='Password123!', email='bureau@intech.com', role='BUREAU'
        )
        self.user_robotech = User.objects.create_user(
            username='robotech_member', password='Password123!', email='robotech@intech.com', role='ROBOTECH'
        )
        self.user_adherent = User.objects.create_user(
            username='adherent_member', password='Password123!', email='adherent@intech.com', role='ADHERENT'
        )
        
        # Create a shared dummy filament and file setup for requests
        self.filament = Filament.objects.create(
            color='#FFFFFF', color_name='Blanc', type='PLA', quantity=10
        )
        test_file = SimpleUploadedFile(name='role_test.stl', content=b'data', content_type='model/stl')
        self.file_obj = File.objects.create(path=test_file, number_of_printing=1, filament=self.filament)

        # Authenticate the client as admin for priority testing
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        self.admin_request_list_url = reverse('admin-request-list')

    def test_admin_request_list_priority_sorting(self):
        """
        Verify that the admin viewset orders requests primarily by priority rank:
        BUREAU (0) > ROBOTECH/AUTOTECH/DRONE (1) > ADHERENT (2)
        """
        # Create requests in mixed/scrambled order of roles
        req_adherent = Request.objects.create(user=self.user_adherent, status='SUBMITTED', comment="Adherent Req", file=self.file_obj)
        req_bureau = Request.objects.create(user=self.user_bureau, status='SUBMITTED', comment="Bureau Req", file=self.file_obj)
        req_robotech = Request.objects.create(user=self.user_robotech, status='SUBMITTED', comment="Robotech Req", file=self.file_obj)

        response = self.client.get(self.admin_request_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Extract the comments in order from the response payload
        returned_comments = [item['comment'] for item in response.data]
        
        # Assert specific priority rank hierarchy sorting
        expected_order = ["Bureau Req", "Robotech Req", "Adherent Req"]
        self.assertEqual(returned_comments, expected_order)

    def test_default_role_is_adherent(self):
        """Ensure a newly registered user defaults safely to the ADHERENT role."""
        new_user = User.objects.create_user(
            username='fresh_user', 
            password='Password123!', 
            email='fresh@intech.com'
        )
        self.assertEqual(new_user.role, User.Role.ADHERENT)


class UserRoleTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='cel', 
            password='Password123!', 
            email='cel@intech.com',
            role='ADHERENT'
        )
        self.admin = User.objects.create_user(
            username='sek', 
            password='Password123!', 
            email='sek@intech.com', 
            is_staff=True
        )
        
        self.me_url = reverse('user_info')
        self.admin_user_detail_url = reverse('admin-user-detail', args=[self.user.id])

    def test_regular_user_cannot_change_own_role(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.patch(self.me_url, {'role': 'BUREAU'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'ADHERENT')

    def test_admin_can_modify_user_role(self):
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.patch(self.admin_user_detail_url, {'role': 'ROBOTECH'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'ROBOTECH')

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