import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class AvatarStateService {
  private readonly storageKey = 'profile_avatar_src';
  private readonly defaultAvatar = 'profile.svg';

  readonly avatarSrc = signal<string>(
    localStorage.getItem(this.storageKey) ?? this.defaultAvatar
  );

  setAvatar(src: string): void {
    this.avatarSrc.set(src);
    localStorage.setItem(this.storageKey, src);
  }
}
