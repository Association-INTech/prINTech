import { computed, Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly tokenStorageKey = 'auth_token';
  private readonly apiBase = '/api';
  private readonly token = signal<string | null>(
    localStorage.getItem(this.tokenStorageKey)
  );

  readonly isAuthenticated = computed(() => this.token() !== null);

  login(email: string, password: string): Observable<LoginResponse> {
    const payload: LoginRequest = { email, password };

    return this.http
      .post<LoginResponse>(`${this.apiBase}/auth/login`, payload)
      .pipe(tap(({ token }) => this.setToken(token)));
  }

  logout(): void {
    this.clearToken();
  }

  getToken(): string | null {
    return this.token();
  }

  private setToken(token: string): void {
    this.token.set(token);
    localStorage.setItem(this.tokenStorageKey, token);
  }

  private clearToken(): void {
    this.token.set(null);
    localStorage.removeItem(this.tokenStorageKey);
  }
}

interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  token: string;
}
