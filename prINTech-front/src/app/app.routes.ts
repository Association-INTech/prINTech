import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard/auth.guard';
import { adminGuard } from './guards/admin.guard';

export const routes: Routes = [
    {
        path: '',
        pathMatch: 'full',
        loadComponent: () => import('./home/home').then((m) => m.Home),
        canActivate: [authGuard],
    },
    {
        path: 'profile',
        loadComponent: () => import('./profile/profile').then((m) => m.Profile),
        canActivate: [authGuard],
    },
    {
        path: 'print',
        loadComponent: () => import('./print/print').then((m) => m.Print),
        canActivate: [authGuard],
    },
    {
        path: 'history',
        loadComponent: () => import('./history/history').then((m) => m.History),
        canActivate: [authGuard],
    },
    {
        path: 'login',
        loadComponent: () => import('./login/login').then((m) => m.Login),
    },
    {
        path: 'admin/dashboard',
        loadComponent: () => import('./admin-dashboard/admin-dashboard').then((m) => m.AdminDashboard),
        canActivate: [adminGuard],
    },
];
