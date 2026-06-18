import { Component, inject, computed } from '@angular/core';
import { AuthService } from '../services/auth';
import { ChangePassword } from './change-password/change-password';
import { ProfilePicture } from './profile-picture/profile-picture';

@Component({
  selector: 'app-profile',
  imports: [ChangePassword, ProfilePicture],
  templateUrl: './profile.html',
  styleUrl: './profile.css',
})
export class Profile {
  private readonly auth = inject(AuthService);

  username = computed(() => this.auth.currentUser()?.username ?? '');
  email    = computed(() => this.auth.currentUser()?.email ?? '');
  credit   = computed(() => this.auth.currentUser()?.credit ?? 0);
  isAdmin  = computed(() => this.auth.currentUser()?.is_staff ?? false);
}