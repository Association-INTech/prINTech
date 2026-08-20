import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, UrlTree } from '@angular/router';
import { firstValueFrom, of, throwError } from 'rxjs';
import { AuthService } from '../../services/auth';
import { authGuard } from './auth.guard';

describe('authGuard', () => {
  let isLoggedIn = false;
  let refreshSucceeds = false;

  beforeEach(() => {
    isLoggedIn = false;
    refreshSucceeds = false;

    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        {
          provide: AuthService,
          useValue: {
            isLoggedIn: () => isLoggedIn,
            refreshToken: () => refreshSucceeds ? of({ access: 'new-token' }) : throwError(() => new Error('expired')),
            loadCurrentUser: () => of({ id: '1', username: 'test', email: 'test@example.com', credit: 0, is_staff: false, profile_picture: null }),
          },
        },
      ],
    });
  });

  it('returns true when user is logged in', () => {
    isLoggedIn = true;

    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as never, {} as never)
    );

    expect(result).toBe(true);
  });

  it('returns true after refreshing an expired access token', async () => {
    isLoggedIn = false;
    refreshSucceeds = true;

    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as never, {} as never)
    );

    expect(result).toBeTruthy();
    const value = await firstValueFrom(result as any);
    expect(value).toBe(true);
  });

  it('redirects to /login when user is not logged in and refresh fails', async () => {
    isLoggedIn = false;
    refreshSucceeds = false;
    const router = TestBed.inject(Router);

    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as never, {} as never)
    );

    expect(result).toBeTruthy();
    const value = await firstValueFrom(result as any);
    expect(value instanceof UrlTree).toBe(true);
    expect(router.serializeUrl(value as UrlTree)).toBe('/login');
  });
});
