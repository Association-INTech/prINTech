import { ChangeDetectionStrategy, Component, inject, signal, OnInit } from '@angular/core';
import { ReactiveFormsModule, Validators, FormBuilder } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { finalize, switchMap } from 'rxjs';
import { AuthService } from '../services/auth';
import { HomeService } from '../services/home';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Login implements OnInit{
  private readonly auth = inject(AuthService);
  private readonly homeService = inject(HomeService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly formBuilder = inject(FormBuilder);

  readonly loading = signal(false);
  readonly errorMessage = signal('');

  readonly loginForm = this.formBuilder.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  ngOnInit(): void {
    const savedEmail = localStorage.getItem('last_login_email');
    if (savedEmail) {
      this.loginForm.patchValue({ email: savedEmail });
    }
  }

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
      .pipe(switchMap(() => this.auth.loadCurrentUser()))
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (user) => {
          localStorage.setItem('last_login_email', email);
          const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl');
          if (returnUrl && returnUrl.startsWith('/')) {
            void this.router.navigateByUrl(returnUrl);
            return;
          }

          if (user.is_staff) {
            void this.router.navigate(['/admin/dashboard']);
          } else {
            void this.router.navigate(['/']);
          }
        },
        error: () => {
          this.errorMessage.set('Adresse e-mail ou mot de passe invalide.');
        },
      });
  }
}
