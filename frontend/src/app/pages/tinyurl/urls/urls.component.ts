import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { environment } from '../../../../environments/environment';

interface Url {
  id: string;
  long_url: string;
  short_code: string;
  is_active: boolean;
  total_clicks: number;
  qrcode_clicks: number;
  qrcode_image?: string;
  created_at: string;
}

@Component({
  selector: 'app-tinyurl-urls',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './urls.component.html',
  styleUrl: './urls.component.css'
})
export class TinyurlUrlsComponent implements OnInit {
  private api = inject(ApiService);
  
  tinyurlUrl = environment.linktreeUrl;

  urls = signal<Url[]>([]);
  isLoading = signal(true);
  showModal = signal(false);
  editingUrl = signal<Url | null>(null);
  isSaving = signal(false);
  message = signal<{ type: 'success' | 'error'; text: string } | null>(null);
  copiedId = signal<string | null>(null);

  // Form fields
  longUrl = signal('');
  customAlias = signal('');
  isActive = signal(true);

  ngOnInit() {
    this.loadUrls();
  }

  loadUrls() {
    this.isLoading.set(true);
    this.api.get<Url[]>('/tinyurl/urls/').subscribe({
      next: (data) => {
        this.urls.set(data);
        this.isLoading.set(false);
      },
      error: () => {
        this.isLoading.set(false);
      }
    });
  }

  openModal(url?: Url) {
    if (url) {
      this.editingUrl.set(url);
      this.longUrl.set(url.long_url);
      this.customAlias.set(url.short_code || '');
      this.isActive.set(url.is_active);
    } else {
      this.editingUrl.set(null);
      this.resetForm();
    }
    this.showModal.set(true);
  }

  closeModal() {
    this.showModal.set(false);
    this.resetForm();
  }

  resetForm() {
    this.longUrl.set('');
    this.customAlias.set('');
    this.isActive.set(true);
  }

  saveUrl() {
    if (!this.longUrl()) {
      this.message.set({ type: 'error', text: 'URL longue requise' });
      return;
    }

    this.isSaving.set(true);
    const data: any = {
      long_url: this.longUrl(),
      is_active: this.isActive(),
      short_code: this.customAlias() || '' 
    };

    const request = this.editingUrl()
      ? this.api.put<Url>(`/tinyurl/urls/${this.editingUrl()!.id}/`, data)
      : this.api.post<Url>('/tinyurl/urls/', data);

    request.subscribe({
      next: () => {
        this.loadUrls();
        this.closeModal();
        this.isSaving.set(false);
        this.message.set({ type: 'success', text: this.editingUrl() ? 'URL modifiée' : 'URL créée' });
        setTimeout(() => this.message.set(null), 3000);
      },
      error: (err) => {
        this.isSaving.set(false);
        let errorMsg = 'Erreur lors de la sauvegarde';
        if (err.error) {
           if (typeof err.error === 'string') {
             errorMsg = err.error;
           } else if (err.error.short_code) {
             errorMsg = `Code court: ${err.error.short_code.join(', ')}`;
           } else if (err.error.detail) {
             errorMsg = err.error.detail;
           }
        }
        this.message.set({ type: 'error', text: errorMsg });
      }
    });
  }

  deleteUrl(url: Url) {
    if (!confirm(`Supprimer cette URL raccourcie ?`)) return;

    this.api.delete(`/tinyurl/urls/${url.id}/`).subscribe({
      next: () => {
        this.loadUrls();
        this.message.set({ type: 'success', text: 'URL supprimée' });
        setTimeout(() => this.message.set(null), 3000);
      },
      error: (err) => {
        this.message.set({ type: 'error', text: err.message || 'Erreur' });
      }
    });
  }

  toggleActive(url: Url) {
    this.api.patch<Url>(`/tinyurl/urls/${url.id}/`, { is_active: !url.is_active }).subscribe({
      next: () => this.loadUrls(),
      error: () => {}
    });
  }

  getShortUrl(url: Url): string {
    return `${this.tinyurlUrl}/${url.short_code}`;
  }

  copyToClipboard(url: Url) {
    const shortUrl = this.getShortUrl(url);
    navigator.clipboard.writeText(shortUrl).then(() => {
      this.copiedId.set(url.id);
      setTimeout(() => this.copiedId.set(null), 2000);
    });
  }
  downloadQrCode(url: Url) {
    if (!url.qrcode_image) return;
    const link = document.createElement('a');
    link.href = url.qrcode_image;
    link.download = `qrcode-${url.short_code}.png`;
    link.click();
  }
}
