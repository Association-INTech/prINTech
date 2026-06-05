import { HttpInterceptorFn, HttpRequest, HttpHandlerFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from './auth';

export const tokenInterceptor: HttpInterceptorFn = (req: HttpRequest<unknown>, next: HttpHandlerFn) => {
  const authService = inject(AuthService);

  if (req.url.includes('/api/v1/token/')) {
    return next(req);
  }

  const token = authService.getToken();
  if (!token) {
    return next(req);
  }

  const requestWithToken = (accessToken: string) =>
    req.clone({
      setHeaders: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

  if (!authService.isLoggedIn()) {
    return authService.refreshToken().pipe(
      switchMap(({ access }) => next(requestWithToken(access))),
      catchError((error) => {
        authService.logout();
        return throwError(() => error);
      })
    );
  }

  return next(requestWithToken(token));
};
