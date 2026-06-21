import { Routes } from '@angular/router';

//import { MapaSectorizado } from './components/mapa-sectorizado/mapa-sectorizado';
import { Mapa } from './components/mapa/mapa';
import { Error } from './components/error/error';
import { Healt } from './components/healt/healt';
import { Bienvenida } from './components/bienvenida/bienvenida';
import { MapaUnico } from './components/mapa-unico/mapa-unico';
import { ClienteAlta } from './components/cliente-alta/cliente-alta';
import { InformeRiesgo } from './components/informe-riesgo/informe-riesgo';
import { InformesDeRiesgo } from './components/informes-de-riesgo/informes-de-riesgo';
import { OrdenesTableComponent } from './components/ordenes/ordenes';
import { Login } from './login/login';
import { authGuard } from './auth-guard';

export const routes: Routes = [
  {path: 'login', component: Login},
  {path: 'home', component: Bienvenida},
  {path: 'ordenes', component: OrdenesTableComponent},
  {path: 'mapauni/:id', component: MapaUnico},
  {path: 'cliente-alta', component: ClienteAlta},
  {path: 'informe-riesgo', component: InformeRiesgo},
  {path: 'informes-de-riesgo', component: InformesDeRiesgo},
  {path: 'mapa', component: Mapa, canActivate: [authGuard]},
  {path: 'healt', component: Healt, canActivate: [authGuard]},
  {path: 'error', component: Error},
  {path: '', redirectTo: 'login', pathMatch: 'full' },
  {path: '**' , component: Error}
];






















