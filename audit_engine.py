"""
SEO Audit Engine - Playwright-based data collection
Collects all SEO data in a single browser session for efficiency
"""
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import asyncio
import re
from typing import Dict, List, Any, Optional
from datetime import datetime


class SEOAuditEngine:
    def __init__(self, url: str, timeout: int = 300000):
        self.url = self._normalize_url(url)
        self.timeout = timeout
        self.domain = urlparse(self.url).netloc
        self.results = {}

    def _normalize_url(self, url: str) -> str:
        """Ensure URL has protocol"""
        if not url.startswith(('http://', 'https://')):
            return f'https://{url}'
        return url

    async def run_audit(self) -> Dict[str, Any]:
        """Main audit orchestrator - runs all checks in one session"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            try:
                page = await browser.new_page()
                page.set_default_timeout(self.timeout)

                # Navigate to page
                await page.goto(self.url, wait_until='networkidle', timeout=self.timeout)

                # Run all audits
                self.results = {
                    'url': self.url,
                    'domain': self.domain,
                    'audit_date': datetime.now().isoformat(),
                    'technical': await self._audit_technical(page),
                    'onpage': await self._audit_onpage(page),
                    'performance': await self._audit_performance(page),
                }

                # Auto-detect primary keyword
                primary_keyword = self._detect_primary_keyword()
                self.results['primary_keyword'] = primary_keyword

                # SERP analysis for top 3 competitors
                if primary_keyword:
                    self.results['competitors'] = await self._audit_serp(browser, primary_keyword)

                return self.results

            except Exception as e:
                raise Exception(f"Audit failed: {str(e)}")

            finally:
                await browser.close()

    async def _audit_technical(self, page: Page) -> Dict[str, Any]:
        """Technical SEO checks"""
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')

        # SSL/HTTPS check
        is_https = self.url.startswith('https://')

        # Mobile responsiveness
        viewport = page.viewport_size
        is_mobile_responsive = await self._check_mobile_responsive(page)

        # Robots meta tag
        robots_meta = soup.find('meta', attrs={'name': 'robots'})
        robots_content = robots_meta.get('content', '') if robots_meta else 'index, follow'

        # Canonical tag
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        canonical_url = canonical.get('href', '') if canonical else None

        # Heading structure
        headings = self._analyze_headings(soup)

        # Check for robots.txt
        robots_txt_exists = await self._check_robots_txt(page)

        # Check for XML sitemap
        sitemap_exists = await self._check_sitemap(page)

        # Schema markup detection
        schema_markup = self._detect_schema(soup)

        # Broken links detection (sample check - first 20 links)
        broken_links = await self._check_broken_links(page, soup)

        return {
            'https': is_https,
            'mobile_responsive': is_mobile_responsive,
            'viewport': viewport,
            'robots_meta': robots_content,
            'canonical': canonical_url,
            'headings': headings,
            'robots_txt_exists': robots_txt_exists,
            'sitemap_exists': sitemap_exists,
            'schema_markup': schema_markup,
            'broken_links': broken_links,
        }

    async def _audit_onpage(self, page: Page) -> Dict[str, Any]:
        """On-page SEO checks"""
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')

        # Meta tags
        title_tag = soup.find('title')
        title = title_tag.get_text() if title_tag else ''

        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ''

        # Content analysis
        body_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ''
        word_count = len(body_text.split())

        # Image optimization
        images = soup.find_all('img')
        images_analysis = self._analyze_images(images)

        # Internal links
        internal_links = self._analyze_links(soup, internal=True)

        # External links
        external_links = self._analyze_links(soup, internal=False)

        # URL structure
        url_analysis = self._analyze_url_structure()

        return {
            'title': title,
            'title_length': len(title),
            'meta_description': description,
            'meta_description_length': len(description),
            'word_count': word_count,
            'images': images_analysis,
            'internal_links': internal_links,
            'external_links': external_links,
            'url_structure': url_analysis,
        }

    async def _audit_performance(self, page: Page) -> Dict[str, Any]:
        """Performance metrics"""
        # Get performance metrics
        performance_timing = await page.evaluate("""
            () => {
                const timing = performance.timing;
                const navigation = performance.getEntriesByType('navigation')[0];

                return {
                    loadTime: timing.loadEventEnd - timing.navigationStart,
                    domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                    firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0,
                    transferSize: navigation?.transferSize || 0,
                };
            }
        """)

        # Core Web Vitals approximation
        web_vitals = await page.evaluate("""
            () => {
                return new Promise((resolve) => {
                    let lcp = 0;
                    let fid = 0;
                    let cls = 0;

                    // LCP observer
                    new PerformanceObserver((entryList) => {
                        const entries = entryList.getEntries();
                        lcp = entries[entries.length - 1].startTime;
                    }).observe({type: 'largest-contentful-paint', buffered: true});

                    // CLS observer
                    new PerformanceObserver((entryList) => {
                        for (const entry of entryList.getEntries()) {
                            if (!entry.hadRecentInput) {
                                cls += entry.value;
                            }
                        }
                    }).observe({type: 'layout-shift', buffered: true});

                    setTimeout(() => {
                        resolve({ lcp, fid, cls });
                    }, 2000);
                });
            }
        """)

        return {
            'load_time_ms': performance_timing['loadTime'],
            'dom_content_loaded_ms': performance_timing['domContentLoaded'],
            'first_paint_ms': performance_timing['firstPaint'],
            'transfer_size_bytes': performance_timing['transferSize'],
            'lcp': web_vitals.get('lcp', 0),
            'cls': web_vitals.get('cls', 0),
        }

    async def _audit_serp(self, browser: Browser, keyword: str) -> Dict[str, Any]:
        """Analyze top 3 competitors from Google SERP"""
        try:
            page = await browser.new_page()

            # Search Google
            search_url = f"https://www.google.com/search?q={keyword.replace(' ', '+')}"
            await page.goto(search_url, wait_until='networkidle', timeout=30000)

            # Extract top 10 organic results
            competitors = await page.evaluate("""
                () => {
                    const results = [];
                    const searchResults = document.querySelectorAll('div.g');

                    for (let i = 0; i < Math.min(10, searchResults.length); i++) {
                        const result = searchResults[i];
                        const titleEl = result.querySelector('h3');
                        const linkEl = result.querySelector('a');
                        const descEl = result.querySelector('div[data-sncf]');

                        if (titleEl && linkEl) {
                            results.push({
                                position: i + 1,
                                title: titleEl.innerText,
                                url: linkEl.href,
                                description: descEl ? descEl.innerText : '',
                            });
                        }
                    }

                    return results;
                }
            """)

            await page.close()

            # Analyze top 3 competitors
            top_competitors = []
            for comp in competitors[:3]:
                if comp['url'] != self.url and self.domain not in comp['url']:
                    top_competitors.append({
                        'position': comp['position'],
                        'url': comp['url'],
                        'title': comp['title'],
                        'title_length': len(comp['title']),
                        'description': comp['description'],
                        'description_length': len(comp['description']),
                    })

            # Find current site position
            current_position = None
            for comp in competitors:
                if self.domain in comp['url']:
                    current_position = comp['position']
                    break

            return {
                'keyword': keyword,
                'current_position': current_position,
                'top_competitors': top_competitors[:3],
                'total_results_analyzed': len(competitors),
            }

        except Exception as e:
            return {
                'keyword': keyword,
                'error': str(e),
                'top_competitors': [],
            }

    # Helper methods

    def _analyze_headings(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze heading structure"""
        headings = {}
        for i in range(1, 7):
            h_tags = soup.find_all(f'h{i}')
            headings[f'h{i}'] = [h.get_text(strip=True) for h in h_tags]

        return {
            'structure': headings,
            'h1_count': len(headings.get('h1', [])),
            'h1_text': headings.get('h1', [''])[0] if headings.get('h1') else '',
            'has_proper_hierarchy': len(headings.get('h1', [])) == 1,
        }

    def _analyze_images(self, images: List) -> Dict[str, Any]:
        """Analyze image optimization"""
        total_images = len(images)
        images_with_alt = sum(1 for img in images if img.get('alt'))
        images_without_alt = total_images - images_with_alt

        return {
            'total_images': total_images,
            'images_with_alt': images_with_alt,
            'images_without_alt': images_without_alt,
            'alt_percentage': round(images_with_alt / total_images * 100, 1) if total_images > 0 else 0,
        }

    def _analyze_links(self, soup: BeautifulSoup, internal: bool = True) -> Dict[str, Any]:
        """Analyze internal or external links"""
        links = soup.find_all('a', href=True)
        filtered_links = []

        for link in links:
            href = link.get('href', '')
            is_internal = href.startswith('/') or self.domain in href

            if (internal and is_internal) or (not internal and not is_internal and href.startswith('http')):
                filtered_links.append({
                    'href': href,
                    'text': link.get_text(strip=True)[:50],
                })

        return {
            'count': len(filtered_links),
            'sample': filtered_links[:10],  # First 10 links
        }

    def _analyze_url_structure(self) -> Dict[str, Any]:
        """Analyze URL structure"""
        parsed = urlparse(self.url)
        path = parsed.path

        return {
            'length': len(self.url),
            'has_parameters': bool(parsed.query),
            'path_depth': len([p for p in path.split('/') if p]),
            'uses_hyphens': '-' in path,
            'uses_underscores': '_' in path,
        }

    def _detect_primary_keyword(self) -> Optional[str]:
        """Auto-detect primary keyword from title and H1"""
        title = self.results.get('onpage', {}).get('title', '')
        h1_text = self.results.get('technical', {}).get('headings', {}).get('h1_text', '')

        # Simple heuristic: use H1 if available, otherwise title
        if h1_text:
            # Remove common stop words and get first 3-5 words
            keyword = h1_text.lower().strip()
        elif title:
            keyword = title.lower().strip()
        else:
            return None

        # Clean up keyword
        keyword = re.sub(r'[^\w\s-]', '', keyword)
        words = keyword.split()[:5]  # First 5 words
        return ' '.join(words) if words else None

    async def _check_mobile_responsive(self, page: Page) -> bool:
        """Check if page is mobile responsive"""
        meta_viewport = await page.evaluate("""
            () => {
                const viewport = document.querySelector('meta[name="viewport"]');
                return viewport ? viewport.content : null;
            }
        """)
        return meta_viewport is not None and 'width=device-width' in meta_viewport

    async def _check_robots_txt(self, page: Page) -> bool:
        """Check if robots.txt exists"""
        try:
            robots_url = f"{urlparse(self.url).scheme}://{self.domain}/robots.txt"
            response = await page.goto(robots_url, timeout=10000)
            return response.status == 200
        except:
            return False

    async def _check_sitemap(self, page: Page) -> bool:
        """Check if XML sitemap exists"""
        try:
            sitemap_url = f"{urlparse(self.url).scheme}://{self.domain}/sitemap.xml"
            response = await page.goto(sitemap_url, timeout=10000)
            return response.status == 200
        except:
            return False

    def _detect_schema(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Detect schema markup"""
        schema_scripts = soup.find_all('script', attrs={'type': 'application/ld+json'})

        return {
            'has_schema': len(schema_scripts) > 0,
            'schema_count': len(schema_scripts),
            'schema_types': [self._extract_schema_type(script.string) for script in schema_scripts if script.string],
        }

    def _extract_schema_type(self, schema_json: str) -> str:
        """Extract @type from schema JSON"""
        try:
            import json
            data = json.loads(schema_json)
            return data.get('@type', 'Unknown')
        except:
            return 'Invalid'

    async def _check_broken_links(self, page: Page, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check for broken links (sample of first 20 links)"""
        links = soup.find_all('a', href=True)[:20]
        broken = []

        for link in links:
            href = link.get('href', '')
            if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue

            # Make absolute URL
            absolute_url = urljoin(self.url, href)

            try:
                response = await page.goto(absolute_url, timeout=5000, wait_until='domcontentloaded')
                if response.status >= 400:
                    broken.append({
                        'url': href,
                        'status': response.status,
                    })
            except:
                broken.append({
                    'url': href,
                    'status': 'timeout/error',
                })

        return {
            'checked': len(links),
            'broken_count': len(broken),
            'broken_links': broken,
        }


async def run_seo_audit(url: str) -> Dict[str, Any]:
    """Convenience function to run audit"""
    engine = SEOAuditEngine(url)
    return await engine.run_audit()
