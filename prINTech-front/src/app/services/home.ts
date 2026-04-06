import { HttpClient } from '@angular/common/http';
import { inject, Injectable, signal, } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class HomeService {
  private readonly http = inject(HttpClient)
  private readonly ApiBase = '/api/v1'

  userCredit = signal<number | null>(null);
  active_printers = signal<number>(0);
  total_printers = signal<number>(67);
  username = signal<string>('John Doe');
  printers_status = signal<string>('Disponible')
  email = signal<string>('johndoe@gmail.com')

  getActivePrinters(){
    this.http.get<Printer[]>(`${this.ApiBase}/printers/`)
    .subscribe(
      (res) => {
        this.total_printers.set(res.length)
        const active = res.filter( (stat) => stat.status == "UP").length
        this.active_printers.set(active)
        if (active == res.length){
          this.printers_status.set('Complet')
        } else {
          this.printers_status.set('Disponible')
        }
      }
    )
  }

  loadUserInfo(){
    this.http.get< User >(`${this.ApiBase}/user/me`)
    .subscribe(
      (res) => {
        this.username.set(res.username)
        this.email.set(res.email)
        this.userCredit.set(res.credit)
      }
    )
  }
}

export interface Printer {
  name: string,
  status: string,
}

export interface User {
  id: string,
  username: string,
  email: string,
  credit: number,
}
