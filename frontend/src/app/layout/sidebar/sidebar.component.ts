import { Component, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

interface NavItem {
  label: string;
  icon: string;
  route: string;
  children?: NavItem[];
  expanded?: boolean;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.css'
})
export class SidebarComponent {
  isCollapsed = signal(false);

  navGroups: NavGroup[] = [
    {
      title: 'MENU',
      items: [
        { label: 'Tableau de bord', icon: 'dashboard', route: '/dashboard' },
      ]
    },
    {
      title: 'MON COMPTE',
      items: [
        { label: 'Mon profil', icon: 'person', route: '/profile' },
        { label: 'Mes sociétés', icon: 'business', route: '/companies' },
      ]
    },
    {
      title: 'LINKTREE',
      items: [
        { label: 'Mes liens', icon: 'link', route: '/linktree/links' },
      ]
    },
    {
      title: 'TINYURL',
      items: [
        { label: 'Mes URLs', icon: 'short_text', route: '/tinyurl/urls' },
      ]
    }
  ];

  toggleSidebar() {
    this.isCollapsed.update(v => !v);
  }
}
