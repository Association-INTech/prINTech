import { Component, inject, signal, computed } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NgIf } from '@angular/common';
import { AvatarStateService } from '../../services/avatar-state';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-header',
  imports: [RouterLink, NgIf],
  templateUrl: './header.html',
  styleUrl: './header.css',
})
export class Header {
  private readonly avatarState = inject(AvatarStateService);
  private readonly auth = inject(AuthService);

  title = signal('prINTech') ;
  avatarSrc = this.avatarState.avatarSrc;
  isAdmin = computed(() => !!this.auth.currentUser()?.is_staff);
}
