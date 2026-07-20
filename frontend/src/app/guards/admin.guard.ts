import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map, catchError, of } from 'rxjs';
import { AuthService } from '../services/auth';

export const adminGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isLoggedIn()) {
    return router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
  }

  // fast path: if we already have the user loaded, use it
  const cached = authService.currentUser();
  if (cached) {
    return cached.is_staff ? true : router.createUrlTree(['/']);
  }

  // otherwise load the user and decide
  return authService.loadCurrentUser().pipe(
    map((user) => (user.is_staff ? true : router.createUrlTree(['/']))),
    catchError(() => of(router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } })))
  );
};
