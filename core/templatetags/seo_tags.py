from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()


@register.simple_tag
def structured_data_provider(provider, base_url):
    """Generate Schema.org structured data for a service provider"""
    profile = getattr(provider, 'provider_profile', None)
    
    data = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": provider.get_full_name() or provider.email,
        "description": getattr(profile, 'bio', '') or f"Professional {provider.get_user_type_display()}",
        "url": f"{base_url}/users/profile/{provider.id}/",
        "telephone": getattr(profile, 'phone', ''),
        "email": provider.email,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": getattr(profile, 'location', ''),
            "addressCountry": "ZA"
        } if profile and profile.location else None,
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": float(profile.latitude) if profile and profile.latitude else None,
            "longitude": float(profile.longitude) if profile and profile.longitude else None
        } if profile and profile.latitude and profile.longitude else None,
        "priceRange": f"R{getattr(profile, 'daily_rate', 0)}" if profile and profile.daily_rate else None,
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": float(profile.average_rating) if profile and profile.average_rating else 0,
            "reviewCount": profile.review_count if profile else 0,
            "bestRating": 5,
            "worstRating": 1
        } if profile and profile.average_rating and profile.review_count > 0 else None,
        "areaServed": getattr(profile, 'service_areas', []) if profile else [],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Services",
            "itemListElement": []
        }
    }
    
    # Add services from gigs
    if hasattr(provider, 'gig_set'):
        services = []
        for gig in provider.gig_set.filter(is_active=True)[:5]:  # Limit to 5 services
            services.append({
                "@type": "Offer",
                "itemOffered": {
                    "@type": "Service",
                    "name": gig.title,
                    "description": gig.description[:200] + "..." if len(gig.description) > 200 else gig.description,
                    "category": gig.category.name if gig.category else ""
                },
                "price": f"R{gig.basic_price}" if gig.basic_price else None,
                "priceCurrency": "ZAR",
                "availability": "https://schema.org/InStock"
            })
        data["hasOfferCatalog"]["itemListElement"] = services
    
    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(data, indent=2)}</script>')


@register.simple_tag
def structured_data_gig(gig, base_url):
    """Generate Schema.org structured data for a gig/service"""
    data = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": gig.title,
        "description": gig.description[:200] + "..." if len(gig.description) > 200 else gig.description,
        "url": f"{base_url}/gigs/{gig.id}/",
        "provider": {
            "@type": "Person",
            "name": gig.user.get_full_name() or gig.user.email,
            "url": f"{base_url}/users/profile/{gig.user.id}/"
        },
        "category": gig.category.name if gig.category else "",
        "offers": {
            "@type": "Offer",
            "price": f"R{gig.basic_price}" if gig.basic_price else None,
            "priceCurrency": "ZAR",
            "availability": "https://schema.org/InStock",
            "seller": {
                "@type": "Person",
                "name": gig.user.get_full_name() or gig.user.email
            }
        } if gig.basic_price else None,
        "areaServed": gig.location or "",
        "image": gig.image.url if gig.image else None,
        "datePosted": gig.created_at.isoformat(),
        "dateModified": gig.updated_at.isoformat()
    }
    
    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(data, indent=2)}</script>')


@register.simple_tag
def structured_data_review(review, base_url):
    """Generate Schema.org structured data for a review"""
    data = {
        "@context": "https://schema.org",
        "@type": "Review",
        "itemReviewed": {
            "@type": "Person",
            "name": review.service_provider.get_full_name() or review.service_provider.email,
            "url": f"{base_url}/users/profile/{review.service_provider.id}/"
        },
        "reviewRating": {
            "@type": "Rating",
            "ratingValue": review.rating,
            "bestRating": 5,
            "worstRating": 1
        },
        "author": {
            "@type": "Person",
            "name": review.homeowner.get_full_name() or review.homeowner.email
        },
        "reviewBody": review.comment or "",
        "datePublished": review.created_at.isoformat()
    }
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(data, indent=2)}</script>')


@register.simple_tag
def structured_data_search_results(query, results, base_url):
    """Generate Schema.org structured data for search results page"""
    items = []
    
    for result in results[:10]:  # Limit to 10 results
        if hasattr(result, 'user_type') and result.user_type == 'service_provider':
            items.append({
                "@type": "ListItem",
                "position": len(items) + 1,
                "item": {
                    "@type": "Person",
                    "name": result.get_full_name() or result.email,
                    "url": f"{base_url}/users/profile/{result.id}/",
                    "description": getattr(result.provider_profile, 'bio', '') or f"Professional {result.get_user_type_display()}"
                }
            })
    
    data = {
        "@context": "https://schema.org",
        "@type": "SearchResultsPage",
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(items),
            "itemListElement": items
        },
        "query": query or "All providers"
    }
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(data, indent=2)}</script>')


@register.simple_tag
def structured_data_breadcrumb(breadcrumbs):
    """Generate Schema.org structured data for breadcrumbs"""
    items = []
    
    for i, (name, url) in enumerate(breadcrumbs):
        items.append({
            "@type": "ListItem",
            "position": i + 1,
            "name": name,
            "item": url
        })
    
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items
    }
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(data, indent=2)}</script>')


@register.simple_tag
def structured_data_organization(base_url):
    """Generate Schema.org structured data for the organization"""
    data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "pro4me",
        "url": base_url,
        "logo": f"{base_url}/static/images/logo.png",
        "description": "Connect with trusted local service providers for home improvement, repairs, and maintenance in South Africa",
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "ZA",
            "addressRegion": "Gauteng"
        },
        "contactPoint": {
            "@type": "ContactPoint",
            "telephone": "+27-123-456-789",
            "contactType": "customer service",
            "availableLanguage": ["English"]
        },
        "sameAs": [
            # Add social media URLs here
        ]
    }
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(data, indent=2)}</script>')


@register.simple_tag
def structured_data_website(base_url):
    """Generate Schema.org structured data for the website"""
    data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "pro4me",
        "url": base_url,
        "description": "Find trusted local service providers for home improvement, repairs, and maintenance in South Africa",
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{base_url}/search/?q={{search_term}}"
            },
            "query-input": "required name=search_term"
        }
    }
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(data, indent=2)}</script>')


@register.simple_tag
def structured_data_faq(faqs):
    """Generate Schema.org structured data for FAQ section"""
    items = []
    
    for faq in faqs:
        items.append({
            "@type": "Question",
            "name": faq['question'],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": faq['answer']
            }
        })
    
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": items
    }
    
    return mark_safe(f'<script type="application/ld+json">{json.dumps(data, indent=2)}</script>')


@register.simple_tag
def meta_tags_seo(title, description, keywords="", image="", canonical_url=""):
    """Generate comprehensive SEO meta tags"""
    tags = []
    
    # Basic meta tags
    if title:
        tags.append(f'<title>{title}</title>')
        tags.append(f'<meta property="og:title" content="{title}">')
        tags.append(f'<meta name="twitter:title" content="{title}">')
    
    if description:
        tags.append(f'<meta name="description" content="{description}">')
        tags.append(f'<meta property="og:description" content="{description}">')
        tags.append(f'<meta name="twitter:description" content="{description}">')
    
    if keywords:
        tags.append(f'<meta name="keywords" content="{keywords}">')
    
    if canonical_url:
        tags.append(f'<link rel="canonical" href="{canonical_url}">')
        tags.append(f'<meta property="og:url" content="{canonical_url}">')
    
    if image:
        tags.append(f'<meta property="og:image" content="{image}">')
        tags.append(f'<meta name="twitter:image" content="{image}">')
    
    # Twitter Card
    tags.append('<meta name="twitter:card" content="summary_large_image">')
    
    # Open Graph
    tags.append('<meta property="og:type" content="website">')
    tags.append('<meta property="og:site_name" content="pro4me">')
    tags.append('<meta property="og:locale" content="en_ZA">')
    
    # Additional SEO tags
    tags.append('<meta name="robots" content="index, follow">')
    tags.append('<meta name="googlebot" content="index, follow">')
    tags.append('<meta name="author" content="pro4me">')
    
    return mark_safe('\n'.join(tags))
