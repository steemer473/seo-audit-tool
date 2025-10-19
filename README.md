# SEO Audit Tool

A comprehensive, automated SEO audit tool that generates professional PDF reports with actionable insights. Built for **Level Play Digital** to capture leads and demonstrate SEO expertise.

## Features

### Free Tier
- ✅ **Technical SEO Analysis**
  - HTTPS/SSL verification
  - Mobile responsiveness check
  - Page speed & Core Web Vitals
  - Schema markup detection
  - Robots.txt & sitemap validation
  - Broken links detection

- ✅ **On-Page SEO Audit**
  - Title tag & meta description analysis
  - Content quality & word count
  - Heading structure (H1-H6)
  - Image optimization & alt text
  - Internal/external linking analysis
  - URL structure evaluation

- ✅ **Competitive Analysis**
  - Auto-detected primary keyword
  - SERP position tracking
  - Top 3 competitor analysis
  - Meta tag comparison

- ✅ **Professional PDF Reports**
  - Branded Level Play Digital design
  - Visual charts & graphs
  - Overall SEO score (0-100)
  - Prioritized recommendations
  - Transparent scoring breakdown

- ✅ **Lead Capture**
  - Go High Level (GHL) webhook integration
  - Email collection
  - 3-day report retention

### Future: Paid Tier
- 🔮 Google Search Console integration
- 🔮 Google Analytics integration
- 🔮 AI-powered content recommendations (Claude API)
- 🔮 Custom keyword tracking
- 🔮 Backlink analysis
- 🔮 Ongoing monitoring & alerts

## Tech Stack

- **Backend:** FastAPI (Python 3.11+)
- **Web Scraping:** Playwright (Chromium)
- **HTML Parsing:** BeautifulSoup4
- **Database:** SQLite with aiosqlite
- **PDF Generation:** WeasyPrint + Jinja2
- **Charts:** Matplotlib
- **Security:** Cryptography (Fernet encryption for OAuth tokens)
- **Deployment:** Render.com

## Project Structure

```
seo-audit-tool/
├── app.py                  # FastAPI application & routes
├── audit_engine.py         # Playwright-based SEO data collection
├── scoring.py              # Transparent scoring algorithm
├── database.py             # SQLite database operations
├── report_generator.py     # PDF report generation
├── requirements.txt        # Python dependencies
├── render.yaml            # Render deployment config
├── .env.example           # Environment variables template
├── templates/
│   ├── form.html          # Landing page form
│   ├── processing.html    # Real-time processing page
│   ├── complete.html      # Report ready page
│   └── report_template.html # PDF report template
├── static/
│   └── logo-dark.svg      # Level Play Digital logo
└── data/
    ├── reports/           # Generated PDF reports
    └── drafts/            # Draft reports
```

## Local Development Setup

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/seo-audit-tool.git
   cd seo-audit-tool
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Run the application**
   ```bash
   python3 app.py
   ```

7. **Visit in browser**
   ```
   http://localhost:8000
   ```

## Environment Variables

Create a `.env` file with the following variables:

```bash
# Required
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
DATABASE_PATH=./data/audit.db
PDF_STORAGE_PATH=./data/reports
DRAFT_STORAGE_PATH=./data/drafts

# Optional: Go High Level Integration
GHL_WEBHOOK_URL=https://your-ghl-webhook-url
GHL_API_KEY=your-ghl-api-key

# Optional: Google OAuth (for paid tier)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Optional: Claude API (for paid tier)
CLAUDE_API_KEY=your-claude-api-key

# Application Settings
MAX_CONCURRENT_AUDITS=10
AUDIT_TIMEOUT_SECONDS=300
REPORT_RETENTION_DAYS=3
BASE_URL=http://localhost:8000
```

## Deployment to Render

### Option 1: Deploy via Render Dashboard

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Create new Web Service on Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`

3. **Configure environment variables in Render**
   - Add `SECRET_KEY`, `GHL_WEBHOOK_URL`, etc.
   - Render will auto-generate `SECRET_KEY` if not provided

4. **Deploy!**
   - Render automatically builds and deploys
   - Your app will be live at `https://your-app-name.onrender.com`

### Option 2: Deploy via Render Blueprint

```bash
# Render will auto-detect render.yaml and configure everything
# Just connect your repo and deploy!
```

### Render Configuration

The `render.yaml` file includes:
- Python 3.11 environment
- Automatic Playwright installation
- Health check endpoint (`/health`)
- Environment variable configuration

**Cost:** Start with free tier, upgrade to Standard ($7/mo) for:
- Persistent disk storage (10GB SSD)
- No spin-down
- Better performance

## API Endpoints

### Public Endpoints

- `GET /` - Landing page with audit form
- `POST /audit/submit` - Submit audit request
- `GET /audit/processing/{uuid}` - Processing page with status
- `GET /audit/status/{uuid}` - AJAX status check
- `GET /audit/complete/{uuid}` - Report ready page
- `GET /audit/download/{uuid}` - Download PDF report
- `GET /health` - Health check (for Render)

## Scoring Algorithm

### Transparent Weighted Scoring (0-100)

- **Technical SEO (40%)**
  - HTTPS: 5 pts
  - Mobile responsive: 10 pts
  - Robots.txt: 5 pts
  - XML sitemap: 5 pts
  - Schema markup: 5 pts
  - Heading structure: 10 pts
  - Canonical tag: 5 pts
  - Page speed: 25 pts (tiered)
  - Core Web Vitals: 15 pts (LCP + CLS)
  - Broken links: 15 pts

- **On-Page SEO (40%)**
  - Title tag: 15 pts (optimal: 30-60 chars)
  - Meta description: 15 pts (optimal: 120-160 chars)
  - Content quality: 20 pts (word count based)
  - Image optimization: 15 pts (alt text coverage)
  - Internal linking: 20 pts
  - URL structure: 15 pts

- **Competitive Analysis (20%)**
  - SERP position: 40 pts
  - Title competitiveness: 30 pts
  - Description competitiveness: 30 pts

### Grade Scale
- A: 90-100
- B: 80-89
- C: 70-79
- D: 60-69
- F: 0-59

## Database Schema

### Reports Table
```sql
CREATE TABLE reports (
    id INTEGER PRIMARY KEY,
    uuid TEXT UNIQUE,
    url TEXT,
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    report_type TEXT,
    status TEXT,
    pdf_path TEXT,
    audit_data TEXT,
    score INTEGER,
    error_message TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP
)
```

### Audit Log Table
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    report_uuid TEXT,
    event_type TEXT,
    message TEXT,
    timestamp TIMESTAMP
)
```

## Security Features

- ✅ HTTPS enforcement (in production)
- ✅ Encrypted OAuth token storage (Fernet)
- ✅ Automatic report expiration (3 days)
- ✅ Rate limiting via semaphore
- ✅ Secure secret key management
- ✅ Input validation & sanitization

## Lead Capture Integration

### Go High Level (GHL) Webhook

When a user submits an audit, their information is sent to GHL:

```json
{
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "website": "https://example.com",
  "reportType": "free",
  "source": "SEO Audit Tool",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Configure `GHL_WEBHOOK_URL` in your `.env` file to enable.

## Customization

### Branding
- Update `static/logo-dark.svg` with your logo
- Modify colors in `report_generator.py` (COLORS dict)
- Customize email copy in `app.py` (send_report_email)

### Scoring Weights
- Edit weights in `scoring.py` (TECHNICAL_WEIGHT, ONPAGE_WEIGHT, etc.)
- Adjust point allocations per metric

### Timeout & Limits
- Modify in `.env`: `AUDIT_TIMEOUT_SECONDS`, `MAX_CONCURRENT_AUDITS`

## Troubleshooting

### Common Issues

**Issue:** Playwright fails to launch browser
**Solution:** Run `playwright install chromium` and ensure system dependencies are installed

**Issue:** PDF generation fails
**Solution:** WeasyPrint requires system libraries. On Ubuntu: `apt-get install libpango-1.0-0 libpangoft2-1.0-0`

**Issue:** Database locked errors
**Solution:** Ensure only one instance is writing at a time. Check `MAX_CONCURRENT_AUDITS`

**Issue:** Reports not expiring
**Solution:** Ensure `periodic_cleanup()` task is running. Check logs.

## Performance Optimization

- Concurrent audit limiting via semaphore
- Async/await throughout for I/O operations
- Single browser session per audit (efficiency)
- Background task processing (non-blocking)
- PDF caching (future enhancement)

## Monitoring & Logs

Application logs include:
- Audit submissions
- Processing stages
- Errors & failures
- GHL webhook status
- Report downloads

Check logs in Render dashboard or local console.

## Future Enhancements

- [ ] Google Search Console integration (OAuth)
- [ ] Google Analytics integration (OAuth)
- [ ] Claude AI content recommendations
- [ ] Email delivery (SMTP/SendGrid)
- [ ] Custom keyword tracking
- [ ] Scheduled re-audits
- [ ] User dashboard
- [ ] White-label options
- [ ] API for programmatic access

## License

Proprietary - Level Play Digital

## Support

For questions or issues:
- Email: hello@levelplaydigital.com
- Website: https://levelplaydigital.com

---

**Built with ❤️ by Level Play Digital**
