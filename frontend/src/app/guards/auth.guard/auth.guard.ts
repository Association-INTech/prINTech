import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router'
import { catchError, map, of, switchMap } from 'rxjs';
import { AuthService } from '../../services/auth';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService)
  const router = inject(Router)

  if (authService.isLoggedIn()) {
    return true;
  }

  return authService.refreshToken().pipe(
    switchMap(() => authService.loadCurrentUser()),
    map(() => true),
    catchError(() => of(router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } })))
  );
}
