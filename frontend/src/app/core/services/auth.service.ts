import { Injectable, signal, computed } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { tap, catchError, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface Company {
  id: string;
  name: string;
  address: string;
  siret: string;
  tva: string;
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  profile_picture?: string;
  companies: Company[];
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  message: string;
  user: User;
  profile: UserProfile;
  csrf_token: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly apiUrl = environment.apiUrl;
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  private currentProfileSubject = new BehaviorSubject<UserProfile | null>(null);
  private csrfToken: string | null = null;

  public currentUser$ = this.currentUserSubject.asObservable();
  public currentProfile$ = this.currentProfileSubject.asObservable();
  public isAuthenticated$ = this.currentUser$.pipe(map(user => !!user));

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    // Try to restore session on startup
    this.checkAuth().subscribe();
  }

  get currentUser(): User | null {
    return this.currentUserSubject.value;
  }

  get currentProfile(): UserProfile | null {
    return this.currentProfileSubject.value;
  }

  get isAuthenticated(): boolean {
    return !!this.currentUser;
  }

  get token(): string | null {
    return this.csrfToken;
  }

  getCsrfToken(): Observable<string> {
    return this.http.get<{ csrf_token: string }>(`${this.apiUrl}/auth/csrf/`, {
      withCredentials: true
    }).pipe(
      tap(response => {
        this.csrfToken = response.csrf_token;
      }),
      map(response => response.csrf_token)
    );
  }

  login(username: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/auth/login/`, {
      username,
      password
    }, {
      withCredentials: true
    }).pipe(
      tap(response => {
        this.currentUserSubject.next(response.user);
        this.currentProfileSubject.next(response.profile);
        this.csrfToken = response.csrf_token;
      }),
      catchError(this.handleError)
    );
  }

  logout(): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/logout/`, {}, {
      withCredentials: true
    }).pipe(
      tap(() => {
        this.currentUserSubject.next(null);
        this.currentProfileSubject.next(null);
        this.csrfToken = null;
        this.router.navigate(['/login']);
      }),
      catchError(this.handleError)
    );
  }

  checkAuth(): Observable<any> {
    return this.http.get<{ user: User; profile: UserProfile }>(`${this.apiUrl}/auth/me/`, {
      withCredentials: true
    }).pipe(
      tap(response => {
        this.currentUserSubject.next(response.user);
        this.currentProfileSubject.next(response.profile);
        this.csrfToken = (response as any).csrf_token;
      }),
      catchError((error) => {
        this.currentUserSubject.next(null);
        this.currentProfileSubject.next(null);
        return throwError(() => error);
      })
    );
  }

  updateProfile(profileData: Partial<UserProfile> | FormData): Observable<UserProfile> {
    return this.http.patch<UserProfile>(`${this.apiUrl}/linktree/profile/update_profile/`, profileData, {
      withCredentials: true
    }).pipe(
      tap(profile => {
        this.currentProfileSubject.next(profile);
      }),
      catchError(this.handleError)
    );
  }

  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An error occurred';
    if (error.error instanceof ErrorEvent) {
      errorMessage = error.error.message;
    } else if (error.error?.error) {
      errorMessage = error.error.error;
    } else if (error.status === 401) {
      errorMessage = 'Invalid credentials';
    } else if (error.status === 403) {
      errorMessage = 'Access denied';
    }
    return throwError(() => new Error(errorMessage));
  }
}
