import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { Company } from '../../../core/services/auth.service';

@Component({
  selector: 'app-companies',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './companies.component.html',
  styleUrl: './companies.component.css'
})
export class CompaniesComponent implements OnInit {
  private api = inject(ApiService);

  companies = signal<Company[]>([]);
  isLoading = signal(true);
  showModal = signal(false);
  editingCompany = signal<Company | null>(null);
  isSaving = signal(false);
  message = signal<{ type: 'success' | 'error'; text: string } | null>(null);

  // Form fields
  name = signal('');
  address = signal('');
  siret = signal('');
  tva = signal('');

  ngOnInit() {
    this.loadCompanies();
  }

  loadCompanies() {
    this.isLoading.set(true);
    this.api.get<Company[]>('/linktree/companies/', { mine: true }).subscribe({
      next: (data) => {
        this.companies.set(data);
        this.isLoading.set(false);
      },
      error: () => {
        this.isLoading.set(false);
      }
    });
  }

  openModal(company?: Company) {
    if (company) {
      this.editingCompany.set(company);
      this.name.set(company.name);
      this.address.set(company.address);
      this.siret.set(company.siret);
      this.tva.set(company.tva);
    } else {
      this.editingCompany.set(null);
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
    this.address.set('');
    this.siret.set('');
    this.tva.set('');
  }

  saveCompany() {
    if (!this.name()) {
      this.message.set({ type: 'error', text: 'Le nom est requis' });
      return;
    }

    this.isSaving.set(true);
    const data = {
      name: this.name(),
      address: this.address(),
      siret: this.siret(),
      tva: this.tva(),
    };

    const request = this.editingCompany()
      ? this.api.put<Company>(`/linktree/companies/${this.editingCompany()!.id}/`, data)
      : this.api.post<Company>('/linktree/companies/', data);

    request.subscribe({
      next: () => {
        this.loadCompanies();
        this.closeModal();
        this.isSaving.set(false);
        this.message.set({ type: 'success', text: this.editingCompany() ? 'Société modifiée' : 'Société créée' });
        setTimeout(() => this.message.set(null), 3000);
      },
      error: (err) => {
        this.isSaving.set(false);
        this.message.set({ type: 'error', text: err.message || 'Erreur' });
      }
    });
  }

  deleteCompany(company: Company) {
    if (!confirm(`Supprimer "${company.name}" ?`)) return;

    this.api.delete(`/linktree/companies/${company.id}/`).subscribe({
      next: () => {
        this.loadCompanies();
        this.message.set({ type: 'success', text: 'Société supprimée' });
        setTimeout(() => this.message.set(null), 3000);
      },
      error: (err) => {
        this.message.set({ type: 'error', text: err.message || 'Erreur' });
      }
    });
  }
}
