import { HttpInterceptorFn, HttpRequest, HttpHandlerFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req: HttpRequest<unknown>, next: HttpHandlerFn) => {
  const router = inject(Router);
  const authService = inject(AuthService);

  // Clone request with credentials and CSRF token if available
  let headers = req.headers;
  const csrfToken = authService.token;
  
  // Only add CSRF token for mutating requests (POST, PUT, PATCH, DELETE)
  if (csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(req.method)) {
    headers = headers.set('X-CSRFToken', csrfToken);
  }

  const authReq = req.clone({
    withCredentials: true,
    headers
  });

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // 403 can also mean CSRF failure, but usually 401 is for login status
      if (error.status === 401) {
        // Clear any stored auth state and redirect to login
        router.navigate(['/login']);
      }
      return throwError(() => error);
    })
  );
};
