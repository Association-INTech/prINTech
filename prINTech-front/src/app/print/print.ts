import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { finalize } from 'rxjs';
import { Print as printService, Filament, PrintRequestResponse } from '../services/print';

@Component({
  selector: 'app-print',
  imports: [CommonModule],
  templateUrl: './print.html',
  styleUrl: './print.css',
})
export class Print implements OnInit {
  private readonly printService = inject(printService);

  readonly loading = signal(false);
  readonly errorMessage = signal('');
  readonly successMessage = signal('');
  readonly filaments = signal<Filament[]>([]);
  
  readonly selectedMaterial = signal<string>('');
  readonly selectedColor = signal<string>('');
  readonly selectedQuantity = signal<number>(1);
  
  readonly isFileSelected = signal<boolean>(false);
  private selectedFile: File | null = null;

  readonly availableMaterials = computed(() => {
    return Array.from(new Set(this.filaments().map((f) => f.type)));
  });

  readonly availableColors = computed(() => {
    const material = this.selectedMaterial();
    if (!material) return [];
    return Array.from(new Set(
      this.filaments()
        .filter((f) => f.type === material)
        .map((f) => f.color_name)
    ));
  });

  readonly selectedFilament = computed<Filament | null>(() => {
    const material = this.selectedMaterial();
    const color = this.selectedColor();
    return this.filaments().find(f => f.type === material && f.color_name === color) ?? null;
  });

  readonly selectedFilamentId = computed<number | null>(() => {
    return this.selectedFilament()?.id ?? null;
  });
  ngOnInit(): void {
    this.loadFilaments();
  }

  onMaterialChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.selectedMaterial.set(target.value);
    
    // Automatically match the first available color option for this new material
    const colors = this.availableColors();
    this.selectedColor.set(colors.length > 0 ? colors[0] : '');
  }

  onColorChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.selectedColor.set(target.value);
  }

  onQuantityChange(event: Event): void {
    const value = Number((event.target as HTMLInputElement).value);
    this.selectedQuantity.set(Math.max(1, value || 1));
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.selectedFile = file;
    this.isFileSelected.set(file !== null);
  }

  SendRequest(fileInput: HTMLInputElement, comment: string): void {
    if (this.loading()) return;

    const file = fileInput.files?.[0] ?? this.selectedFile;
    const filamentId = this.selectedFilamentId();

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
        number_of_printing: this.selectedQuantity(),
      })
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (response: PrintRequestResponse) => {
          this.successMessage.set(`Demande envoyée avec succès. Statut: ${response.status}.`);
          this.resetForm(fileInput);
        },
        error: () => {
          this.errorMessage.set("Impossible d'envoyer la demande. Vérifiez le backend et les champs saisis.");
          this.scrollToTop();
          setTimeout(() => this.errorMessage.set(''), 8000);
        },
      });
  }

  private loadFilaments(): void {
    this.printService.getFilaments().subscribe({
      next: (filaments) => {
        this.filaments.set(filaments);
        if (filaments.length > 0) {
          this.selectedMaterial.set(filaments[0].type);
          this.selectedColor.set(filaments[0].color_name);
        }
      },
      error: () => {
        this.errorMessage.set('Impossible de charger les filaments depuis le backend.');
      },
    });
  }

  private resetForm(fileInput: HTMLInputElement): void {
    this.scrollToTop();
    fileInput.value = '';
    this.selectedFile = null;
    this.isFileSelected.set(false);
    this.selectedQuantity.set(1);
    setTimeout(() => this.successMessage.set(''), 6000);
  }

  private scrollToTop(): void {
    try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch {}
  }
}