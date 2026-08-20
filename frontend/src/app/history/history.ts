import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, ChangeDetectorRef, signal } from '@angular/core';
import { HistoryServices, Filament, Printer } from '../services/history-services';
import { HistoryItem } from './history.model';

@Component({
  selector: 'app-history',
  imports: [CommonModule],
  templateUrl: './history.html',
  styleUrl: './history.css',
})
export class History implements OnInit{
  private readonly historyService = inject(HistoryServices);
  private readonly cdr = inject(ChangeDetectorRef);

  fullHistory: HistoryItem[] = [];
  filteredHistory: HistoryItem[] = [];
  filaments: Filament[] = [];
  printers: Printer[] = []; 
  SearchQuery = '';

  readonly sortColumn = signal<'created_at'>('created_at');
  readonly sortDirection = signal<'asc' | 'desc'>('desc');

  errorMessage = '';
  successMessage = '';
  relaunchingIds = new Set<string>();
  payingIds = new Set<string>();

  ngOnInit(): void {
    this.loadFilaments();
    this.loadHistory();
    this.loadPrinters(); 
  }

  onSearch(event: Event) {
    this.SearchQuery = (event.target as HTMLInputElement).value;
    this.applyFilters();
  }

  // Filter status 
  readonly statusFilter = signal<string>('ONGOING');
  setStatusFilter(status: string): void {
    this.statusFilter.set(status);
    this.applyFilters();
  }

  private applyFilters(): void {
    const query = this.SearchQuery.toLowerCase();
    const currentFilter = this.statusFilter();
    
    // 1. Filtrage par recherche (nom de fichier)
    let filtered = !query 
      ? [...this.fullHistory] 
      : this.fullHistory.filter(item => {
          const fileName = this.getFileName(item.file?.path).toLowerCase();
          return fileName.includes(query);
        });

    // 2. Filtrage par statut
    if (currentFilter === 'ONGOING') {
      filtered = filtered.filter((item) => {
        const st = item.status;
        return st === 'SUBMITTED' || st === 'AWAITING_PAYMENT' || st==='PENDING' || st === 'PRINTING' || st === 'AWAITING_PICKUP';
      });
    } else if (currentFilter !== 'ALL') {
      filtered = filtered.filter((item) => item.status === currentFilter);
    }

    // 3. Tri par Date (created_at)
    const direction = this.sortDirection();
    filtered.sort((a, b) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();
      const res = dateA - dateB;
      return direction === 'asc' ? res : -res;
    });

    this.filteredHistory = filtered;
    this.cdr.detectChanges();
  }

  private loadFilaments(): void {
    this.historyService.getFilaments().subscribe({
      next: (filaments) => {
        this.filaments = filaments;
        this.cdr.detectChanges();
      },
      error: () => {
        this.filaments = [];
      },
    });
  }

  private loadPrinters(): void {
  this.historyService.getPrinters().subscribe({
    next: (printers) => {
      this.printers = printers;
      this.cdr.detectChanges();
    },
    error: () => {
        this.printers = [];
      },
  });
}

  private loadHistory(): void {
    this.historyService.getHistory().subscribe({
      next: (response: any) => {
        const items = response?.results ? response.results : (Array.isArray(response) ? response : []);
        this.fullHistory = items;
        this.applyFilters();
      },
      error: (err) => {
        this.errorMessage = err.message || 'Error occurred';
        this.fullHistory = [];
        this.applyFilters();
      },
    });
  }

  getFilamentName(filamentId: number | null | undefined): string {
    if (filamentId == null) return '-';
    const filament = this.filaments.find(f => f.id === filamentId);
    if (!filament) return `ID: ${filamentId}`;
    return `${filament.type} (${filament.color_name})`;
  }

  getFileName(path: string | null | undefined): string {
    if (!path) return '-';
    return path.split('/').pop() || path;
  }

  getPrinterName(printerName: string | null | undefined): string {
    if (!printerName) return '-';
    // Recherche l'imprimante par son nom dans la liste des imprimantes
    const printer = this.printers.find(p => String(p.name) === String(printerName));
    return printer ? printer.name : `ID: ${printerName}`;
  }

  onRelaunch(item: HistoryItem): void {
    if (this.relaunchingIds.has(item.id) || this.payingIds.has(item.id)) return;

    this.errorMessage = '';
    this.successMessage = '';
    this.relaunchingIds.add(item.id);

    this.historyService.relaunchRequest(item.id).subscribe({
      next: () => {
        this.successMessage = 'Demande relancée avec succès.';
        this.relaunchingIds.delete(item.id);
        this.loadHistory();
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.errorMessage = err?.error?.error || 'Impossible de relancer cette impression.';
        this.relaunchingIds.delete(item.id);
        this.cdr.detectChanges();
      },
    });
  }

  onPay(item: HistoryItem): void {
    if (this.payingIds.has(item.id) || this.relaunchingIds.has(item.id)) return;

    this.errorMessage = '';
    this.successMessage = '';
    this.payingIds.add(item.id);

    this.historyService.payRequest(item.id).subscribe({
      next: () => {
        this.successMessage = 'Paiement effectué avec succès !';
        this.payingIds.delete(item.id);
        this.loadHistory();
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.errorMessage = err?.error?.error || 'Échec du paiement. Vérifiez votre solde.';
        this.payingIds.delete(item.id);
        this.cdr.detectChanges();
      },
    });
  }

  onHeaderSort(column: 'created_at'): void {
    if (this.sortColumn() === column) {
      this.sortDirection.set(this.sortDirection() === 'asc' ? 'desc' : 'asc');
    } else {
      this.sortColumn.set(column);
      this.sortDirection.set('asc');
    }
    this.applyFilters();
  }

  sortIndicator(column: 'created_at'): string {
    if (this.sortColumn() !== column) return '';
    return this.sortDirection() === 'asc' ? ' ↑' : ' ↓';
  }

  isRelaunching(id: string): boolean {
    return this.relaunchingIds.has(id);
  }

  isPaying(id: string): boolean {
    return this.payingIds.has(id);
  }
}