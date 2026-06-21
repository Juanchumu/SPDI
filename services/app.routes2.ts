import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
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

const routes: Routes = [
  { path: '', component: WelcomeComponent },
  { path: 'login', component: LoginComponent },
  { 
    path: 'dashboard', 
    component: DashboardComponent,
    canActivate: [AuthGuard]
  },
  { 
    path: 'informes-riesgo', 
    component: InformeRiesgoComponent,
    canActivate: [AuthGuard]
  },
  { 
    path: 'informes-cliente', 
    component: InformeClienteComponent,
    canActivate: [AuthGuard]
  },
  { 
    path: 'alta-cliente', 
    component: AltaClienteComponent,
    canActivate: [AuthGuard]
  },
  { 
    path: 'registro-cliente/:id', 
    component: RegistroClienteComponent,
    canActivate: [AuthGuard]
  },
  { 
    path: 'gestion-alertas/:id', 
    component: GestionAlertasComponent,
    canActivate: [AuthGuard]
  },
  { path: '**', redirectTo: '' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
