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

  getCredit(){
    this.http.get<{ credit: number }>(`${this.ApiBase}/user/me/`) 
    .subscribe(
      (res) => {this.userCredit.set(res.credit)} 
    )
  }

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

  getEmail(){
    this.http.get<{ email: string }>(`${this.ApiBase}/user/me`)
    .subscribe(
      (res) => {this.email.set(res.email)}
    )
  }

  getUsername(){
    this.http.get<{ username: string }>(`${this.ApiBase}/user/me`)
    .subscribe(
      (res) => {this.username.set(res.username)}
    )
  }
}

export interface Printer {
  name: string,
  status: string,
}
