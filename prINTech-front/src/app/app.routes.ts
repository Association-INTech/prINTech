import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard/auth.guard';

export const routes: Routes = [{
    path: '',
    pathMatch: 'full',
    loadComponent: () => {
        return import('./home/home').then(m => m.Home)
    },
    canActivate: [authGuard]
},
{
    path:'profile',
    loadComponent: () => {
        return import('./profile/profile').then(m => m.Profile)
    },
    canActivate: [authGuard]
},
{
    path:'print',
    loadComponent: () => {
        return import('./print/print').then(m => m.Print)
    },
    canActivate: [authGuard] 
},
{
    path:'history',
    loadComponent: ()=> {
        return import('./history/history').then(m => m.History)
    },
    canActivate: [authGuard]
},
{
    path: 'login',
    loadComponent: () => {
        return import('./login/login').then(m => m.Login)
    }
}];
