import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ClienteAlta } from './cliente-alta';

describe('ClienteAlta', () => {
  let component: ClienteAlta;
  let fixture: ComponentFixture<ClienteAlta>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ClienteAlta],
    }).compileComponents();

    fixture = TestBed.createComponent(ClienteAlta);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
