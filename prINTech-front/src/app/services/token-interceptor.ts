import { HttpInterceptorFn, HttpRequest, HttpHandlerFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './auth';

export const tokenInterceptor: HttpInterceptorFn = (req: HttpRequest<unknown>, next: HttpHandlerFn) => {
  const authService = inject(AuthService);

  const token = authService.getToken();
  if (!token) {
    return next(req);
  }

  const requestWithToken = req.clone({
    setHeaders:{
      Authorization: `Bearer ${token}`
    }
  })
  return next(requestWithToken);
};
