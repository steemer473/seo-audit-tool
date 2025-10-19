"""
PDF Report Generator with WeasyPrint
Generates professional SEO audit reports with LPD branding
"""
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
from typing import Dict, Any
import os


class ReportGenerator:
    """Generate PDF reports with Level Play Digital branding"""

    # LPD Brand Colors
    COLORS = {
        'primary_navy': '#1E2E52',
        'accent_orange': '#FF4D26',
        'accent_cyan': '#00B8D9',
        'dark_900': '#0A1220',
        'light_100': '#F5F5F7',
        'light_300': '#D6D6DE',
        'text_dark': '#1C2B4D',
        'background': '#FFFFFF',
        'border': '#E6E6EB',
    }

    def __init__(self, template_dir: str = './templates'):
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate_report(
        self,
        audit_data: Dict[str, Any],
        score_data: Dict[str, Any],
        output_path: str,
        report_type: str = 'free'
    ) -> str:
        """Generate PDF report"""

        # Prepare data for template
        template_data = {
            'audit': audit_data,
            'score': score_data,
            'report_type': report_type,
            'generated_date': datetime.now().strftime('%B %d, %Y'),
            'domain': audit_data.get('domain', ''),
            'url': audit_data.get('url', ''),
            'charts': self._generate_charts(audit_data, score_data),
            'colors': self.COLORS,
        }

        # Render HTML from template
        template = self.env.get_template('report_template.html')
        html_content = template.render(**template_data)

        # Generate PDF with WeasyPrint
        HTML(string=html_content, base_url=self.template_dir).write_pdf(
            output_path,
            stylesheets=[CSS(string=self._get_pdf_styles())]
        )

        return output_path

    def _generate_charts(self, audit_data: Dict[str, Any], score_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate all charts as base64 encoded images"""
        charts = {}

        # Overall score gauge chart
        charts['score_gauge'] = self._create_score_gauge(score_data['total_score'])

        # Breakdown bar chart
        charts['breakdown_bar'] = self._create_breakdown_chart(score_data['breakdown'])

        # Performance metrics chart
        charts['performance'] = self._create_performance_chart(audit_data.get('performance', {}))

        # On-page metrics chart
        charts['onpage_metrics'] = self._create_onpage_chart(audit_data.get('onpage', {}))

        return charts

    def _create_score_gauge(self, score: int) -> str:
        """Create circular gauge chart for overall score"""
        fig, ax = plt.subplots(figsize=(6, 4), subplot_kw=dict(aspect="equal"))

        # Determine color based on score
        if score >= 80:
            color = self.COLORS['accent_cyan']
        elif score >= 60:
            color = self.COLORS['accent_orange']
        else:
            color = '#F24444'  # Red

        # Create donut chart
        sizes = [score, 100 - score]
        colors_list = [color, self.COLORS['light_100']]

        wedges, texts = ax.pie(
            sizes,
            colors=colors_list,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.5, edgecolor='white')
        )

        # Add score text in center
        ax.text(0, 0, f"{score}", ha='center', va='center',
                fontsize=48, fontweight='bold', color=self.COLORS['text_dark'],
                fontfamily='sans-serif')

        ax.text(0, -0.3, "Overall Score", ha='center', va='center',
                fontsize=14, color=self.COLORS['text_dark'],
                fontfamily='sans-serif')

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def _create_breakdown_chart(self, breakdown: Dict[str, Any]) -> str:
        """Create horizontal bar chart for score breakdown"""
        fig, ax = plt.subplots(figsize=(8, 5))

        categories = []
        scores = []
        colors = []

        for category, data in breakdown.items():
            categories.append(category.replace('_', ' ').title())
            score = data['score']
            scores.append(score)

            # Color based on score
            if score >= 80:
                colors.append(self.COLORS['accent_cyan'])
            elif score >= 60:
                colors.append(self.COLORS['accent_orange'])
            else:
                colors.append('#F24444')

        # Create horizontal bars
        y_pos = range(len(categories))
        bars = ax.barh(y_pos, scores, color=colors, edgecolor=self.COLORS['border'], linewidth=1)

        # Add value labels
        for i, (bar, score) in enumerate(zip(bars, scores)):
            ax.text(score + 2, i, f"{score}/100", va='center',
                    fontsize=10, color=self.COLORS['text_dark'],
                    fontfamily='sans-serif')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories, fontsize=11, fontfamily='sans-serif')
        ax.set_xlabel('Score', fontsize=11, fontweight='bold',
                      color=self.COLORS['text_dark'], fontfamily='sans-serif')
        ax.set_xlim(0, 110)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='x', alpha=0.3, linestyle='--')

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def _create_performance_chart(self, performance: Dict[str, Any]) -> str:
        """Create performance metrics bar chart"""
        fig, ax = plt.subplots(figsize=(8, 4))

        metrics = {
            'Load Time': performance.get('load_time_ms', 0) / 1000,  # Convert to seconds
            'DOM Ready': performance.get('dom_content_loaded_ms', 0) / 1000,
            'First Paint': performance.get('first_paint_ms', 0) / 1000,
        }

        categories = list(metrics.keys())
        values = list(metrics.values())

        # Color based on thresholds
        colors = []
        for val in values:
            if val < 2:
                colors.append(self.COLORS['accent_cyan'])
            elif val < 4:
                colors.append(self.COLORS['accent_orange'])
            else:
                colors.append('#F24444')

        bars = ax.bar(categories, values, color=colors, edgecolor=self.COLORS['border'], linewidth=1)

        # Add value labels
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + 0.1,
                    f'{val:.2f}s', ha='center', va='bottom',
                    fontsize=10, color=self.COLORS['text_dark'],
                    fontfamily='sans-serif')

        ax.set_ylabel('Seconds', fontsize=11, fontweight='bold',
                      color=self.COLORS['text_dark'], fontfamily='sans-serif')
        ax.set_title('Performance Metrics', fontsize=13, fontweight='bold',
                     color=self.COLORS['text_dark'], pad=15, fontfamily='sans-serif')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def _create_onpage_chart(self, onpage: Dict[str, Any]) -> str:
        """Create on-page optimization metrics"""
        fig, ax = plt.subplots(figsize=(7, 4))

        metrics = {
            'Title Length': {
                'current': onpage.get('title_length', 0),
                'ideal': 50,
                'max': 70,
            },
            'Meta Desc': {
                'current': onpage.get('meta_description_length', 0),
                'ideal': 140,
                'max': 180,
            },
            'Word Count': {
                'current': min(onpage.get('word_count', 0), 2000),  # Cap at 2000 for visualization
                'ideal': 1000,
                'max': 2000,
            },
        }

        categories = list(metrics.keys())
        current_values = [m['current'] for m in metrics.values()]
        ideal_values = [m['ideal'] for m in metrics.values()]

        x = range(len(categories))
        width = 0.35

        # Current vs Ideal bars
        bars1 = ax.bar([i - width/2 for i in x], current_values, width,
                       label='Current', color=self.COLORS['accent_orange'],
                       edgecolor=self.COLORS['border'], linewidth=1)

        bars2 = ax.bar([i + width/2 for i in x], ideal_values, width,
                       label='Ideal', color=self.COLORS['accent_cyan'],
                       alpha=0.7, edgecolor=self.COLORS['border'], linewidth=1)

        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=10, fontfamily='sans-serif')
        ax.set_ylabel('Value', fontsize=11, fontweight='bold',
                      color=self.COLORS['text_dark'], fontfamily='sans-serif')
        ax.set_title('On-Page Metrics: Current vs Ideal', fontsize=12, fontweight='bold',
                     color=self.COLORS['text_dark'], pad=15, fontfamily='sans-serif')
        ax.legend(fontsize=10, frameon=False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return f"data:image/png;base64,{img_base64}"

    def _get_pdf_styles(self) -> str:
        """Get CSS styles for PDF"""
        return f"""
        @page {{
            size: A4;
            margin: 2cm;
            @bottom-right {{
                content: counter(page) " of " counter(pages);
                font-size: 10px;
                color: {self.COLORS['light_300']};
            }}
        }}

        body {{
            font-family: 'Inter', 'Helvetica', 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: {self.COLORS['text_dark']};
        }}

        h1, h2, h3, h4 {{
            font-family: 'Poppins', 'Helvetica', 'Arial', sans-serif;
            color: {self.COLORS['primary_navy']};
            font-weight: 700;
        }}

        h1 {{
            font-size: 28pt;
            margin-bottom: 10pt;
            border-bottom: 3px solid {self.COLORS['accent_orange']};
            padding-bottom: 10pt;
        }}

        h2 {{
            font-size: 20pt;
            margin-top: 20pt;
            margin-bottom: 12pt;
            color: {self.COLORS['primary_navy']};
        }}

        h3 {{
            font-size: 16pt;
            margin-top: 15pt;
            margin-bottom: 8pt;
        }}

        .cover-page {{
            text-align: center;
            padding-top: 100pt;
        }}

        .cover-logo {{
            width: 180px;
            margin-bottom: 30pt;
        }}

        .cover-title {{
            font-size: 36pt;
            font-weight: 800;
            background: linear-gradient(135deg, {self.COLORS['accent_orange']}, {self.COLORS['accent_cyan']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 15pt;
        }}

        .cover-domain {{
            font-size: 18pt;
            color: {self.COLORS['text_dark']};
            margin-bottom: 30pt;
        }}

        .score-badge {{
            display: inline-block;
            background: {self.COLORS['light_100']};
            border: 3px solid {self.COLORS['accent_orange']};
            border-radius: 50%;
            width: 120pt;
            height: 120pt;
            line-height: 120pt;
            font-size: 48pt;
            font-weight: 800;
            color: {self.COLORS['accent_orange']};
            margin: 20pt auto;
        }}

        .metric-box {{
            background: {self.COLORS['light_100']};
            border-left: 4px solid {self.COLORS['accent_cyan']};
            padding: 12pt;
            margin: 10pt 0;
        }}

        .recommendation {{
            background: white;
            border: 1px solid {self.COLORS['border']};
            border-radius: 6pt;
            padding: 12pt;
            margin: 10pt 0;
            page-break-inside: avoid;
        }}

        .recommendation.critical {{
            border-left: 4px solid #F24444;
        }}

        .recommendation.high {{
            border-left: 4px solid {self.COLORS['accent_orange']};
        }}

        .recommendation.medium {{
            border-left: 4px solid {self.COLORS['accent_cyan']};
        }}

        .priority-badge {{
            display: inline-block;
            padding: 4pt 10pt;
            border-radius: 4pt;
            font-size: 9pt;
            font-weight: 700;
            text-transform: uppercase;
            color: white;
        }}

        .priority-critical {{
            background: #F24444;
        }}

        .priority-high {{
            background: {self.COLORS['accent_orange']};
        }}

        .priority-medium {{
            background: {self.COLORS['accent_cyan']};
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15pt 0;
        }}

        th {{
            background: {self.COLORS['primary_navy']};
            color: white;
            padding: 10pt;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 8pt 10pt;
            border-bottom: 1px solid {self.COLORS['border']};
        }}

        tr:nth-child(even) {{
            background: {self.COLORS['light_100']};
        }}

        .chart-container {{
            text-align: center;
            margin: 20pt 0;
            page-break-inside: avoid;
        }}

        .chart-container img {{
            max-width: 100%;
            height: auto;
        }}

        .footer {{
            text-align: center;
            font-size: 9pt;
            color: {self.COLORS['light_300']};
            margin-top: 30pt;
            padding-top: 15pt;
            border-top: 1px solid {self.COLORS['border']};
        }}

        .gradient-text {{
            background: linear-gradient(135deg, {self.COLORS['accent_orange']}, {self.COLORS['accent_cyan']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
        }}

        code {{
            background: {self.COLORS['light_100']};
            padding: 2pt 6pt;
            border-radius: 3pt;
            font-family: 'Roboto Mono', 'Courier', monospace;
            font-size: 9pt;
        }}
        """


def generate_pdf_report(
    audit_data: Dict[str, Any],
    score_data: Dict[str, Any],
    output_path: str,
    report_type: str = 'free',
    template_dir: str = './templates'
) -> str:
    """Convenience function to generate PDF report"""
    generator = ReportGenerator(template_dir)
    return generator.generate_report(audit_data, score_data, output_path, report_type)
