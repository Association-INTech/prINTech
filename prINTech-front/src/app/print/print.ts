import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { finalize } from 'rxjs';
import { Print as printService, Filament, PrintRequestResponse } from '../services/print';
import { PrintRequestPayload } from '../services/print';

@Component({
  selector: 'app-print',
  imports: [CommonModule],
  templateUrl: './print.html',
  styleUrl: './print.css',
})
export class Print {
  private readonly printService = inject(printService);
  readonly loading = signal(false);
  readonly errorMessage = signal('');
  readonly successMessage = signal('');
  readonly filaments = signal<Filament[]>([]);
  readonly selectedFilamentId = signal<number | null>(null);

  private selectedFile: File | null = null;

  ngOnInit(): void {
    this.loadFilaments();
  }

  getTypes(): string[] {
    const types = Array.from(new Set(this.filaments().map((f) => f.type)));
    return types;
  }

  getColorsFor(type: string): string[] {
    if (!type) return [];
    const colors = this.filaments()
      .filter((f) => f.type === type)
      .map((f) => f.color_name);
    return Array.from(new Set(colors));
  }

  SendRequest(
    fileInput: HTMLInputElement,
    material: string,
    color: string,
    quantity: string,
    comment: string,
  ): void {
    if (this.loading()) {
      return;
    }

    const file = fileInput.files?.[0] ?? this.selectedFile;
    const filamentId = this.findFilamentId(material, color);
    const numberOfPrinting = Math.max(0, Number(quantity) || 0);

    this.errorMessage.set('');
    this.successMessage.set('');

    if (!file) {
      this.errorMessage.set('Veuillez sélectionner un fichier STL.');
      return;
    }

    if (filamentId === null) {
      this.errorMessage.set('Aucun filament correspondant au matériau et à la couleur sélectionnés.');
      return;
    }

    this.loading.set(true);

    this.printService
      .SendRequest({
        filament: filamentId,
        comment: comment.trim(),
        path: file,
        number_of_printing: numberOfPrinting,
      })
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (response: PrintRequestResponse) => {
          const msg = `Demande envoyée avec succès. Statut: ${response.status}.`;
          this.successMessage.set(msg);
          // scroll to top so the banner is visible and auto-hide after a few seconds
          try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch {}
          setTimeout(() => this.successMessage.set(''), 6000);
          fileInput.value = '';
          this.selectedFile = null;
          this.selectedFilamentId.set(filamentId);
        },
        error: () => {
          const err = 'Impossible d\'envoyer la demande. Vérifiez le backend et les champs saisis.';
          this.errorMessage.set(err);
          try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch {}
          setTimeout(() => this.errorMessage.set(''), 8000);
        },
      });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files?.[0] ?? null;
  }

  updateSelectedFilament(material: string, color: string): void {
    this.selectedFilamentId.set(this.findFilamentId(material, color));
  }

  private loadFilaments(): void {
    this.printService.getFilaments().subscribe({
      next: (filaments) => {
        this.filaments.set(filaments);
        this.selectedFilamentId.set(this.findFilamentId('PLA', 'Noir'));
      },
      error: () => {
        this.errorMessage.set('Impossible de charger les filaments depuis le backend.');
      },
    });
  }

  private findFilamentId(material: string, color: string): number | null {
    const filament = this.filaments().find(
      (item) => item.type === material && item.color_name === color,
    );

    return filament?.id ?? null;
  }

}
