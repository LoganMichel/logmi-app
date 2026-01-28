import { Component, inject, OnInit, signal, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { environment } from '../../../environments/environment';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

interface ClickData {
  date: string;
  count: number;
}

interface DashboardStats {
  linktree: {
    total_links: number;
    active_links: number;
    total_clicks: number;
    qrcode_clicks: number;
    clicks_by_day: ClickData[];
  };
  tinyurl: {
    total_urls: number;
    active_urls: number;
    total_clicks: number;
    qrcode_clicks: number;
    clicks_by_day: ClickData[];
  };
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit, AfterViewInit {
  private api = inject(ApiService);
  private authService = inject(AuthService);
  
  linktreeUrl = environment.linktreeUrl;
  tinyurlUrl = environment.linktreeUrl; // Same base URL for short links
  
  get username(): string {
    return this.authService.currentUser?.username || '';
  }

  @ViewChild('linktreeChart') linktreeChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('tinyurlChart') tinyurlChartRef!: ElementRef<HTMLCanvasElement>;

  stats = signal<DashboardStats | null>(null);
  isLoading = signal(true);
  error = signal<string | null>(null);

  private linktreeChart: Chart | null = null;
  private tinyurlChart: Chart | null = null;

  ngOnInit() {
    this.loadStats();
  }

  ngAfterViewInit() {
    // Charts will be created after data loads
  }

  loadStats() {
    this.isLoading.set(true);
    
    // Load both Linktree and TinyURL stats
    Promise.all([
      this.api.get<any>('/linktree/dashboard/').toPromise(),
      this.api.get<any>('/tinyurl/dashboard/').toPromise()
    ]).then(([linktreeData, tinyurlData]) => {
      this.stats.set({
        linktree: {
          total_links: linktreeData?.total_links || 0,
          active_links: linktreeData?.active_links || 0,
          total_clicks: linktreeData?.total_clicks || 0,
          qrcode_clicks: linktreeData?.qrcode_clicks || 0,
          clicks_by_day: linktreeData?.clicks_by_day || [],
        },
        tinyurl: {
          total_urls: tinyurlData?.total_urls || 0,
          active_urls: tinyurlData?.active_urls || 0,
          total_clicks: tinyurlData?.total_clicks || 0,
          qrcode_clicks: tinyurlData?.qrcode_clicks || 0,
          clicks_by_day: tinyurlData?.clicks_by_day || [],
        }
      });
      this.isLoading.set(false);
      
      // Create charts after data is loaded and view is ready
      setTimeout(() => this.createCharts(), 0);
    }).catch(err => {
      this.error.set('Erreur lors du chargement des statistiques');
      this.isLoading.set(false);
    });
  }

  createCharts() {
    const data = this.stats();
    if (!data) return;

    // Create Linktree chart
    if (this.linktreeChartRef?.nativeElement) {
      this.linktreeChart?.destroy();
      this.linktreeChart = this.createLineChart(
        this.linktreeChartRef.nativeElement,
        data.linktree.clicks_by_day,
        'Clics Linktree',
        '#7c3aed'
      );
    }

    // Create TinyURL chart
    if (this.tinyurlChartRef?.nativeElement) {
      this.tinyurlChart?.destroy();
      this.tinyurlChart = this.createLineChart(
        this.tinyurlChartRef.nativeElement,
        data.tinyurl.clicks_by_day,
        'Clics TinyURL',
        '#059669'
      );
    }
  }

  private createLineChart(canvas: HTMLCanvasElement, data: ClickData[], label: string, color: string): Chart {
    const labels = data.map(d => {
      const date = new Date(d.date);
      return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
    });
    const values = data.map(d => d.count);

    return new Chart(canvas, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label,
          data: values,
          borderColor: color,
          backgroundColor: color + '20',
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: color,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: '#1f2937',
            titleColor: '#fff',
            bodyColor: '#fff',
            padding: 12,
            cornerRadius: 8,
            displayColors: false,
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: '#6b7280',
              font: { size: 11 }
            }
          },
          y: {
            beginAtZero: true,
            grid: {
              color: '#e5e7eb'
            },
            ticks: {
              color: '#6b7280',
              font: { size: 11 },
              stepSize: 1
            }
          }
        },
        interaction: {
          intersect: false,
          mode: 'index'
        }
      }
    });
  }
}
