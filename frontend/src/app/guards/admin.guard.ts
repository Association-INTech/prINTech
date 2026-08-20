import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map, catchError, of, switchMap } from 'rxjs';
import { AuthService } from '../services/auth';

export const adminGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const loginRedirect = () => router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
  const resolveAdminAccess = () => authService.loadCurrentUser().pipe(
    map((user) => (user.is_staff ? true : router.createUrlTree(['/']))),
    catchError(() => of(loginRedirect()))
  );

  if (!authService.isLoggedIn()) {
    return authService.refreshToken().pipe(
      switchMap(() => resolveAdminAccess()),
      catchError(() => of(loginRedirect()))
    );
  }

  return resolveAdminAccess();
};
