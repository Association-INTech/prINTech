import { CommonModule, DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  AdminService,
  AdminUser,
  AdminUserCreatePayload,
  AdminUserUpdatePayload,
  PrintRequestStatus,
  PrintRequest,
} from '../services/admin';

@Component({
  selector: 'app-admin-dashboard',
  imports: [CommonModule, ReactiveFormsModule, DatePipe],
  templateUrl: './admin-dashboard.html',
  styleUrl: './admin-dashboard.css',
})
export class AdminDashboard implements OnInit {
  private readonly adminService = inject(AdminService);
  private readonly formBuilder = inject(FormBuilder);

  readonly waitingPrints = signal<PrintRequest[]>([]);
  readonly sortedWaitingPrints = signal<PrintRequest[]>([]);
  readonly users = signal<AdminUser[]>([]);
  readonly loading = signal(false);
  readonly errorMessage = signal('');
  readonly successMessage = signal('');
  readonly statusOptions: PrintRequestStatus[] = [
    'SUBMITTED',
    'AWAITING_PAYMENT',
    'PENDING',
    'PRINTING',
    'AWAITING_PICKUP',
    'PICKED_UP',
    'FAILED',
    'CANCELED',
  ];
  readonly sortColumn = signal<'id' | 'file' | 'user' | 'created_at' | 'status'>('created_at');
  readonly sortDirection = signal<'asc' | 'desc'>('desc');
  readonly searchQuery = signal('');
  updatingRequestIds = new Set<string>();

  readonly createUserForm = this.formBuilder.nonNullable.group({
    username: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    is_staff: [false],
    is_active: [true],
  });

  readonly editUserForm = this.formBuilder.nonNullable.group({
    id: ['', [Validators.required]],
    username: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    password: [''],
    is_staff: [false],
    is_active: [true],
  });

  ngOnInit(): void {
    this.loadAll();
  }

  loadAll(): void {
    this.loading.set(true);
    this.errorMessage.set('');

    this.adminService.getWaitingRequests().subscribe({
      next: (requests) => {
        const waiting = requests.filter(
          (item) =>
            item.status === 'SUBMITTED' ||
            item.status === 'AWAITING_PAYMENT' ||
            item.status === 'PENDING' ||
            item.status === 'PRINTING' ||
            item.status === 'AWAITING_PICKUP'
        );
        this.waitingPrints.set(waiting);
        this.applyPrintSort();
      },
      error: () => this.errorMessage.set('Impossible de charger les impressions en attente.'),
    });

    this.adminService.getUsers().subscribe({
      next: (users) => {
        this.users.set(users);
        this.loading.set(false);
      },
      error: () => {
        this.errorMessage.set('Impossible de charger les comptes utilisateurs.');
        this.loading.set(false);
      },
    });
  }

  onCreateUser(): void {
    if (this.createUserForm.invalid) {
      this.createUserForm.markAllAsTouched();
      return;
    }

    const payload = this.createUserForm.getRawValue() as AdminUserCreatePayload;
    this.adminService.createUser(payload).subscribe({
      next: () => {
        this.successMessage.set('Compte créé avec succès.');
        this.createUserForm.reset({
          username: '',
          email: '',
          password: '',
          is_staff: false,
          is_active: true,
        });
        this.loadAll();
      },
      error: (err) => this.errorMessage.set(this.readError(err, 'Création du compte impossible.')),
    });
  }

  startEditUser(user: AdminUser): void {
    this.editUserForm.setValue({
      id: user.id,
      username: user.username,
      email: user.email,
      password: '',
      is_staff: user.is_staff,
      is_active: user.is_active,
    });
  }

  onUpdateUser(): void {
    if (this.editUserForm.invalid) {
      this.editUserForm.markAllAsTouched();
      return;
    }

    const formValue = this.editUserForm.getRawValue();
    const payload: AdminUserUpdatePayload = {
      username: formValue.username,
      email: formValue.email,
      is_staff: formValue.is_staff,
      is_active: formValue.is_active,
    };

    if (formValue.password) {
      payload.password = formValue.password;
    }

    this.adminService.updateUser(formValue.id, payload).subscribe({
      next: () => {
        this.successMessage.set('Compte mis à jour avec succès.');
        this.loadAll();
      },
      error: (err) => this.errorMessage.set(this.readError(err, 'Mise à jour du compte impossible.')),
    });
  }

  onDeleteUser(userId: string): void {
    this.adminService.deleteUser(userId).subscribe({
      next: () => {
        this.successMessage.set('Compte supprimé avec succès.');
        this.loadAll();
      },
      error: (err) => this.errorMessage.set(this.readError(err, 'Suppression du compte impossible.')),
    });
  }

  onHeaderSort(column: 'id' | 'file' | 'user' | 'created_at' | 'status'): void {
    if (this.sortColumn() === column) {
      this.sortDirection.set(this.sortDirection() === 'asc' ? 'desc' : 'asc');
    } else {
      this.sortColumn.set(column);
      this.sortDirection.set('asc');
    }
    this.applyPrintSort();
  }

  sortIndicator(column: 'id' | 'file' | 'user' | 'created_at' | 'status'): string {
    if (this.sortColumn() !== column) {
      return '';
    }
    return this.sortDirection() === 'asc' ? '↑' : '↓';
  }

  onSearchChange(event: Event): void {
    this.searchQuery.set((event.target as HTMLInputElement).value.trim().toLowerCase());
    this.applyPrintSort();
  }

  onStatusChange(item: PrintRequest, event: Event): void {
    const newStatus = (event.target as HTMLSelectElement).value as PrintRequestStatus;

    if (newStatus === item.status || !this.canTransition(item.status, newStatus)) {
      this.applyPrintSort();
      return;
    }

    if (this.updatingRequestIds.has(item.id)) {
      return;
    }

    this.updatingRequestIds.add(item.id);
    this.errorMessage.set('');

    this.adminService.changeRequestStatus(item.id, newStatus).subscribe({
      next: () => {
        this.successMessage.set('Statut de l\'impression mis à jour.');
        this.updatingRequestIds.delete(item.id);
        this.loadAll();
      },
      error: (err) => {
        this.errorMessage.set(this.readError(err, 'Impossible de changer le statut de l\'impression.'));
        this.updatingRequestIds.delete(item.id);
        this.applyPrintSort();
      },
    });
  }

  isUpdatingRequest(requestId: string): boolean {
    return this.updatingRequestIds.has(requestId);
  }

  canTransition(current: PrintRequestStatus, next: PrintRequestStatus): boolean {
    if (current === next) {
      return true;
    }

    const transitions: Record<PrintRequestStatus, PrintRequestStatus[]> = {
      SUBMITTED: ['AWAITING_PAYMENT', 'FAILED', 'CANCELED'],
      AWAITING_PAYMENT: ['PENDING', 'FAILED', 'CANCELED'],
      PENDING: ['PRINTING', 'FAILED', 'CANCELED'],
      PRINTING: ['AWAITING_PICKUP', 'FAILED'],
      AWAITING_PICKUP: ['PICKED_UP', 'FAILED'],
      PICKED_UP: [],
      FAILED: [],
      CANCELED: [],
    };

    return transitions[current].includes(next);
  }

  getFileName(path?: string | null): string {
    if (!path) return '-';
    return path.split('/').pop() || path;
  }

  getDownloadUrl(path?: string | null): string {
    if (!path) return '';
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    if (path.startsWith('/')) {
      return path;
    }
    return `/${path}`;
  }

  getStatusBadgeClass(status: PrintRequestStatus): string {
    if (status === 'SUBMITTED' || status === 'AWAITING_PAYMENT' || status === 'PENDING') {
      return 'status-queued';
    }
    if (status === 'PRINTING' || status === 'AWAITING_PICKUP') {
      return 'status-progress';
    }
    if (status === 'PICKED_UP') {
      return 'status-done';
    }
    return 'status-failed';
  }

  private applyPrintSort(): void {
    const query = this.searchQuery();
    const filtered = !query
      ? this.waitingPrints()
      : this.waitingPrints().filter((item) => {
          const id = item.id.toLowerCase();
          const file = this.getFileName(item.file?.path).toLowerCase();
          const user = item.user.toLowerCase();
          const status = item.status.toLowerCase();
          return id.includes(query) || file.includes(query) || user.includes(query) || status.includes(query);
        });

    const sorted = [...filtered];
    const column = this.sortColumn();
    const direction = this.sortDirection();

    sorted.sort((a, b) => {
      let result = 0;

      if (column === 'created_at') {
        result = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      } else if (column === 'status') {
        result = a.status.localeCompare(b.status);
      } else if (column === 'user') {
        result = a.user.localeCompare(b.user);
      } else if (column === 'file') {
        result = this.getFileName(a.file?.path).localeCompare(this.getFileName(b.file?.path));
      } else {
        result = a.id.localeCompare(b.id);
      }

      return direction === 'asc' ? result : -result;
    });

    this.sortedWaitingPrints.set(sorted);
  }

  private readError(error: any, fallback: string): string {
    const data = error?.error;
    if (typeof data === 'string') return data;
    if (data?.detail) return data.detail;
    if (data?.non_field_errors?.length) return data.non_field_errors[0];
    const firstKey = data && typeof data === 'object' ? Object.keys(data)[0] : null;
    if (firstKey && Array.isArray(data[firstKey]) && data[firstKey][0]) {
      return `${firstKey}: ${data[firstKey][0]}`;
    }
    return fallback;
  }
}
