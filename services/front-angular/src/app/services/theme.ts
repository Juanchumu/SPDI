import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {

  init(): void {
    if (localStorage.getItem('theme') === 'dark') {
      document.body.classList.add('dark-theme');
    }
  }

  toggle(): void {
    const dark = document.body.classList.toggle('dark-theme');

    localStorage.setItem(
      'theme',
      dark ? 'dark' : 'light'
    );
  }

  isDark(): boolean {
    return document.body.classList.contains('dark-theme');
  }
}
