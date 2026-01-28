import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { environment } from '../../../../environments/environment';

interface Link {
  id: string;
  name: string;
  url: string;
  icon: string;
  is_active: boolean;
  order: number;
  total_clicks: number;
  qrcode_clicks: number;
  qrcode_image?: string;
  created_at: string;
}

@Component({
  selector: 'app-linktree-links',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './links.component.html',
  styleUrl: './links.component.css'
})
export class LinktreeLinksComponent implements OnInit {
  private api = inject(ApiService);
  private authService = inject(AuthService);
  
  linktreeUrl = environment.linktreeUrl;
  
  get username(): string {
    return this.authService.currentUser?.username || '';
  }

  links = signal<Link[]>([]);
  isLoading = signal(true);
  showModal = signal(false);
  editingLink = signal<Link | null>(null);
  isSaving = signal(false);
  message = signal<{ type: 'success' | 'error'; text: string } | null>(null);

  // Form fields
  name = signal('');
  url = signal('');
  icon = signal('');
  isActive = signal(true);

  ngOnInit() {
    this.loadLinks();
  }

  loadLinks() {
    this.isLoading.set(true);
    this.api.get<Link[]>('/linktree/links/').subscribe({
      next: (data) => {
        this.links.set(data);
        this.isLoading.set(false);
      },
      error: () => {
        this.isLoading.set(false);
      }
    });
  }

  openModal(link?: Link) {
    if (link) {
      this.editingLink.set(link);
      this.name.set(link.name);
      this.url.set(link.url);
      this.icon.set(link.icon);
      this.isActive.set(link.is_active);
    } else {
      this.editingLink.set(null);
      this.resetForm();
    }
    this.showModal.set(true);
  }

  closeModal() {
    this.showModal.set(false);
    this.resetForm();
  }

  resetForm() {
    this.name.set('');
    this.url.set('');
    this.icon.set('');
    this.isActive.set(true);
  }

  saveLink() {
    if (!this.name() || !this.url()) {
      this.message.set({ type: 'error', text: 'Nom et URL requis' });
      return;
    }

    this.isSaving.set(true);
    const data = {
      name: this.name(),
      url: this.url(),
      icon: this.icon(),
      is_active: this.isActive(),
    };

    const request = this.editingLink()
      ? this.api.put<Link>(`/linktree/links/${this.editingLink()!.id}/`, data)
      : this.api.post<Link>('/linktree/links/', data);

    request.subscribe({
      next: () => {
        this.loadLinks();
        this.closeModal();
        this.isSaving.set(false);
        this.message.set({ type: 'success', text: this.editingLink() ? 'Lien modifié' : 'Lien créé' });
        setTimeout(() => this.message.set(null), 3000);
      },
      error: (err) => {
        this.isSaving.set(false);
        this.message.set({ type: 'error', text: err.message || 'Erreur' });
      }
    });
  }

  deleteLink(link: Link) {
    if (!confirm(`Supprimer "${link.name}" ?`)) return;

    this.api.delete(`/linktree/links/${link.id}/`).subscribe({
      next: () => {
        this.loadLinks();
        this.message.set({ type: 'success', text: 'Lien supprimé' });
        setTimeout(() => this.message.set(null), 3000);
      },
      error: (err) => {
        this.message.set({ type: 'error', text: err.message || 'Erreur' });
      }
    });
  }

  toggleActive(link: Link) {
    this.api.patch<Link>(`/linktree/links/${link.id}/`, { is_active: !link.is_active }).subscribe({
      next: () => this.loadLinks(),
      error: () => {}
    });
  }

  // Drag and drop
  draggedIndex = signal<number | null>(null);
  dragOverIndex = signal<number | null>(null);

  onDragStart(event: DragEvent, index: number) {
    this.draggedIndex.set(index);
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', index.toString());
    }
  }

  onDragEnd() {
    this.draggedIndex.set(null);
    this.dragOverIndex.set(null);
  }

  onDragOver(event: DragEvent, index: number) {
    event.preventDefault();
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = 'move';
    }
    if (this.draggedIndex() !== index) {
      this.dragOverIndex.set(index);
    }
  }

  onDragLeave() {
    this.dragOverIndex.set(null);
  }

  onDrop(event: DragEvent, dropIndex: number) {
    event.preventDefault();
    const dragIndex = this.draggedIndex();
    
    if (dragIndex === null || dragIndex === dropIndex) {
      this.onDragEnd();
      return;
    }

    // Reorder locally
    const linksCopy = [...this.links()];
    const [draggedItem] = linksCopy.splice(dragIndex, 1);
    linksCopy.splice(dropIndex, 0, draggedItem);
    
    // Update order values
    const updatedLinks = linksCopy.map((link, index) => ({
      ...link,
      order: index
    }));
    
    this.links.set(updatedLinks);
    this.onDragEnd();

    // Save new order to backend
    this.saveOrder(updatedLinks);
  }

  saveOrder(links: Link[]) {
    const orders = links.map((link, index) => ({
      id: link.id,
      order: index
    }));

    // Update each link's order
    orders.forEach(({ id, order }) => {
      this.api.patch(`/linktree/links/${id}/`, { order }).subscribe({
        error: () => this.loadLinks() // Reload on error
      });
    });
  }
}
