import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AltaUsuario } from './alta-usuario';

describe('AltaUsuario', () => {
  let component: AltaUsuario;
  let fixture: ComponentFixture<AltaUsuario>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AltaUsuario],
    }).compileComponents();

    fixture = TestBed.createComponent(AltaUsuario);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
