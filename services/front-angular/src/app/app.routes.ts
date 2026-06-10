import { Routes } from '@angular/router';

//import { MapaSectorizado } from './components/mapa-sectorizado/mapa-sectorizado';
import { Mapa } from './components/mapa/mapa';
import { Error } from './components/error/error';
import { Healt } from './components/healt/healt';
import { Login } from './login/login';
import { authGuard } from './auth-guard';

export const routes: Routes = [
  {path: 'login', component: Login},
  {path: 'mapa', component: Mapa, canActivate: [authGuard]},
  {path: 'healt', component: Healt, canActivate: [authGuard]},
  {path: 'error', component: Error},
  {path: '', redirectTo: 'login', pathMatch: 'full' },
  {path: '**' , component: Error}
];






















