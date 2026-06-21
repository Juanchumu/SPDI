import { Routes } from '@angular/router';

//import { MapaSectorizado } from './components/mapa-sectorizado/mapa-sectorizado';
import { Mapa } from './components/mapa/mapa';
import { Error } from './components/error/error';
import { Healt } from './components/healt/healt';
import { Login } from './login/login';
//import { authGuard } from './auth-guard';
import { AuthGuard } from './guards/auth.guard';


// Layout
import { SidebarComponent } from './components/layout/sidebar/sidebar.component';
import { HeaderComponent } from './components/layout/header/header.component';
import { FooterComponent } from './components/layout/footer/footer.component';

// Pages
import { WelcomeComponent } from './components/pages/welcome/welcome.component';
import { LoginComponent } from './components/pages/login/login.component';
import { DashboardComponent } from './components/pages/dashboard/dashboard.component';
import { InformeRiesgoComponent } from './components/pages/informe-riesgo/informe-riesgo.component';
import { InformeClienteComponent } from './components/pages/informe-cliente/informe-cliente.component';
import { AltaClienteComponent } from './components/pages/alta-cliente/alta-cliente.component';
import { RegistroClienteComponent } from './components/pages/registro-cliente/registro-cliente.component';
import { GestionAlertasComponent } from './components/pages/gestion-alertas/gestion-alertas.component';




export const routes: Routes = [
  //{path: 'login', component: Login},
  //{path: 'mapa', component: Mapa, canActivate: [authGuard]},
  //{path: 'healt', component: Healt, canActivate: [authGuard]},
  {path: 'error', component: Error},
  {path: '', redirectTo: 'login', pathMatch: 'full' },
  //{path: '**' , component: Error}
  { path: '', component: WelcomeComponent },
  { path: 'login', component: LoginComponent },
  { path: 'dashboard', component: DashboardComponent,canActivate: [AuthGuard]},
  { path: 'informes-riesgo', component: InformeRiesgoComponent,canActivate: [AuthGuard]},
  { path: 'informes-cliente', component: InformeClienteComponent,canActivate: [AuthGuard]},
  { path: 'alta-cliente', component: AltaClienteComponent,canActivate: [AuthGuard]},
  { path: 'registro-cliente/:id', component: RegistroClienteComponent,canActivate: [AuthGuard]},
  { path: 'gestion-alertas/:id', component: GestionAlertasComponent,canActivate: [AuthGuard]},
  { path: '**', redirectTo: '' }

];




















