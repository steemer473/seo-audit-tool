"""
SEO Scoring Algorithm
Transparent, weighted scoring system (0-100)
"""
from typing import Dict, Any, List


class SEOScorer:
    """Calculate SEO score based on audit results"""

    # Weight distribution
    TECHNICAL_WEIGHT = 40
    ONPAGE_WEIGHT = 40
    COMPETITIVE_WEIGHT = 20

    def __init__(self, audit_data: Dict[str, Any]):
        self.audit_data = audit_data
        self.breakdown = {}

    def calculate_score(self) -> Dict[str, Any]:
        """Calculate overall SEO score with breakdown"""
        technical_score = self._score_technical()
        onpage_score = self._score_onpage()
        competitive_score = self._score_competitive()

        total_score = round(
            (technical_score * self.TECHNICAL_WEIGHT / 100) +
            (onpage_score * self.ONPAGE_WEIGHT / 100) +
            (competitive_score * self.COMPETITIVE_WEIGHT / 100)
        )

        return {
            'total_score': total_score,
            'grade': self._get_grade(total_score),
            'breakdown': {
                'technical': {
                    'score': technical_score,
                    'weight': self.TECHNICAL_WEIGHT,
                    'details': self.breakdown.get('technical', {}),
                },
                'onpage': {
                    'score': onpage_score,
                    'weight': self.ONPAGE_WEIGHT,
                    'details': self.breakdown.get('onpage', {}),
                },
                'competitive': {
                    'score': competitive_score,
                    'weight': self.COMPETITIVE_WEIGHT,
                    'details': self.breakdown.get('competitive', {}),
                },
            },
            'recommendations': self._generate_recommendations(technical_score, onpage_score, competitive_score),
        }

    def _score_technical(self) -> int:
        """Score Technical SEO (0-100)"""
        technical = self.audit_data.get('technical', {})
        performance = self.audit_data.get('performance', {})

        scores = {}

        # SSL/HTTPS (5 points)
        scores['https'] = 5 if technical.get('https', False) else 0

        # Mobile Responsive (10 points)
        scores['mobile'] = 10 if technical.get('mobile_responsive', False) else 0

        # Robots.txt (5 points)
        scores['robots_txt'] = 5 if technical.get('robots_txt_exists', False) else 0

        # XML Sitemap (5 points)
        scores['sitemap'] = 5 if technical.get('sitemap_exists', False) else 0

        # Schema Markup (5 points)
        schema = technical.get('schema_markup', {})
        scores['schema'] = 5 if schema.get('has_schema', False) else 0

        # Heading Structure (10 points)
        headings = technical.get('headings', {})
        h1_score = 10 if headings.get('has_proper_hierarchy', False) else 5 if headings.get('h1_count', 0) > 0 else 0
        scores['headings'] = h1_score

        # Canonical Tag (5 points)
        scores['canonical'] = 5 if technical.get('canonical') else 0

        # Page Speed (25 points)
        load_time = performance.get('load_time_ms', 10000)
        if load_time < 2000:
            speed_score = 25
        elif load_time < 3000:
            speed_score = 20
        elif load_time < 5000:
            speed_score = 15
        elif load_time < 7000:
            speed_score = 10
        else:
            speed_score = 5
        scores['speed'] = speed_score

        # Core Web Vitals (15 points)
        lcp = performance.get('lcp', 5000)
        cls = performance.get('cls', 1)

        lcp_score = 8 if lcp < 2500 else 5 if lcp < 4000 else 2
        cls_score = 7 if cls < 0.1 else 4 if cls < 0.25 else 1
        scores['lcp'] = lcp_score
        scores['cls'] = cls_score

        # Broken Links (15 points)
        broken = technical.get('broken_links', {})
        broken_count = broken.get('broken_count', 0)
        broken_score = 15 if broken_count == 0 else max(0, 15 - (broken_count * 3))
        scores['broken_links'] = broken_score

        self.breakdown['technical'] = scores
        return sum(scores.values())

    def _score_onpage(self) -> int:
        """Score On-Page SEO (0-100)"""
        onpage = self.audit_data.get('onpage', {})

        scores = {}

        # Title Tag (15 points)
        title = onpage.get('title', '')
        title_length = onpage.get('title_length', 0)

        if 30 <= title_length <= 60:
            title_score = 15
        elif 20 <= title_length <= 70:
            title_score = 10
        elif title_length > 0:
            title_score = 5
        else:
            title_score = 0
        scores['title'] = title_score

        # Meta Description (15 points)
        desc_length = onpage.get('meta_description_length', 0)

        if 120 <= desc_length <= 160:
            desc_score = 15
        elif 100 <= desc_length <= 180:
            desc_score = 10
        elif desc_length > 0:
            desc_score = 5
        else:
            desc_score = 0
        scores['meta_description'] = desc_score

        # Content Quality (20 points)
        word_count = onpage.get('word_count', 0)

        if word_count >= 1500:
            content_score = 20
        elif word_count >= 1000:
            content_score = 16
        elif word_count >= 500:
            content_score = 12
        elif word_count >= 300:
            content_score = 8
        else:
            content_score = 4
        scores['content'] = content_score

        # Image Optimization (15 points)
        images = onpage.get('images', {})
        alt_percentage = images.get('alt_percentage', 0)

        if alt_percentage >= 90:
            image_score = 15
        elif alt_percentage >= 70:
            image_score = 12
        elif alt_percentage >= 50:
            image_score = 8
        elif alt_percentage >= 30:
            image_score = 5
        else:
            image_score = 2
        scores['images'] = image_score

        # Internal Linking (20 points)
        internal_links = onpage.get('internal_links', {}).get('count', 0)

        if internal_links >= 10:
            internal_score = 20
        elif internal_links >= 5:
            internal_score = 15
        elif internal_links >= 3:
            internal_score = 10
        elif internal_links >= 1:
            internal_score = 5
        else:
            internal_score = 0
        scores['internal_links'] = internal_score

        # URL Structure (15 points)
        url_struct = onpage.get('url_structure', {})
        url_length = url_struct.get('length', 100)
        uses_hyphens = url_struct.get('uses_hyphens', False)
        path_depth = url_struct.get('path_depth', 5)

        url_score = 15
        if url_length > 100:
            url_score -= 5
        if not uses_hyphens and path_depth > 0:
            url_score -= 3
        if path_depth > 4:
            url_score -= 4

        scores['url_structure'] = max(0, url_score)

        self.breakdown['onpage'] = scores
        return sum(scores.values())

    def _score_competitive(self) -> int:
        """Score Competitive Position (0-100)"""
        competitors = self.audit_data.get('competitors', {})

        if not competitors or 'error' in competitors:
            # No competitive data available
            return 50  # Neutral score

        scores = {}

        # Current SERP Position (40 points)
        position = competitors.get('current_position')

        if position:
            if position == 1:
                position_score = 40
            elif position <= 3:
                position_score = 35
            elif position <= 5:
                position_score = 30
            elif position <= 10:
                position_score = 20
            else:
                position_score = 10
        else:
            position_score = 5  # Not ranking in top 10

        scores['serp_position'] = position_score

        # Competitive Meta Analysis (60 points)
        top_competitors = competitors.get('top_competitors', [])

        if top_competitors:
            # Compare title length
            avg_comp_title_length = sum(c.get('title_length', 0) for c in top_competitors) / len(top_competitors)
            current_title_length = self.audit_data.get('onpage', {}).get('title_length', 0)

            if 30 <= current_title_length <= 60 and abs(current_title_length - avg_comp_title_length) < 20:
                title_comp_score = 30
            elif current_title_length > 0:
                title_comp_score = 20
            else:
                title_comp_score = 5

            scores['title_competitiveness'] = title_comp_score

            # Compare description length
            avg_comp_desc_length = sum(c.get('description_length', 0) for c in top_competitors) / len(top_competitors)
            current_desc_length = self.audit_data.get('onpage', {}).get('meta_description_length', 0)

            if 120 <= current_desc_length <= 160 and abs(current_desc_length - avg_comp_desc_length) < 30:
                desc_comp_score = 30
            elif current_desc_length > 0:
                desc_comp_score = 20
            else:
                desc_comp_score = 5

            scores['description_competitiveness'] = desc_comp_score
        else:
            scores['title_competitiveness'] = 25
            scores['description_competitiveness'] = 25

        self.breakdown['competitive'] = scores
        return sum(scores.values())

    def _get_grade(self, score: int) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def _generate_recommendations(self, technical_score: int, onpage_score: int, competitive_score: int) -> List[Dict[str, str]]:
        """Generate prioritized recommendations based on scores"""
        recommendations = []

        # Technical recommendations
        technical = self.audit_data.get('technical', {})
        performance = self.audit_data.get('performance', {})

        if not technical.get('https', False):
            recommendations.append({
                'priority': 'critical',
                'category': 'Technical',
                'issue': 'No HTTPS/SSL Certificate',
                'recommendation': 'Install an SSL certificate to enable HTTPS. This is critical for security and SEO.',
            })

        if not technical.get('mobile_responsive', False):
            recommendations.append({
                'priority': 'critical',
                'category': 'Technical',
                'issue': 'Not Mobile Responsive',
                'recommendation': 'Implement responsive design with proper viewport meta tag. Mobile-first indexing requires mobile optimization.',
            })

        if performance.get('load_time_ms', 0) > 3000:
            recommendations.append({
                'priority': 'high',
                'category': 'Performance',
                'issue': f"Slow Page Load ({performance.get('load_time_ms', 0)}ms)",
                'recommendation': 'Optimize images, enable caching, minimize CSS/JS, and use a CDN to improve load times.',
            })

        if not technical.get('sitemap_exists', False):
            recommendations.append({
                'priority': 'high',
                'category': 'Technical',
                'issue': 'No XML Sitemap',
                'recommendation': 'Create and submit an XML sitemap to help search engines discover your pages.',
            })

        # On-page recommendations
        onpage = self.audit_data.get('onpage', {})

        title_length = onpage.get('title_length', 0)
        if title_length == 0:
            recommendations.append({
                'priority': 'critical',
                'category': 'On-Page',
                'issue': 'Missing Title Tag',
                'recommendation': 'Add a unique, descriptive title tag (30-60 characters) to every page.',
            })
        elif title_length < 30 or title_length > 60:
            recommendations.append({
                'priority': 'medium',
                'category': 'On-Page',
                'issue': f"Title Tag Length ({title_length} chars)",
                'recommendation': 'Optimize title tag length to 30-60 characters for better SERP display.',
            })

        desc_length = onpage.get('meta_description_length', 0)
        if desc_length == 0:
            recommendations.append({
                'priority': 'high',
                'category': 'On-Page',
                'issue': 'Missing Meta Description',
                'recommendation': 'Add a compelling meta description (120-160 characters) to improve click-through rates.',
            })

        images = onpage.get('images', {})
        if images.get('images_without_alt', 0) > 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'On-Page',
                'issue': f"{images.get('images_without_alt')} Images Missing Alt Text",
                'recommendation': 'Add descriptive alt text to all images for accessibility and SEO.',
            })

        word_count = onpage.get('word_count', 0)
        if word_count < 300:
            recommendations.append({
                'priority': 'high',
                'category': 'Content',
                'issue': f"Thin Content ({word_count} words)",
                'recommendation': 'Add more high-quality, relevant content. Aim for at least 500-1000 words for better rankings.',
            })

        # Competitive recommendations
        competitors = self.audit_data.get('competitors', {})
        if competitors and not competitors.get('error'):
            position = competitors.get('current_position')
            if not position:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'Competitive',
                    'issue': 'Not Ranking in Top 10',
                    'recommendation': f"Target keyword '{competitors.get('keyword')}' - Analyze top-ranking competitors and improve content quality.",
                })

        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))

        return recommendations[:10]  # Return top 10 recommendations


def calculate_seo_score(audit_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to calculate score"""
    scorer = SEOScorer(audit_data)
    return scorer.calculate_score()
