import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Header } from './components/header/header';
import { provideHttpClient } from '@angular/common/http';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Header ],
  template: `

    <app-header />
    <main>
      <router-outlet />
    </main>
  `,
  styles: [
    `
    main {
      padding: 16px ;
    }
    `
  ],
})
export class App {
  protected readonly title = signal('prINTech-frnt');
}
