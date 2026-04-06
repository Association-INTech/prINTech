import { Component, inject, OnInit } from '@angular/core';
import { NgOptimizedImage } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Greeting } from '../components/greeting/greeting';
import { Counter } from '../components/counter/counter';
import { HomeService } from '../services/home';

@Component({
  selector: 'app-home',
  imports: [Greeting, Counter, RouterLink, NgOptimizedImage],
  templateUrl: './home.html',
  styleUrl: './home.css',
})
export class Home implements OnInit{
  private readonly homeService = inject(HomeService);

  ngOnInit(): void {
    this.homeService.getCredit();
    this.homeService.getActivePrinters();
  }

  UserCredit = this.homeService.userCredit
  Active_printers = this.homeService.active_printers
  Total_printers = this.homeService.total_printers
}
