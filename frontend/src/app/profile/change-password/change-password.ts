import { Component, inject, signal } from '@angular/core';
import { AuthService } from '../../services/auth';
import { ReactiveFormsModule, Validators, FormBuilder, AbstractControl, ValidationErrors } from '@angular/forms';
import { finalize } from 'rxjs';


@Component({
  selector: 'app-change-password',
  imports: [ReactiveFormsModule],
  templateUrl: './change-password.html',
  styleUrl: './change-password.css',
})
export class ChangePassword {
  private readonly authService = inject(AuthService)
  private readonly formBuilder = inject(FormBuilder)

  readonly loading = signal(false);
  readonly errorMessage = signal('');
  readonly successMessage = signal('');

  readonly changePasswordForm = this.formBuilder.nonNullable.group(
    {
      old_password: ['', [Validators.required, Validators.minLength(8)]],
      new_password: ['', [Validators.required, Validators.minLength(8)]],
      confirm_password: ['', [Validators.required, Validators.minLength(8)]]
    },
    { validators: [this.passwordsMatchValidator] }
  )

  private passwordsMatchValidator(control: AbstractControl): ValidationErrors | null {
    const newPassword = control.get('new_password')?.value
    const confirmPassword = control.get('confirm_password')?.value
    return newPassword === confirmPassword ? null : { passwordMismatch: true }
  }

  onChangePassword(): void {
    if (this.changePasswordForm.invalid || this.loading()) {
      this.changePasswordForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set('');
    this.successMessage.set('');
    this.loading.set(true);

    const { old_password, new_password, confirm_password } = this.changePasswordForm.getRawValue();

    this.authService
      .change_password(old_password, new_password, confirm_password)
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: () => {
          this.successMessage.set('Mot de passe mis à jour avec succès.');
          this.changePasswordForm.reset({
            old_password: '',
            new_password: '',
            confirm_password: '',
          });
        },
        error: () => {
          this.errorMessage.set('Impossible de mettre à jour le mot de passe. Vérifiez vos informations.');
        },
      });
  }
}
