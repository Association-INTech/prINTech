import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class AdminService {
  private readonly http = inject(HttpClient);
  private readonly apiBase = '/api/v1';

  // ── Requests ────────────────────────────────────────────────
  getWaitingRequests(): Observable<PrintRequest[]> {
    return this.http
      .get<PrintRequest[] | PaginatedResponse<PrintRequest>>(`${this.apiBase}/admin/requests/`)
      .pipe(map((response) => Array.isArray(response) ? response : response.results));
  }

  changeRequestStatus(requestId: string, status: PrintRequestStatus, price?: number): Observable<PrintRequest> {
    const body: Record<string, unknown> = { status };
    if (price !== undefined) body['price'] = price;
    return this.http.patch<PrintRequest>(
      `${this.apiBase}/admin/requests/${requestId}/change_status/`,
      body
    );
  }

  // ── Users ───────────────────────────────────────────────────
  getUsers(): Observable<AdminUser[]> {
    return this.http
      .get<AdminUser[] | PaginatedResponse<AdminUser>>(`${this.apiBase}/admin/users/`)
      .pipe(map((response) => Array.isArray(response) ? response : response.results));
  }

  createUser(payload: AdminUserCreatePayload): Observable<AdminUser> {
    return this.http.post<AdminUser>(`${this.apiBase}/admin/users/`, payload);
  }

  updateUser(userId: string, payload: AdminUserUpdatePayload): Observable<AdminUser> {
    return this.http.patch<AdminUser>(`${this.apiBase}/admin/users/${userId}/`, payload);
  }

  deleteUser(userId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiBase}/admin/users/${userId}/`);
  }

  // ── Operations ──────────────────────────────────────────────
  getOperations(): Observable<Operation[]> {
    return this.http
      .get<Operation[] | PaginatedResponse<Operation>>(`${this.apiBase}/admin/operations/`)
      .pipe(map((response) => Array.isArray(response) ? response : response.results));
  }

  createOperation(payload: OperationCreatePayload): Observable<Operation> {
    return this.http.post<Operation>(`${this.apiBase}/admin/operations/`, payload);
  }

  // ── Filaments ───────────────────────────────────────────────
  getFilaments(): Observable<Filament[]> {
    return this.http
      .get<Filament[] | PaginatedResponse<Filament>>(`${this.apiBase}/admin/filaments/`)
      .pipe(map((response) => Array.isArray(response) ? response : response.results));
  }

  createFilament(payload: FilamentPayload): Observable<Filament> {
    return this.http.post<Filament>(`${this.apiBase}/admin/filaments/`, payload);
  }

  updateFilament(id: number, payload: FilamentPayload): Observable<Filament> {
    return this.http.patch<Filament>(`${this.apiBase}/admin/filaments/${id}/`, payload);
  }

  deleteFilament(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiBase}/admin/filaments/${id}/`);
  }

  // ── Printers ────────────────────────────────────────────────
  getPrinters(): Observable<Printer[]> {
    return this.http
      .get<Printer[] | PaginatedResponse<Printer>>(`${this.apiBase}/admin/printers/`)
      .pipe(map((response) => Array.isArray(response) ? response : response.results));
  }

  updatePrinter(name: string, payload: PrinterUpdatePayload): Observable<Printer> {
    return this.http.patch<Printer>(`${this.apiBase}/admin/printers/${name}/`, payload);
  }
}

// ── Shared ─────────────────────────────────────────────────────
interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ── Request types ───────────────────────────────────────────────
export type PrintRequestStatus =
  | 'SUBMITTED'
  | 'AWAITING_PAYMENT'
  | 'PENDING'
  | 'PRINTING'
  | 'AWAITING_PICKUP'
  | 'PICKED_UP'
  | 'FAILED'
  | 'CANCELED';

export interface PrintRequest {
  id: string;
  user: string;
  status: PrintRequestStatus;
  created_at: string;
  price: number;
  comment: string | null;
  printer: string | null;
  file: {
    path: string;
    number_of_printing: number;
    filament: number | null;
    para_slicer: unknown;
  } | null;
}

// ── User types ──────────────────────────────────────────────────
export interface AdminUser {
  id: string;
  username: string;
  email: string;
  credit: number;
  priority: string;
  is_staff: boolean;
  is_active: boolean;
  role: string;

}

export interface AdminUserCreatePayload {
  username: string;
  email: string;
  password: string;
  is_staff: boolean;
  is_active: boolean;
  role?: string;
}

export interface AdminUserUpdatePayload {
  username?: string;
  email?: string;
  password?: string;
  priority?: string;
  is_staff?: boolean;
  is_active?: boolean;
  role?: string;
}

// ── Operation types ─────────────────────────────────────────────
export type OperationType = 'CASH' | 'CARD' | 'PAYMENT' | 'REFUND';

export interface Operation {
  id: string;
  beneficiary: string;
  agent: string;
  amount: number;
  operation_type: OperationType;
  comment: string | null;
  created_at: string;
  request: string | null;
}

export interface OperationCreatePayload {
  beneficiary: string;
  amount: number;
  operation_type: OperationType;
  request?: string;
  comment?: string;
}

// ── Filament types ──────────────────────────────────────────────
export interface Filament {
  id: number;
  color: string;
  color_name: string;
  type: 'PLA' | 'PETG';
  quantity: number;
  price: number;
}

export type FilamentPayload = Omit<Filament, 'id'>;

// ── Printer types ───────────────────────────────────────────────
export type PrinterStatus = 'UP' | 'DOWN' | 'USED';

export interface Printer {
  name: string;
  status: PrinterStatus;
}

export interface PrinterUpdatePayload {
  status: PrinterStatus;
}
