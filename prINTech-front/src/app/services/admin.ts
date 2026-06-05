import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class AdminService {
  private readonly http = inject(HttpClient);
  private readonly apiBase = '/api/v1';

  getWaitingRequests(): Observable<PrintRequest[]> {
    return this.http
      .get<PrintRequest[] | PaginatedResponse<PrintRequest>>(`${this.apiBase}/admin/requests/`)
      .pipe(map((response) => Array.isArray(response) ? response : response.results));
  }

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

  changeRequestStatus(requestId: string, status: PrintRequestStatus): Observable<PrintRequest> {
    return this.http.patch<PrintRequest>(
      `${this.apiBase}/admin/requests/${requestId}/change_status/`,
      { status }
    );
  }
}

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
  comment: string | null;
  printer: string | null;
  file: {
    path: string;
    number_of_printing: number;
    filament: number | null;
    para_slicer: unknown;
  } | null;
}

export interface AdminUser {
  id: string;
  username: string;
  email: string;
  credit: number;
  is_staff: boolean;
  is_active: boolean;
}

export interface AdminUserCreatePayload {
  username: string;
  email: string;
  password: string;
  is_staff: boolean;
  is_active: boolean;
}

export interface AdminUserUpdatePayload {
  username?: string;
  email?: string;
  password?: string;
  is_staff?: boolean;
  is_active?: boolean;
}

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
