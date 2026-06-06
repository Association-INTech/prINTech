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

  private readonly userStorageKey = 'auth_current_user';
  // Current user cached as a signal so UI can reactively depend on it
  currentUser = signal<UserMeResponse | null>(
    (() => {
      const stored = localStorage.getItem(this.userStorageKey);
      return stored ? JSON.parse(stored) : null;
    })()
  );

  readonly isAuthenticated = computed(() => this.token() !== null);

  constructor() {
    const token = this.token();
    if (token) {
      try {
        const decoded: any = jwtDecode(token as string);
        const now = Date.now() / 1000;
        if (!decoded.exp || decoded.exp < now) {
          this.clearToken();
        } else {
          this.loadCurrentUser().subscribe({ next: () => {}, error: () => {} });
        }
      } catch (e) {
        this.clearToken();
      }
    }
  }

  login(email: string, password: string): Observable<LoginResponse> {
    const payload: LoginRequest = { email, password };

    return this.http
      .post<LoginResponse>(`${this.apiBase}/token/`, payload)
      .pipe(
        tap(({ access, refresh }) => {
          this.setTokens(access, refresh);
          // eagerly load current user
          this.loadCurrentUser().subscribe({ next: () => {}, error: () => {} });
        })
      );
  }

  getCurrentUser(): Observable<UserMeResponse> {
    return this.http.get<UserMeResponse>(`${this.apiBase}/user/me/`);
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
    this.currentUser.set(null);
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
    localStorage.removeItem(this.userStorageKey);
  }

  loadCurrentUser(): Observable<UserMeResponse> {
    const obs = this.http.get<UserMeResponse>(`${this.apiBase}/user/me/`);
    obs.subscribe({
      next: (u) => {
        this.currentUser.set(u);
        localStorage.setItem(this.userStorageKey, JSON.stringify(u));
      },
      error: () => this.currentUser.set(null)
    });
    return obs;
  }
}


interface LoginRequest {
  email: string;
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

interface UserMeResponse {
  id: string;
  username: string;
  email: string;
  credit: number;
  is_staff: boolean;
  profile_picture: string | null; 
}
