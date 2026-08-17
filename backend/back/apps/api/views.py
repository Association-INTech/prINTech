from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.db.models.deletion import ProtectedError
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiTypes
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import User, Operation, Request, File, Filament, Printer, AdminActionLog
from django.db.models import Case, When, IntegerField, Value
from rest_framework import permissions, viewsets, mixins, generics, status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle, UserRateThrottle
from .serializers import UserSerializer, ChangePasswordSerializer, OperationSerializer, RequestSerializer,FilamentSerializer, PrinterSerializer
from .serializers import AdminUserSerializer
from django.db import transaction


REFRESH_TOKEN_COOKIE_NAME = 'refresh_token'
REFRESH_TOKEN_COOKIE_PATH = '/api/v1/token/'


def set_refresh_cookie(response, refresh_token):
    max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
    response.set_cookie(
        REFRESH_TOKEN_COOKIE_NAME,
        str(refresh_token),
        max_age=max_age,
        path=REFRESH_TOKEN_COOKIE_PATH,
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
    )


def delete_refresh_cookie(response):
    response.delete_cookie(
        REFRESH_TOKEN_COOKIE_NAME,
        path=REFRESH_TOKEN_COOKIE_PATH,
        samesite='Lax',
    )


def blacklist_refresh_token(refresh_token):
    if not refresh_token:
        return
    try:
        RefreshToken(refresh_token).blacklist()
    except (AttributeError, TokenError):
        pass


def serialize_audit_value(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def model_snapshot(obj, fields):
    return {field: serialize_audit_value(getattr(obj, field)) for field in fields}


def log_admin_action(request, action, target, *, before=None, after=None, comment=None):
    actor = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    AdminActionLog.objects.create(
        actor=actor,
        action=action,
        target_type=target._meta.label,
        target_id=str(target.pk),
        before=before,
        after=after,
        comment=comment,
    )


class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class HasScopedStaffPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if not user.is_staff:
            return False
        required_permissions = view.get_required_permissions()
        if required_permissions is None:
            return False
        return bool(required_permissions) and user.has_perms(required_permissions)


class CookieTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh = response.data.pop('refresh', None)
        if refresh:
            set_refresh_cookie(response, refresh)
        return response


class CookieTokenRefreshView(TokenRefreshView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'token-refresh'

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data.setdefault('refresh', request.COOKIES.get(REFRESH_TOKEN_COOKIE_NAME))

        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(exc.args[0])

        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        refresh = response.data.pop('refresh', None)
        if refresh:
            set_refresh_cookie(response, refresh)
        return response


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=None, responses={204: OpenApiResponse(description='Logged out')})
    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get(REFRESH_TOKEN_COOKIE_NAME) or request.data.get('refresh')
        blacklist_refresh_token(refresh)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        delete_refresh_cookie(response)
        return response

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'signup'
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        if not settings.ALLOW_PUBLIC_SIGNUP:
            return Response({"Message": "Public signup is disabled."}, status=status.HTTP_403_FORBIDDEN)
        if request.user.is_authenticated:
            return Response({"Message": "Vous ne devez pas être authentifié."},status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        access_token = AccessToken.for_user(user)

        response = Response(
            {
                "user": serializer.data,
                "access": str(access_token),
            },
            status=status.HTTP_201_CREATED,
        )
        set_refresh_cookie(response, refresh)
        return response


class UserMeView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    throttle_classes = [UserRateThrottle]

    def get_object(self):
        return self.request.user

    def destroy(self, request, *args, **kwargs):
        """Deletes ONLY profile picture, not the user account."""
        user = self.get_object()
        if user.profile_picture:
            user.profile_picture.delete(save=False) 
            user.profile_picture = None
            user.save()
            return Response({"message": "Photo de profil supprimée avec succès."}, status=status.HTTP_200_OK)
        return Response({"error": "Aucune photo de profil à supprimer."}, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    throttle_classes = [UserRateThrottle]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(
            {"message": "Mot de passe changé avec succès."}, status=status.HTTP_200_OK
        )

class OperationView(mixins.ListModelMixin, 
                           mixins.RetrieveModelMixin, 
                           viewsets.GenericViewSet):
    serializer_class = OperationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Operation.objects.none()
        return Operation.objects.filter(beneficiary=self.request.user)

class AdminOperationView(mixins.CreateModelMixin, 
                            mixins.ListModelMixin, 
                            mixins.RetrieveModelMixin, 
                            viewsets.GenericViewSet):
    serializer_class = OperationSerializer
    permission_classes = [HasScopedStaffPermission]
    queryset = Operation.objects.all()
    permission_map = {
        'create': ['api.add_operation'],
        'list': ['api.view_operation'],
        'retrieve': ['api.view_operation'],
    }

    def get_required_permissions(self):
        return self.permission_map.get(self.action)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['manual_admin_operation'] = True
        return context

    def perform_create(self, serializer):
        operation = serializer.save(agent=self.request.user)
        log_admin_action(
            self.request,
            'operation.create',
            operation,
            after=model_snapshot(operation, ['beneficiary_id', 'agent_id', 'amount', 'operation_type', 'request_id']),
        )
                
class RequestView(mixins.CreateModelMixin, 
                       mixins.ListModelMixin, 
                       mixins.RetrieveModelMixin, 
                       viewsets.GenericViewSet):
    serializer_class = RequestSerializer
    permission_classes=[IsAuthenticated]
    unit_print_price = 1

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Request.objects.none()
        return Request.objects.filter(user=self.request.user)

    def get_locked_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        queryset = self.filter_queryset(self.get_queryset()).select_for_update()
        obj = get_object_or_404(queryset, **{self.lookup_field: lookup_value})
        self.check_object_permissions(self.request, obj)
        return obj
    
    def get_request_price(self, number_of_printing, filament):
        unit_price = filament.price if filament and filament.price > 0 else self.unit_print_price
        return unit_price * number_of_printing

    def reserve_filament(self, filament, number_of_printing):
        if filament is None:
            raise serializers.ValidationError({'filament': 'Filament is required.'})
        locked_filament = Filament.objects.select_for_update().get(pk=filament.pk)
        if locked_filament.price <= 0:
            raise serializers.ValidationError({'filament': 'Selected filament has no valid price.'})
        if locked_filament.quantity < number_of_printing:
            raise serializers.ValidationError({'filament': 'Not enough filament stock.'})
        locked_filament.quantity -= number_of_printing
        locked_filament.save(update_fields=['quantity'])
        return locked_filament

    def debit_user(self, user, amount):
        locked_user = User.objects.select_for_update().get(pk=user.pk)
        if locked_user.credit < amount:
            raise serializers.ValidationError({"credit": "Insufficient funds"})
        locked_user.credit -= amount
        locked_user.save(update_fields=['credit'])
        return locked_user

    def create_payment_operation(self, print_request, user, amount):
        return Operation.objects.create(
            beneficiary=user,
            agent=user,
            amount=-amount,
            operation_type=Operation.Type.PAYMENT,
            request=print_request,
            comment=f"Payment for request {print_request.id}",
        )

    def cleanup_request_file(self, print_request):
        if print_request and print_request.file_id and print_request.file and print_request.file.path:
            print_request.file.path.delete(save=False)

    def perform_create(self, serializer):
        number_of_printing = serializer.validated_data['number_of_printing']
        print_request = None
        try:
            with transaction.atomic():
                locked_filament = self.reserve_filament(serializer.validated_data['filament'], number_of_printing)
                price = self.get_request_price(number_of_printing, locked_filament)
                locked_user = self.debit_user(self.request.user, price)
                print_request = serializer.save(
                    user=locked_user,
                    status=Request.Status.SUBMITTED,
                    price=price,
                    filament=locked_filament,
                )
                self.create_payment_operation(print_request, locked_user, price)
        except Exception:
            self.cleanup_request_file(print_request)
            raise

    def _charge_request(self, print_request, user):
        locked_user = self.debit_user(user, print_request.price)
        self.create_payment_operation(print_request, locked_user, print_request.price)

    @transaction.atomic
    @action(detail=True, methods=['post'])
    def relaunch(self, request, pk=None):
        previous_request = self.get_locked_object()

        if previous_request.file is None:
            return Response(
                {"error": "Cannot relaunch a request without file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        number_of_printing = previous_request.file.number_of_printing
        locked_filament = self.reserve_filament(previous_request.file.filament, number_of_printing)
        relaunched_request = Request.objects.create(
            user=request.user,
            file=previous_request.file,
            printer=None,
            price=self.get_request_price(number_of_printing, locked_filament),
            comment=previous_request.comment,
            status=Request.Status.SUBMITTED,
        )
        self._charge_request(relaunched_request, request.user)

        serializer = self.get_serializer(relaunched_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @transaction.atomic
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        print_request = self.get_locked_object()

        if print_request.status != 'AWAITING_PAYMENT':
            return Response(
                {"error": "Request not awaiting payment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        price = print_request.price
        if price <= 0:
            return Response(
                {"error": "Request price is not set."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = {
                "beneficiary": request.user.id,
                "amount": -price,
                "operation_type": "PAYMENT",
                "request": print_request.id
            }
        
        serializer = OperationSerializer(data=data)
        if serializer.is_valid():
            serializer.save(agent=request.user)
            print_request.status = 'PENDING'
            print_request.save(update_fields=['status'])
            return Response(status=201)
        return Response(serializer.errors, status=400)
    
    @transaction.atomic
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        print_request = self.get_locked_object()
        
        allowed_cancel = ['SUBMITTED','AWAITING_PAYMENT', 'PENDING']
        
        if print_request.status not in allowed_cancel:
            return Response(
                {"error": f"Cannot cancel for status: {print_request.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        payments = print_request.operation_set.filter(operation_type=Operation.Type.PAYMENT)
        refunds = print_request.operation_set.filter(operation_type=Operation.Type.REFUND)

        if payments.count() > 1:
            return Response(
                {"error": "Cannot refund ambiguous payments."},
                status=status.HTTP_409_CONFLICT
            )

        if payments.count() == 1 and refunds.count() == 0:
            payment = payments.first()
            refund_amount = abs(payment.amount)
            serializer = OperationSerializer(data={
                "beneficiary": print_request.user.id,
                "amount": refund_amount,
                "operation_type": Operation.Type.REFUND,
                "request": print_request.id,
                "comment": f"Refund for cancellation of request {print_request.id}",
            })
            serializer.is_valid(raise_exception=True)
            serializer.save(agent=request.user)
        elif refunds.count() > 0:
            return Response(
                {"error": "Request already refunded."},
                status=status.HTTP_409_CONFLICT
            )

        print_request.status = 'CANCELED'
        print_request.save(update_fields=['status'])
        
        return Response({"status": "Request canceled successfully"}, status=status.HTTP_200_OK)
    
class AdminRequestView(viewsets.ReadOnlyModelViewSet):
    serializer_class = RequestSerializer
    permission_classes=[HasScopedStaffPermission]
    permission_map = {
        'list': ['api.view_request'],
        'retrieve': ['api.view_request'],
        'change_status': ['api.change_request'],
        'refund': ['api.change_request', 'api.add_operation'],
    }

    def get_required_permissions(self):
        return self.permission_map.get(self.action)

    def get_locked_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        queryset = self.filter_queryset(self.get_queryset()).select_for_update()
        obj = get_object_or_404(queryset, **{self.lookup_field: lookup_value})
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        # BUREAU highest (0), project types equal (1), ADHERENT lowest (2)
        qs = Request.objects.all().annotate(
            priority_rank=Case(
                When(user__role='BUREAU', then=Value(0)),
                When(user__role='ROBOTECH', then=Value(1)),
                When(user__role='AUTOTECH', then=Value(1)),
                When(user__role='DRONE', then=Value(1)),
                When(user__role='ADHERENT', then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        ).order_by('priority_rank', '-created_at')
        return qs
    
    @transaction.atomic
    @action(detail=True, methods=['patch'])
    def change_status(self, request, pk):
        print_request = self.get_locked_object()
        new_status = request.data.get('status')
        current_status = str(print_request.status)

        if not new_status:
            auto_next_status = {
                Request.Status.SUBMITTED: Request.Status.PENDING,
                Request.Status.PENDING: Request.Status.PRINTING,
                Request.Status.PRINTING: Request.Status.AWAITING_PICKUP,
                Request.Status.AWAITING_PICKUP: Request.Status.PICKED_UP,
            }
            new_status = auto_next_status.get(current_status)
            if not new_status:
                return Response(
                    {'error': 'Already Completed.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if new_status not in Request.Status.values:
            return Response(
                {'error': f'Invalid status: {new_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        allowed_transitions = {
            Request.Status.SUBMITTED: [Request.Status.PENDING, Request.Status.FAILED, Request.Status.CANCELED],
            Request.Status.PENDING: [Request.Status.PRINTING, Request.Status.FAILED, Request.Status.CANCELED],
            Request.Status.PRINTING: [Request.Status.AWAITING_PICKUP, Request.Status.FAILED],
            Request.Status.AWAITING_PICKUP: [Request.Status.PICKED_UP, Request.Status.FAILED],
            Request.Status.PICKED_UP: [],
            Request.Status.FAILED: [],
            Request.Status.REFUNDED: [],
            Request.Status.CANCELED: [],
            Request.Status.AWAITING_PAYMENT: [Request.Status.PENDING, Request.Status.FAILED, Request.Status.CANCELED],
        }

        if new_status != current_status and new_status not in allowed_transitions.get(current_status, []):
            return Response(
                {'error': f'Invalid transition from {current_status} to {new_status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        before = {'status': current_status}
        print_request.status = new_status
        print_request.save(update_fields=['status'])
        log_admin_action(
            request,
            'request.change_status',
            print_request,
            before=before,
            after={'status': new_status},
        )

        serializer = self.get_serializer(print_request)
        return Response(serializer.data)

    @transaction.atomic
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        print_request = self.get_locked_object()

        if print_request.status != Request.Status.FAILED:
            return Response(
                {'error': 'Only failed requests awaiting refund can be refunded.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment_total = -sum(
            operation.amount
            for operation in print_request.operation_set.filter(operation_type=Operation.Type.PAYMENT)
        )
        refund_total = sum(
            operation.amount
            for operation in print_request.operation_set.filter(operation_type=Operation.Type.REFUND)
        )
        refund_amount = payment_total - refund_total

        if payment_total <= 0:
            return Response(
                {'error': 'No payment found for this request.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if refund_amount <= 0:
            return Response(
                {'error': 'Request already refunded.'},
                status=status.HTTP_409_CONFLICT
            )

        serializer = OperationSerializer(data={
            'beneficiary': print_request.user.id,
            'amount': refund_amount,
            'operation_type': Operation.Type.REFUND,
            'request': print_request.id,
            'comment': f'Refund for failed request {print_request.id}',
        })
        serializer.is_valid(raise_exception=True)
        refund_operation = serializer.save(agent=request.user)

        before = {'status': print_request.status}
        print_request.status = Request.Status.REFUNDED
        print_request.save(update_fields=['status'])
        log_admin_action(
            request,
            'request.refund',
            print_request,
            before=before,
            after={'status': print_request.status, 'refund_operation': str(refund_operation.id)},
        )

        return Response(self.get_serializer(print_request).data, status=status.HTTP_200_OK)


class FileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: OpenApiTypes.BINARY, 404: OpenApiResponse(description='Not found')})
    def get(self, request, pk, *args, **kwargs):
        file_obj = get_object_or_404(File, pk=pk)
        owns_file = Request.objects.filter(
            file=file_obj,
            user=request.user,
        ).exists()
        is_request_file = Request.objects.filter(file=file_obj).exists()
        can_download_request_file = is_request_file and (
            request.user.is_superuser
            or (request.user.is_staff and request.user.has_perm('api.view_request'))
        )
        can_download = owns_file or can_download_request_file
        if not can_download:
            raise Http404
        if not file_obj.path:
            raise Http404

        return FileResponse(
            file_obj.path.open('rb'),
            as_attachment=True,
            filename=Path(file_obj.path.name).name,
        )


class AdminUserView(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('email')
    serializer_class = AdminUserSerializer
    permission_classes = [IsSuperUser]

    def perform_create(self, serializer):
        user = serializer.save()
        log_admin_action(
            self.request,
            'user.create',
            user,
            after=model_snapshot(user, ['email', 'username', 'role', 'is_staff', 'is_active']),
        )

    def perform_update(self, serializer):
        before = model_snapshot(serializer.instance, ['email', 'username', 'role', 'is_staff', 'is_active'])
        user = serializer.save()
        log_admin_action(
            self.request,
            'user.update',
            user,
            before=before,
            after=model_snapshot(user, ['email', 'username', 'role', 'is_staff', 'is_active']),
        )

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        before = model_snapshot(user, ['email', 'username', 'role', 'is_staff', 'is_active'])
        user.is_active = False
        user.save(update_fields=['is_active'])
        log_admin_action(
            request,
            'user.deactivate',
            user,
            before=before,
            after=model_snapshot(user, ['email', 'username', 'role', 'is_staff', 'is_active']),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
class FilamentView(viewsets.ReadOnlyModelViewSet):
    queryset = Filament.objects.all()
    serializer_class = FilamentSerializer
    permission_classes = [permissions.AllowAny]

class AdminFilamentView(viewsets.ModelViewSet):
    queryset = Filament.objects.all()
    serializer_class = FilamentSerializer
    permission_classes = [HasScopedStaffPermission]

    def get_required_permissions(self):
        permission_map = {
            'create': ['api.add_filament'],
            'list': ['api.view_filament'],
            'retrieve': ['api.view_filament'],
            'update': ['api.change_filament'],
            'partial_update': ['api.change_filament'],
            'destroy': ['api.delete_filament'],
        }
        return permission_map.get(self.action)

    def perform_create(self, serializer):
        filament = serializer.save()
        log_admin_action(
            self.request,
            'filament.create',
            filament,
            after=model_snapshot(filament, ['color', 'color_name', 'type', 'quantity', 'price']),
        )

    def perform_update(self, serializer):
        before = model_snapshot(serializer.instance, ['color', 'color_name', 'type', 'quantity', 'price'])
        filament = serializer.save()
        log_admin_action(
            self.request,
            'filament.update',
            filament,
            before=before,
            after=model_snapshot(filament, ['color', 'color_name', 'type', 'quantity', 'price']),
        )

    def destroy(self, request, *args, **kwargs):
        filament = self.get_object()
        before = model_snapshot(filament, ['color', 'color_name', 'type', 'quantity', 'price'])
        try:
            response = super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'error': 'Cannot delete a filament used by existing files.'},
                status=status.HTTP_409_CONFLICT,
            )
        log_admin_action(request, 'filament.delete', filament, before=before)
        return response
    
class PrinterView(viewsets.ReadOnlyModelViewSet):
    queryset = Printer.objects.all()
    serializer_class = PrinterSerializer
    permission_classes = [permissions.AllowAny]
 
class AdminPrinterView(mixins.UpdateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    queryset = Printer.objects.all()
    serializer_class = PrinterSerializer
    permission_classes = [HasScopedStaffPermission]

    def get_required_permissions(self):
        permission_map = {
            'list': ['api.view_printer'],
            'retrieve': ['api.view_printer'],
            'update': ['api.change_printer'],
            'partial_update': ['api.change_printer'],
        }
        return permission_map.get(self.action)

    def perform_update(self, serializer):
        before = model_snapshot(serializer.instance, ['name', 'status'])
        printer = serializer.save()
        log_admin_action(
            self.request,
            'printer.update',
            printer,
            before=before,
            after=model_snapshot(printer, ['name', 'status']),
        )
