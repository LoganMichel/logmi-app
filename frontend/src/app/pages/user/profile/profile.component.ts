import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService, UserProfile } from '../../../core/services/auth.service';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.css'
})
export class ProfileComponent implements OnInit {
  private authService = inject(AuthService);
  
  linktreeUrl = environment.linktreeUrl;

  profile = signal<UserProfile | null>(null);
  isEditing = signal(false);
  isSaving = signal(false);
  message = signal<{ type: 'success' | 'error'; text: string } | null>(null);

  // Edit form fields
  firstName = signal('');
  lastName = signal('');
  email = signal('');
  phone = signal('');

  selectedFile = signal<File | null>(null);
  previewUrl = signal<string | null>(null);

  ngOnInit() {
    this.authService.currentProfile$.subscribe(profile => {
      if (profile) {
        this.profile.set(profile);
        this.resetForm(profile);
      }
    });
  }

  resetForm(profile: UserProfile) {
    this.firstName.set(profile.first_name);
    this.lastName.set(profile.last_name);
    this.email.set(profile.email);
    this.phone.set(profile.phone);
    if (profile.profile_picture) {
      this.previewUrl.set(profile.profile_picture);
    }
  }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.selectedFile.set(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = () => {
        this.previewUrl.set(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  }

  startEditing() {
    this.isEditing.set(true);
    this.message.set(null);
  }

  cancelEditing() {
    this.isEditing.set(false);
    this.selectedFile.set(null);
    if (this.profile()) {
      this.resetForm(this.profile()!);
    }
  }

  saveProfile() {
    this.isSaving.set(true);
    this.message.set(null);

    const formData = new FormData();
    formData.append('first_name', this.firstName());
    formData.append('last_name', this.lastName());
    formData.append('email', this.email());
    formData.append('phone', this.phone());
    
    if (this.selectedFile()) {
      formData.append('profile_picture', this.selectedFile()!);
    }

    this.authService.updateProfile(formData).subscribe({
      next: (profile) => {
        this.profile.set(profile);
        this.isEditing.set(false);
        this.isSaving.set(false);
        this.selectedFile.set(null);
        this.message.set({ type: 'success', text: 'Profil mis à jour avec succès !' });
        setTimeout(() => this.message.set(null), 3000);
      },
      error: (err) => {
        this.isSaving.set(false);
        this.message.set({ type: 'error', text: err.message || 'Erreur lors de la mise à jour' });
      }
    });
  }
}
