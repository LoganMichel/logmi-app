import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, Subject, throwError } from 'rxjs';
import { vi } from 'vitest';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { DashboardComponent } from './dashboard.component';

describe('Périodes du dashboard', () => {
  const get = vi.fn();

  beforeEach(async () => {
    get.mockReset();
    get.mockReturnValue(of({}));
    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        provideRouter([]),
        { provide: ApiService, useValue: { get } },
        { provide: AuthService, useValue: { currentUser: { username: 'test' } } },
      ],
    }).compileComponents();
  });

  it('charge les deux API sur 30 jours par défaut et affiche les quatre périodes', async () => {
    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    expect(get).toHaveBeenCalledWith('/linktree/dashboard/', { days: 30 });
    expect(get).toHaveBeenCalledWith('/tinyurl/dashboard/', { days: 30 });
    const element: HTMLElement = fixture.nativeElement;
    const buttons: HTMLButtonElement[] = Array.from(element.querySelectorAll('.period-button'));
    expect(buttons.map((button: HTMLButtonElement) => button.textContent?.trim()))
      .toEqual(['30 jours', 'Trimestre', 'Semestre', 'Année']);
    expect(buttons[0].getAttribute('aria-pressed')).toBe('true');
  });

  for (const days of [90, 180, 365] as const) {
    it(`recharge les deux API pour la période de ${days} jours`, async () => {
      const fixture = TestBed.createComponent(DashboardComponent);
      fixture.detectChanges();
      await fixture.whenStable();
      const element: HTMLElement = fixture.nativeElement;
      const button = element.querySelector<HTMLButtonElement>(`[data-days="${days}"]`);
      button?.click();
      await fixture.whenStable();
      expect(get).toHaveBeenCalledWith('/linktree/dashboard/', { days });
      expect(get).toHaveBeenCalledWith('/tinyurl/dashboard/', { days });
      expect(button?.getAttribute('aria-pressed')).toBe('true');
      expect(element.textContent).toContain(`${days} derniers jours`);
    });
  }

  it('permet de recharger une autre période après une erreur', async () => {
    get.mockReturnValue(throwError(() => new Error('Indisponible')));
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    await fixture.componentInstance.loadStats();
    fixture.detectChanges();
    expect(fixture.componentInstance.error()).not.toBeNull();
    get.mockReturnValue(of({ total_clicks: 3 }));
    const element: HTMLElement = fixture.nativeElement;
    element.querySelector<HTMLButtonElement>('[data-days="365"]')?.click();
    await fixture.whenStable();
    expect(fixture.componentInstance.error()).toBeNull();
    expect(fixture.componentInstance.stats()?.tinyurl.total_clicks).toBe(3);
    errorSpy.mockRestore();
  });

  it('ignore une ancienne réponse quand la période a changé', async () => {
    const oldResponse = new Subject<{ total_clicks: number }>();
    get.mockReturnValue(oldResponse);
    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();
    get.mockReturnValue(of({ total_clicks: 5 }));
    fixture.componentInstance.selectPeriod(365);
    await fixture.whenStable();
    oldResponse.next({ total_clicks: 1 });
    oldResponse.complete();
    await fixture.whenStable();
    expect(fixture.componentInstance.stats()?.tinyurl.total_clicks).toBe(5);
  });
});
