import { CommonModule, DatePipe, SlicePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  AdminService,
  AdminUser,
  AdminUserCreatePayload,
  AdminUserUpdatePayload,
  PrintRequestStatus,
  PrintRequest,
  Filament,
  FilamentPayload,
  Printer,
  PrinterStatus,
  Operation,
  OperationCreatePayload,
} from '../services/admin';

type TabId = 'requests' | 'users' | 'operations' | 'filaments' | 'printers';

@Component({
  selector: 'app-admin-dashboard',
  imports: [CommonModule, ReactiveFormsModule, DatePipe, SlicePipe],
  templateUrl: './admin-dashboard.html',
  styleUrl: './admin-dashboard.css',
})
export class AdminDashboard implements OnInit {
  private readonly adminService = inject(AdminService);
  private readonly formBuilder = inject(FormBuilder);

  // Tab 
  readonly activeTab = signal<TabId>('requests');

  setTab(tab: TabId): void {
    this.activeTab.set(tab);
    this.errorMessage.set('');
    this.successMessage.set('');
  }

  // Global state 
  readonly loading = signal(false);
  readonly errorMessage = signal('');
  readonly successMessage = signal('');

  // Requests
  readonly waitingPrints = signal<PrintRequest[]>([]);
  readonly sortedWaitingPrints = signal<PrintRequest[]>([]);
  readonly sortColumn = signal<'id' | 'file' | 'user' | 'created_at' | 'status' | 'printer' | 'comment'>('created_at');  readonly sortDirection = signal<'asc' | 'desc'>('desc');
  readonly searchQuery = signal('');
  updatingRequestIds = new Set<string>();
  readonly pendingStatus = signal<Record<string, PrintRequestStatus>>({});
  pendingPrice: Record<string, number | undefined> = {};

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

  // Users
  readonly users = signal<AdminUser[]>([]);
  readonly editingUserId = signal<string | null>(null);

  readonly roleOptions = ['ADHERENT', 'ROBOTECH', 'AUTOTECH', 'DRONE', 'BUREAU'];

  readonly createUserForm = this.formBuilder.nonNullable.group({
    username: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    is_staff: [false],
    is_active: [true],
  });

  readonly editUserForm = this.formBuilder.nonNullable.group({
    id: ['', [Validators.required]],
    username: [''],
    email: ['', [Validators.required, Validators.email]],
    password: [''],
    role: ['ADHERENT'],
    is_staff: [false],
    is_active: [true],
  });

  // Operations 
  readonly operations = signal<Operation[]>([]);

  readonly operationTypes = ['CASH', 'CARD', 'PAYMENT', 'REFUND'];

  readonly createOperationForm = this.formBuilder.nonNullable.group({
    beneficiary: ['', [Validators.required]],
    amount: [0, [Validators.required]],
    operation_type: ['CASH', [Validators.required]],
    request: [''],
    comment: [''],
  });

  // Filaments 
  readonly filaments = signal<Filament[]>([]);
  readonly editingFilamentId = signal<number | null>(null);

  readonly filamentForm = this.formBuilder.nonNullable.group({
    color: ['#ffffff', [Validators.required]],
    color_name: ['', [Validators.required]],
    type: ['PLA', [Validators.required]],
    quantity: [0, [Validators.required, Validators.min(0)]],
    price: [0, [Validators.required, Validators.min(0)]],
  });

  // Printers 
  readonly printers = signal<Printer[]>([]);
  updatingPrinterNames = new Set<string>();

  readonly printerStatuses: PrinterStatus[] = ['UP', 'DOWN', 'USED'];

  // Lifecycle 
  ngOnInit(): void {
    this.loadAll();
  }

  loadAll(): void {
    this.loadRequests();
    this.loadUsers();
    this.loadOperations();
    this.loadFilaments();
    this.loadPrinters();
  }

  // Requests 
  private loadRequests(): void {
    this.adminService.getWaitingRequests().subscribe({
      next: (requests) => {
        const rawList = Array.isArray(requests) ? requests : ((requests as any)?.results || []);
        this.pendingStatus.set({});
        this.waitingPrints.set(rawList);
        this.applyPrintSort();
      },
      error: () => this.errorMessage.set('Impossible de charger les impressions.'),
    });
  }

  onHeaderSort(column: 'id' | 'file' | 'user' | 'created_at' | 'status' | 'printer' | 'comment'): void {
    if (this.sortColumn() === column) {
      this.sortDirection.set(this.sortDirection() === 'asc' ? 'desc' : 'asc');
    } else {
      this.sortColumn.set(column);
      this.sortDirection.set('asc');
    }
    this.applyPrintSort();
  }

  sortIndicator(column: 'id' | 'file' | 'user' | 'created_at' | 'status' | 'printer' | 'comment'): string {
    if (this.sortColumn() !== column) return '';
    return this.sortDirection() === 'asc' ? '↑' : '↓';
  }

  onSearchChange(event: Event): void {
    this.searchQuery.set((event.target as HTMLInputElement).value.trim().toLowerCase());
    this.applyPrintSort();
  }

  onPriceInput(requestId: string, event: Event): void {
    const val = parseInt((event.target as HTMLInputElement).value, 10);
    if (!isNaN(val)) {
      this.pendingPrice[requestId] = val;
    }
  }

  getPendingStatus(requestId: string, currentStatus: PrintRequestStatus): PrintRequestStatus {
    return this.pendingStatus()[requestId] ?? currentStatus;
  }

  hasPendingStatusChange(requestId: string, currentStatus: PrintRequestStatus): boolean {
    const pending = this.pendingStatus()[requestId];
    return !!pending && pending !== currentStatus;
  }

  onSelectStatus(requestId: string, event: Event): void {
    const selected = (event.target as HTMLSelectElement).value as PrintRequestStatus;
    this.pendingStatus.update(map => ({ ...map, [requestId]: selected }));
  }

  onApplyStatus(item: PrintRequest): void {
    if (this.updatingRequestIds.has(item.id)) return;

    const currentStatus = item.status;
    const targetStatus = this.pendingStatus()[item.id] ?? currentStatus;
    const isStatusChange = targetStatus !== currentStatus;

    // 1. Validation de la transition si le statut change
    if (isStatusChange && !this.canTransition(currentStatus, targetStatus)) {
      return;
    }

    // 2. Gestion et récupération du prix
    const inputPrice = this.pendingPrice[item.id];
    const isPriceModified = inputPrice !== undefined && inputPrice !== null && Number(inputPrice) !== Number(item.price);

    // Rien n'a changé : on ne fait rien
    if (!isStatusChange && !isPriceModified) return;

    // On détermine le statut final concerné
    const effectiveStatus = isStatusChange ? targetStatus : currentStatus;
    const needsPrice = effectiveStatus === 'AWAITING_PAYMENT';

    // Si l'impression doit être ou rester en AWAITING_PAYMENT, on vérifie la présence du prix
    const priceToSubmit = isPriceModified ? Number(inputPrice) : item.price;

    if (needsPrice && (priceToSubmit === undefined || priceToSubmit === null || priceToSubmit < 0)) {
      this.errorMessage.set('Un prix valide est requis pour le statut AWAITING_PAYMENT.');
      return;
    }

    this.updatingRequestIds.add(item.id);
    this.errorMessage.set('');

    // 3. Appel unique à l'API avec le statut (nouveau ou actuel) et le prix mis à jour
    this.adminService.changeRequestStatus(item.id, targetStatus, priceToSubmit).subscribe({
      next: () => {
        this.successMessage.set('Demande mise à jour avec succès.');
        this.pendingStatus.update(map => {
          const m = { ...map };
          delete m[item.id];
          return m;
        });
        delete this.pendingPrice[item.id];
        this.updatingRequestIds.delete(item.id);
        this.loadRequests();
      },
      error: (err) => {
        this.errorMessage.set(this.readError(err, 'Impossible de mettre à jour la demande.'));
        this.updatingRequestIds.delete(item.id);
        this.applyPrintSort();
      },
    });
  }

  isUpdatingRequest(requestId: string): boolean {
    return this.updatingRequestIds.has(requestId);
  }

  canTransition(current: PrintRequestStatus, next: PrintRequestStatus): boolean {
    if (current === next) return false;
    // Statuts finaux : aucune transition possible
  
    if (['PICKED_UP', 'FAILED', 'CANCELED'].includes(current)) {
    return false;
    }

    // CANCELED et FAILED sont toujours autorisés avant la finalisation
    if (next === 'CANCELED' || next === 'FAILED') {
    return true;
    }

    const transitions: Record<PrintRequestStatus, PrintRequestStatus[]> = {
      SUBMITTED: ['AWAITING_PAYMENT'],
      AWAITING_PAYMENT: ['PENDING'],
      PENDING: ['PRINTING'],
      PRINTING: ['AWAITING_PICKUP'],
      AWAITING_PICKUP: ['PICKED_UP'],
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
    if (path.startsWith('http://') || path.startsWith('https://')) return path;
    return path.startsWith('/') ? path : `/${path}`;
  }

  getStatusBadgeClass(status: PrintRequestStatus): string {
    if (['SUBMITTED', 'AWAITING_PAYMENT', 'PENDING'].includes(status)) return 'badge-queued';
    if (['PRINTING', 'AWAITING_PICKUP'].includes(status)) return 'badge-progress';
    if (status === 'PICKED_UP') return 'badge-done';
    return 'badge-failed';
  }

  // Filter status 
  readonly statusFilter = signal<string>('BASIC');
  setStatusFilter(status: string): void {
    this.statusFilter.set(status);
    this.applyPrintSort();
  }

  private applyPrintSort(): void {
    const query = this.searchQuery();
    const currentFilter = this.statusFilter();

    // 1. Filtrage par statut
    let filtered = this.waitingPrints();
    if (currentFilter === 'BASIC') {
      filtered = filtered.filter((item) => {
        const st = item.status;
        return st == 'SUBMITTED' || st == 'PENDING' || st == 'PRINTING';
      });
    } else {
      // Filtre strict si un statut spécifique est cliqué
      filtered = filtered.filter((item) => item.status === currentFilter);
    }

    // 2. Filtrage par recherche
    if (query) {
      filtered = filtered.filter((item) => {
        const id = (item.id || '').toLowerCase();
        const file = this.getFileName(item.file?.path).toLowerCase();
        const user = this.getUserEmail(item.user).toLowerCase();
        const st = (item.status || '').toLowerCase();
        const printer = this.getPrinterName((item as any).printer).toLowerCase();
        const comment = ((item as any).comment || '').toLowerCase();

        return (
          id.includes(query) ||
          file.includes(query) ||
          user.includes(query) ||
          st.includes(query) ||
          printer.includes(query) ||
          comment.includes(query)
        );
      });
    }

    // 3. Tri sur TOUTES les colonnes
    const sorted = [...filtered];
    const column = this.sortColumn();
    const direction = this.sortDirection();

    sorted.sort((a, b) => {
      let result = 0;

      switch (column) {
        case 'created_at':
          result = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'status':
          result = (a.status || '').localeCompare(b.status || '');
          break;
        case 'user':
          result = this.getUserEmail(a.user).localeCompare(this.getUserEmail(b.user));
          break;
        case 'file':
          result = this.getFileName(a.file?.path).localeCompare(this.getFileName(b.file?.path));
          break;
        case 'printer':
          result = this.getPrinterName((a as any).printer).localeCompare(this.getPrinterName((b as any).printer));
          break;
        case 'comment':
          result = ((a as any).comment || '').localeCompare((b as any).comment || '');
          break;
        case 'id':
        default:
          result = (a.id || '').localeCompare(b.id || '');
          break;
      }

      return direction === 'asc' ? result : -result;
    });

    this.sortedWaitingPrints.set(sorted);
  }

  // Users
  private loadUsers(): void {
    this.adminService.getUsers().subscribe({
      next: (users) => this.users.set(users),
      error: () => this.errorMessage.set('Impossible de charger les comptes utilisateurs.'),
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
        this.createUserForm.reset({ username: '', email: '', password: '', is_staff: false, is_active: true });
        this.loadUsers();
      },
      error: (err) => this.errorMessage.set(this.readError(err, 'Création du compte impossible.')),
    });
  }

  startEditUser(user: AdminUser): void {
    this.editingUserId.set(user.id);
    this.editUserForm.setValue({
      id: user.id,
      username: user.username,
      email: user.email,
      password: '',
      role: (user as any).role ?? 'ADHERENT',
      is_staff: user.is_staff,
      is_active: user.is_active,
    });
    this.setTab('users');
  }

  cancelEditUser(): void {
    this.editingUserId.set(null);
    this.editUserForm.reset({ id: '', username: '', email: '', password: '', role: 'ADHERENT', is_staff: false, is_active: true });
  }

  onUpdateUser(): void {
    if (this.editUserForm.invalid) {
      this.editUserForm.markAllAsTouched();
      return;
    }
    const formValue = this.editUserForm.getRawValue();
    const payload: AdminUserUpdatePayload = {
      email: formValue.email,
      role: formValue.role,
      is_staff: formValue.is_staff,
      is_active: formValue.is_active,
    };
    if (formValue.username) payload.username = formValue.username;
    if (formValue.password) payload.password = formValue.password;

    this.adminService.updateUser(formValue.id, payload).subscribe({
      next: () => {
        this.successMessage.set('Compte mis à jour avec succès.');
        this.cancelEditUser();
        this.loadUsers();
      },
      error: (err) => this.errorMessage.set(this.readError(err, 'Mise à jour du compte impossible.')),
    });
  }

  onDeleteUser(userId: string): void {
    if (!confirm('Supprimer cet utilisateur ?')) return;
    this.adminService.deleteUser(userId).subscribe({
      next: () => {
        this.successMessage.set('Compte supprimé avec succès.');
        this.loadUsers();
      },
      error: (err) => this.errorMessage.set(this.readError(err, 'Suppression du compte impossible.')),
    });
  }

  // Operations
  private loadOperations(): void {
    this.adminService.getOperations().subscribe({
      next: (ops) => this.operations.set(ops),
      error: () => this.errorMessage.set('Impossible de charger les opérations.'),
    });
  }

  onCreateOperation(): void {
    if (this.createOperationForm.invalid) {
      this.createOperationForm.markAllAsTouched();
      return;
    }
    const formValue = this.createOperationForm.getRawValue();
    const payload: OperationCreatePayload = {
      beneficiary: formValue.beneficiary,
      amount: formValue.amount,
      operation_type: formValue.operation_type as any,
      ...(formValue.request ? { request: formValue.request } : {}),
      ...(formValue.comment ? { comment: formValue.comment } : {}),
    };
    this.adminService.createOperation(payload).subscribe({
      next: () => {
        this.successMessage.set('Opération créée avec succès.');
        this.createOperationForm.reset({ beneficiary: '', amount: 0, operation_type: 'CASH', request: '', comment: '' });
        this.loadOperations();
        this.loadUsers(); // refresh credits
      },
      error: (err) => this.errorMessage.set(this.readError(err, 'Création de l\'opération impossible.')),
    });
  }

  // Filaments
  private loadFilaments(): void {
    this.adminService.getFilaments().subscribe({
      next: (filaments) => this.filaments.set(filaments),
      error: () => this.errorMessage.set('Impossible de charger les filaments.'),
    });
  }

  startEditFilament(f: Filament): void {
    this.editingFilamentId.set(f.id);
    this.filamentForm.setValue({
      color: f.color,
      color_name: f.color_name,
      type: f.type,
      quantity: f.quantity,
      price: f.price,
    });
    this.setTab('filaments');
  }

  cancelEditFilament(): void {
    this.editingFilamentId.set(null);
    this.filamentForm.reset({ color: '#ffffff', color_name: '', type: 'PLA', quantity: 0, price: 0 });
  }

  onSubmitFilament(): void {
    if (this.filamentForm.invalid) {
      this.filamentForm.markAllAsTouched();
      return;
    }
    const payload = this.filamentForm.getRawValue() as FilamentPayload;
    const id = this.editingFilamentId();

    const obs = id
      ? this.adminService.updateFilament(id, payload)
      : this.adminService.createFilament(payload);

    obs.subscribe({
      next: () => {
        this.successMessage.set(id ? 'Filament mis à jour.' : 'Filament ajouté.');
        this.cancelEditFilament();
        this.loadFilaments();
      },
      error: (err) => this.errorMessage.set(this.readError(err, 'Impossible de sauvegarder le filament.')),
    });
  }

  onDeleteFilament(id: number): void {
    if (!confirm('Supprimer ce filament ?')) return;
    this.adminService.deleteFilament(id).subscribe({
      next: () => {
        this.successMessage.set('Filament supprimé.');
        this.loadFilaments();
      },
      error: (err) => this.errorMessage.set(this.readError(err, 'Suppression du filament impossible.')),
    });
  }

  // Printers
  private loadPrinters(): void {
    this.adminService.getPrinters().subscribe({
      next: (printers) => this.printers.set(printers),
      error: () => this.errorMessage.set('Impossible de charger les imprimantes.'),
    });
  }

  onPrinterStatusChange(printer: Printer, event: Event): void {
    const newStatus = (event.target as HTMLSelectElement).value as PrinterStatus;
    if (newStatus === printer.status) return;
    if (this.updatingPrinterNames.has(printer.name)) return;

    this.updatingPrinterNames.add(printer.name);
    this.errorMessage.set('');

    this.adminService.updatePrinter(printer.name, { status: newStatus }).subscribe({
      next: () => {
        this.successMessage.set(`Statut de ${printer.name} mis à jour.`);
        this.updatingPrinterNames.delete(printer.name);
        this.loadPrinters();
      },
      error: (err) => {
        this.errorMessage.set(this.readError(err, 'Impossible de mettre à jour l\'imprimante.'));
        this.updatingPrinterNames.delete(printer.name);
        this.loadPrinters();
      },
    });
  }

  isUpdatingPrinter(name: string): boolean {
    return this.updatingPrinterNames.has(name);
  }

  getPrinterBadgeClass(status: PrinterStatus): string {
    if (status === 'UP') return 'badge-up';
    if (status === 'USED') return 'badge-used';
    return 'badge-down';
  }

  getPrinterName(printer: string | Printer | null | undefined): string {
  if (!printer) return '-';
  // Recherche par nom dans le signal printers
  const found = this.printers().find(p => String(p.name) === printer);
  return found ? found.name : String(printer);
  }

  getUserEmail(userId: string): string {
    return this.users().find((u) => u.id === userId)?.email ?? userId.slice(0, 8) + '…';
  }

  getUserRole(userId: string): string {
  const user = this.users().find((u) => u.id === userId);
  return user && 'role' in user ? (user as any).role : '—';
}
  // Utilities 
  private readError(error: any, fallback: string): string {
    const data = error?.error;
    if (typeof data === 'string') return data;
    if (data?.detail) return data.detail;
    if (data?.non_field_errors?.length) return data.non_field_errors[0];
    if (data?.error) return data.error;
    const firstKey = data && typeof data === 'object' ? Object.keys(data)[0] : null;
    if (firstKey && Array.isArray(data[firstKey]) && data[firstKey][0]) {
      return `${firstKey}: ${data[firstKey][0]}`;
    }
    return fallback;
  }

  //si le prix change 
  isPriceModified(item: any): boolean {
  const inputPrice = this.pendingPrice[item.id];
  if (inputPrice === undefined || inputPrice === null) {
    return false;
  }
  return Number(inputPrice) !== Number(item.price);
}

}