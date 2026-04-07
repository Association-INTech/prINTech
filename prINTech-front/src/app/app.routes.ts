import { Routes } from '@angular/router';

export const routes: Routes = [{
    path: '',
    pathMatch: 'full',
    loadComponent: () => {
        return import('./home/home').then(m => m.Home)
    }
},
{
    path:'profile',
    loadComponent: () => {
        return import('./profile/profile').then(m => m.Profile)
    }
},
{
    path:'print',
    loadComponent: () => {
        return import('./print/print').then(m => m.Print)
    } 
},
{
    path:'history',
    loadComponent: ()=> {
        return import('./history/history').then(m => m.History)
    }
},
{
    path: 'login',
    loadComponent: () => {
        return import('./login/login').then(m => m.Login)
    }
}];
