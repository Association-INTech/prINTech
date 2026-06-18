import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { ReactiveFormsModule, Validators, FormBuilder } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs';
import { AuthService } from '../services/auth';

@Component({
  selector: 'app-admin-login',
  imports: [ReactiveFormsModule],
  templateUrl: './admin-login.html',
  styleUrl: './admin-login.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminLogin {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly formBuilder = inject(FormBuilder);

  readonly loading = signal(false);
  readonly errorMessage = signal('');

  readonly loginForm = this.formBuilder.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  onLogin(): void {
    if (this.loginForm.invalid || this.loading()) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set('');
    this.loading.set(true);

    const { email, password } = this.loginForm.getRawValue();

    this.auth
      .login(email, password)
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: () => {
          this.auth.getCurrentUser().subscribe({
            next: (user) => {
              if (!user.is_staff) {
                this.auth.logout();
                this.errorMessage.set('Compte non administrateur.');
                return;
              }
              void this.router.navigate(['/admin/dashboard']);
            },
            error: () => {
              this.auth.logout();
              this.errorMessage.set('Impossible de vérifier le rôle administrateur.');
            },
          });
        },
        error: () => {
          this.errorMessage.set('Identifiants administrateur invalides.');
        },
      });
  }
}
