import { Routes } from '@angular/router';

//import { MapaSectorizado } from './components/mapa-sectorizado/mapa-sectorizado';
import { Mapa } from './components/mapa/mapa';
import { Error } from './components/error/error';
import { Healt } from './components/healt/healt';

export const routes: Routes = [
  {path: '', component: Mapa},
  {path: 'home', component: Mapa},
  {path: 'healt', component: Healt},
  {path: 'error', component: Error},
  {path: '**' , component: Error}
];






















