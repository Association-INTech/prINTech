import { HttpClient } from '@angular/common/http';
import { Component, inject } from '@angular/core';
import { finalize } from 'rxjs';
import { AvatarStateService } from '../../services/avatar-state';

@Component({
  selector: 'app-profile-picture',
  imports: [],
  templateUrl: './profile-picture.html',
  styleUrl: './profile-picture.css',
})
export class ProfilePicture {
  private readonly http = inject(HttpClient);
  private readonly avatarState = inject(AvatarStateService);

  fileName = '';
  errorMessage = '';
  successMessage = '';
  loading = false;
  private selectedFile: File | null = null;
  private readonly uploadUrl = '/api/v1/user/me/profile-picture/';

  avatarSrc = this.avatarState.avatarSrc;

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;

    this.errorMessage = '';
    this.successMessage = '';

    if (file) {
      this.fileName = file.name;
      this.selectedFile = file;

      const reader = new FileReader();
      reader.onload = () => {
        const imageDataUrl = reader.result;
        if (typeof imageDataUrl === 'string') {
          this.avatarState.setAvatar(imageDataUrl);
        }
      };
      reader.readAsDataURL(file);

      this.uploadSelectedFile();
      return;
    }

    this.fileName = '';
    this.selectedFile = null;
  }

  private uploadSelectedFile(): void {
    if (!this.selectedFile || this.loading) {
      return;
    }

    this.errorMessage = '';
    this.successMessage = '';
    this.loading = true;

    const formData = new FormData();
    formData.append('thumbnail', this.selectedFile);

    this.http
      .post(this.uploadUrl, formData)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: () => {
          this.successMessage = 'Photo envoyée avec succès.';
        },
        error: () => {
          this.errorMessage = 'Échec de l\'upload. Vérifie l\'IP ou le backend.';
        },
      });
  }
}
