import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  // Public routes - redirect to dashboard if already logged in
  {
    path: 'login',
    loadComponent: () => import('./pages/auth/login/login.component').then(m => m.LoginComponent),
    canActivate: [guestGuard]
  },

  // Protected routes with main layout
  {
    path: '',
    loadComponent: () => import('./layout/main-layout/main-layout.component').then(m => m.MainLayoutComponent),
    canActivate: [authGuard],
    children: [
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      },
      {
        path: 'dashboard',
        loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent)
      },
      {
        path: 'profile',
        loadComponent: () => import('./pages/user/profile/profile.component').then(m => m.ProfileComponent)
      },
      {
        path: 'companies',
        loadComponent: () => import('./pages/user/companies/companies.component').then(m => m.CompaniesComponent)
      },
      // Linktree routes
      {
        path: 'linktree/links',
        loadComponent: () => import('./pages/linktree/links/links.component').then(m => m.LinktreeLinksComponent)
      },
      // TinyURL routes
      {
        path: 'tinyurl/urls',
        loadComponent: () => import('./pages/tinyurl/urls/urls.component').then(m => m.TinyurlUrlsComponent)
      }
    ]
  },

  // Catch-all redirect to login for unknown routes
  { path: '**', redirectTo: 'login' }
];
