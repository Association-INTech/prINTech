import { computed, Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { jwtDecode } from 'jwt-decode';

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

  refreshToken(): Observable<RefreshResponse>{
    const refresh = localStorage.getItem(this.refreshTokenStorageKey);
    if (!refresh) throw new Error('no refresh token');
    return this.http
      .post<RefreshResponse>(`${this.apiBase}/token/refresh/`, { refresh })
      .pipe(tap(({ access }) => this.setTokens(access, refresh)));
  }

  change_password(
    old_password: string,
    new_password: string,
    confirm_password: string
  ): Observable<ChangePasswordResponse> {
    const change_password_payload: ChangePasswordRequest = {
      old_password,
      new_password,
      confirm_password,
    };

    return this.http.patch<ChangePasswordResponse>(
      `${this.apiBase}/user/me/change-password/`,
      change_password_payload
    );
  }
  logout(): void {
    this.clearToken();
  }

  getToken(): string | null {
    return this.token();
  }

  isLoggedIn(): boolean {
    const token = this.token();

    if (token == null) {
      console.warn('no token')
      return false;
    }

    const decodedToken = jwtDecode(token);

    if (!decodedToken.exp) {
      console.warn('invalid token')
      return false;
    }
    const currentTime = Date.now() / 1000;
    const isExpired = decodedToken.exp < currentTime;

    return (!isExpired);
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

interface RefreshResponse {
  access: string;
}
interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

interface ChangePasswordResponse {
  message: string;
}
