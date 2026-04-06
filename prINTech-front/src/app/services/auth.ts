import { computed, Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  
  private readonly http = inject(HttpClient);
  private readonly accessTokenStorageKey = 'auth_access_token';
  private readonly refreshTokenStorageKey = 'auth_refresh_token';
  private readonly apiBase = '/api/v1';
  private readonly token = signal<string | null>(
    localStorage.getItem(this.accessTokenStorageKey)
  );

  readonly isAuthenticated = computed(() => this.token() !== null);

  login(username: string, password: string): Observable<LoginResponse> {
    const payload: LoginRequest = { username, password };

    return this.http
      .post<LoginResponse>(`${this.apiBase}/token/`, payload)
      .pipe(tap(({ access, refresh }) => this.setTokens(access, refresh)));
  }

  logout(): void {
    this.clearToken();
  }

  getToken(): string | null {
    return this.token();
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    this.token.set(accessToken);
    localStorage.setItem(this.accessTokenStorageKey, accessToken);
    localStorage.setItem(this.refreshTokenStorageKey, refreshToken);
  }

  private clearToken(): void {
    this.token.set(null);
    localStorage.removeItem(this.accessTokenStorageKey);
    localStorage.removeItem(this.refreshTokenStorageKey);
  }
}

interface LoginRequest {
  username: string;
  password: string;
}

interface LoginResponse {
  access: string;
  refresh: string;
}
