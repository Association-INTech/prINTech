import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AvatarStateService } from '../../services/avatar-state';

@Component({
  selector: 'app-header',
  imports: [RouterLink],
  templateUrl: './header.html',
  styleUrl: './header.css',
})
export class Header {
  private readonly avatarState = inject(AvatarStateService);

  title = signal('prINTech') ;
  avatarSrc = this.avatarState.avatarSrc;
}
