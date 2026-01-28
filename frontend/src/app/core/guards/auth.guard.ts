import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { map, take, catchError } from 'rxjs/operators';
import { of } from 'rxjs';

/**
 * Guard for protected routes - redirects to login if not authenticated
 */
export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // First check if already authenticated
  if (authService.isAuthenticated) {
    return true;
  }

  // Try to restore session
  return authService.checkAuth().pipe(
    take(1),
    map(() => true),
    catchError(() => {
      router.navigate(['/login'], { queryParams: { returnUrl: state.url } });
      return of(false);
    })
  );
};

/**
 * Guard for login page - redirects to dashboard if already authenticated
 */
export const guestGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // If already authenticated, redirect to dashboard
  if (authService.isAuthenticated) {
    router.navigate(['/dashboard']);
    return false;
  }

  // Check if there's an active session
  return authService.checkAuth().pipe(
    take(1),
    map(() => {
      // Session exists, redirect to dashboard
      router.navigate(['/dashboard']);
      return false;
    }),
    catchError(() => {
      // No session, allow access to login page
      return of(true);
    })
  );
};
