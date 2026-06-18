import { Injectable, inject, computed } from '@angular/core';
import { AuthService } from './auth';

@Injectable({ providedIn: 'root' })
export class AvatarStateService {
  private readonly auth = inject(AuthService);
  private readonly defaultAvatar = 'profile.svg';

  readonly avatarSrc = computed(() => {
    const pic = this.auth.currentUser()?.profile_picture;
    return pic ? pic : this.defaultAvatar;
  });

  refresh(): void {
    this.auth.loadCurrentUser().subscribe();
  }
}