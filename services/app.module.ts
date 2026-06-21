import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

// Layout Components
import { SidebarComponent } from './components/layout/sidebar/sidebar.component';
import { HeaderComponent } from './components/layout/header/header.component';
import { FooterComponent } from './components/layout/footer/footer.component';

// Page Components
import { WelcomeComponent } from './components/pages/welcome/welcome.component';
import { LoginComponent } from './components/pages/login/login.component';
import { DashboardComponent } from './components/pages/dashboard/dashboard.component';
import { InformeRiesgoComponent } from './components/pages/informe-riesgo/informe-riesgo.component';
import { InformeClienteComponent } from './components/pages/informe-cliente/informe-cliente.component';
import { AltaClienteComponent } from './components/pages/alta-cliente/alta-cliente.component';
import { RegistroClienteComponent } from './components/pages/registro-cliente/registro-cliente.component';
import { GestionAlertasComponent } from './components/pages/gestion-alertas/gestion-alertas.component';

// Services
import { AuthService } from './services/auth.service';
import { OrdenService } from './services/orden.service';
import { InformeService } from './services/informe.service';
import { ClienteService } from './services/cliente.service';

@NgModule({
  declarations: [
    AppComponent,
    SidebarComponent,
    HeaderComponent,
    FooterComponent,
    WelcomeComponent,
    LoginComponent,
    DashboardComponent,
    InformeRiesgoComponent,
    InformeClienteComponent,
    AltaClienteComponent,
    RegistroClienteComponent,
    GestionAlertasComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    FormsModule,
    ReactiveFormsModule,
    HttpClientModule
  ],
  providers: [
    AuthService,
    OrdenService,
    InformeService,
    ClienteService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
