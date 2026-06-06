import { Component, inject, OnInit } from '@angular/core';
import { HomeService } from '../../../services/home';

@Component({
  selector: 'app-metric-card',
  imports: [],
  templateUrl: './metric-card.html',
  styleUrl: './metric-card.css',
})
export class MetricCard implements OnInit {
  private readonly homeService = inject(HomeService)
  ngOnInit(): void {
    this.homeService.loadUserInfo();
    this.homeService.getActivePrinters();
    this.homeService.GetQueue();
  }

  UserCredit = this.homeService.userCredit
  Active_printers = this.homeService.active_printers
  Total_printers = this.homeService.total_printers
  Printer_statuses = this.homeService.printers_status
  Queue_size = this.homeService.queue_size
  is_active = this.homeService.is_active

}
