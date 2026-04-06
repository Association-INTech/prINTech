import { Component, inject, OnInit } from '@angular/core';
import { NgOptimizedImage } from '@angular/common';
import { RouterLink } from '@angular/router';
import { HomeService } from '../services/home';

@Component({
  selector: 'app-home',
  imports: [RouterLink, NgOptimizedImage],
  templateUrl: './home.html',
  styleUrl: './home.css',
})
export class Home implements OnInit{
  private readonly homeService = inject(HomeService);

  ngOnInit(): void {
    this.homeService.loadUserInfo();
    this.homeService.getActivePrinters();
  }

  Username = this.homeService.username
  UserCredit = this.homeService.userCredit
  Active_printers = this.homeService.active_printers
  Total_printers = this.homeService.total_printers
  Printer_statuses = this.homeService.printers_status
}
