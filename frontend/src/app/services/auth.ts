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
  private readonly apiBase = 'http://127.0.0.1:8000/api/v1';
  private readonly token = signal<string | null>(
    localStorage.getItem(this.accessTokenStorageKey)
  );


  private readonly userStorageKey = 'auth_current_user';
  // Current user cached as a signal so UI can reactively depend on it
  currentUser = signal<UserMeResponse | null>(null);

  readonly isAuthenticated = computed(() => this.token() !== null);

  constructor() {
    this.clearPersistentAuthCache();
    const token = this.token();
    if (token) {
      try {
        const decoded: any = jwtDecode(token as string);
        const now = Date.now() / 1000;
        if (!decoded.exp || decoded.exp < now) {
          this.clearToken();
        } else {
          this.loadCurrentUser().subscribe({
            error: (err) => {
              if (err.status === 401 || err.status === 403) 
                {this.logout();} 
            }});
        }
      } catch (e) {
        this.clearToken();
      }
    }
  }

  login(email: string, password: string): Observable<LoginResponse> {
    const payload: LoginRequest = { email, password };

    return this.http
      .post<LoginResponse>(`${this.apiBase}/token/`, payload, { withCredentials: true })
      .pipe(
        tap(({ access }) => {
          this.setAccessToken(access);
          // eagerly load current user
          this.loadCurrentUser().subscribe({ next: () => {}, error: () => {} });
        })
      );
  }

  getCurrentUser(): Observable<UserMeResponse> {
    return this.http.get<UserMeResponse>(`${this.apiBase}/user/me/`);
  }

  refreshToken(): Observable<RefreshResponse>{
    return this.http
      .post<RefreshResponse>(`${this.apiBase}/token/refresh/`, {}, { withCredentials: true })
      .pipe(tap(({ access }) => this.setAccessToken(access)));
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
    this.http.post(`${this.apiBase}/token/logout/`, {}, { withCredentials: true }).subscribe({
      next: () => {},
      error: () => {},
    });
    this.clearToken();
    this.currentUser.set(null);
  }

  getToken(): string | null {
    return this.token();
  }

  isLoggedIn(): boolean {
    const token = this.token();

    if (token == null) {
      return false;
    }

    const decodedToken = jwtDecode(token);

    if (!decodedToken.exp) {
      return false;
    }
    const currentTime = Date.now() / 1000;
    const isExpired = decodedToken.exp < currentTime;

    return (!isExpired);
  }

  private setAccessToken(accessToken: string): void {
    this.token.set(accessToken);
  }

  private clearToken(): void {
    this.token.set(null);
  }

  private clearPersistentAuthCache(): void {
    localStorage.removeItem(this.accessTokenStorageKey);
    localStorage.removeItem(this.userStorageKey);
    sessionStorage.removeItem(this.accessTokenStorageKey);
    sessionStorage.removeItem(this.userStorageKey);
  }

  loadCurrentUser(): Observable<UserMeResponse> {
    const obs = this.http.get<UserMeResponse>(`${this.apiBase}/user/me/`);
    obs.subscribe({
      next: (u) => {
        this.currentUser.set(u);
      },
      error: (err) => {
        // On ne déconnecte QUE si le token est invalide (401/403)
        if (err.status === 401 || err.status === 403) {
          this.logout();
        }
    }});

    return obs;
  }
}


interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  access: string;
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
