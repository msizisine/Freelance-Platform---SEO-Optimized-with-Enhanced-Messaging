from django import template
from django.utils.safestring import mark_safe
from django.templatetags.static import static
import hashlib
import os

register = template.Library()


@register.filter
def webp_image(image_field, size=None, quality=80):
    """Convert image to WebP format with optional resizing"""
    if not image_field:
        return ""
    
    # Get image path
    image_path = image_field.path if hasattr(image_field, 'path') else str(image_field)
    
    # Generate WebP filename
    base_name, ext = os.path.splitext(image_path)
    webp_path = f"{base_name}.webp"
    
    # Add size to filename if specified
    if size:
        webp_path = f"{base_name}_{size}.webp"
    
    # Check if WebP version exists, create if not
    if not os.path.exists(webp_path):
        try:
            from PIL import Image
            
            # Open original image
            img = Image.open(image_path)
            
            # Convert to RGB if necessary (for JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize if specified
            if size:
                width, height = map(int, size.split('x'))
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
            
            # Save as WebP
            img.save(webp_path, 'WEBP', quality=quality, optimize=True)
            
        except Exception:
            # Fallback to original image if WebP conversion fails
            return image_field.url
    
    # Return WebP URL
    webp_url = webp_path.replace(settings.MEDIA_ROOT, '').replace('\\', '/')
    return webp_url


@register.simple_tag
def optimized_image(image_field, alt_text="", size=None, loading="lazy", class_name="", webp=True):
    """Generate optimized image tag with WebP support and lazy loading"""
    if not image_field:
        return mark_safe(f'<img src="{static("images/placeholder.jpg")}" alt="{alt_text}" class="{class_name}" loading="{loading}">')
    
    # Get original image URL
    original_url = image_field.url if hasattr(image_field, 'url') else str(image_field)
    
    # Generate WebP version if requested
    webp_url = ""
    if webp:
        webp_url = webp_image(image_field, size)
    
    # Build image tag
    img_tag = f'<img '
    
    # Use picture element for WebP fallback
    if webp_url:
        img_tag = f'<picture>'
        img_tag += f'<source srcset="{webp_url}" type="image/webp">'
        img_tag += f'<img src="{original_url}" '
    else:
        img_tag = f'<img src="{original_url}" '
    
    # Add attributes
    img_tag += f'alt="{alt_text}" '
    img_tag += f'loading="{loading}" '
    
    if class_name:
        img_tag += f'class="{class_name}" '
    
    if size:
        width, height = map(int, size.split('x'))
        img_tag += f'width="{width}" height="{height}" '
    
    img_tag += '>'
    
    if webp_url:
        img_tag += '</picture>'
    
    return mark_safe(img_tag)


@register.filter
def thumbnail(image_field, size="100x100", crop="center", quality=85):
    """Generate thumbnail with specified size and cropping"""
    if not image_field:
        return ""
    
    # Generate thumbnail filename
    base_name, ext = os.path.splitext(image_field.path)
    thumbnail_path = f"{base_name}_thumb_{size}_{crop}.jpg"
    
    # Check if thumbnail exists, create if not
    if not os.path.exists(thumbnail_path):
        try:
            from PIL import Image
            
            # Open original image
            img = Image.open(image_field.path)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Calculate dimensions
            target_width, target_height = map(int, size.split('x'))
            original_width, original_height = img.size
            
            # Calculate aspect ratios
            target_ratio = target_width / target_height
            original_ratio = original_width / original_height
            
            if crop == "center":
                if original_ratio > target_ratio:
                    # Image is wider than target
                    new_height = target_height
                    new_width = int(new_height * original_ratio)
                else:
                    # Image is taller than target
                    new_width = target_width
                    new_height = int(new_width / original_ratio)
                
                # Resize and crop
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Calculate crop coordinates
                left = (new_width - target_width) // 2
                top = (new_height - target_height) // 2
                right = left + target_width
                bottom = top + target_height
                
                img = img.crop((left, top, right, bottom))
            else:
                # Simple thumbnail without cropping
                img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)
            
        except Exception:
            # Fallback to original image
            return image_field.url
    
    # Return thumbnail URL
    try:
        from django.conf import settings
        thumbnail_url = thumbnail_path.replace(settings.MEDIA_ROOT, '').replace('\\', '/')
    except (ImportError, AttributeError):
        # Fallback for testing
        thumbnail_url = thumbnail_path.replace('\\', '/')
    return thumbnail_url


@register.simple_tag
def responsive_image(image_field, alt_text="", sizes="(max-width: 600px) 100vw, 50vw", class_name=""):
    """Generate responsive image with multiple sizes"""
    if not image_field:
        return mark_safe(f'<img src="{static("images/placeholder.jpg")}" alt="{alt_text}" class="{class_name}" loading="lazy">')
    
    # Define image sizes
    image_sizes = [
        ("320x240", "small"),
        ("640x480", "medium"),
        ("1024x768", "large"),
        ("1920x1080", "xlarge")
    ]
    
    # Generate srcset
    srcset = []
    for size, label in image_sizes:
        thumb_url = thumbnail(image_field, size)
        width = size.split('x')[0]
        srcset.append(f"{thumb_url} {width}w")
    
    # Build picture element
    picture_tag = '<picture>'
    
    # Add WebP sources
    for size, label in image_sizes:
        webp_url = webp_image(image_field, size)
        width = size.split('x')[0]
        picture_tag += f'<source srcset="{webp_url} {width}w" type="image/webp">'
    
    # Add JPEG sources
    picture_tag += f'<source srcset="{", ".join(srcset)}" sizes="{sizes}">'
    
    # Add fallback img
    original_url = image_field.url if hasattr(image_field, 'url') else str(image_field)
    picture_tag += f'<img src="{original_url}" alt="{alt_text}" class="{class_name}" loading="lazy" sizes="{sizes}">'
    
    picture_tag += '</picture>'
    
    return mark_safe(picture_tag)


@register.filter
def image_placeholder(width=300, height=200, text="Loading..."):
    """Generate SVG placeholder image"""
    svg_content = f'''
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#f8f9fa"/>
        <text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="#6c757d" font-family="Arial, sans-serif" font-size="14">
            {text}
        </text>
    </svg>
    '''
    
    # Convert to data URL
    import base64
    svg_bytes = svg_content.encode('utf-8')
    encoded = base64.b64encode(svg_bytes).decode('utf-8')
    data_url = f"data:image/svg+xml;base64,{encoded}"
    
    return data_url


@register.simple_tag
def lazy_image(image_field, alt_text="", size=None, class_name=""):
    """Generate lazy loading image with placeholder"""
    if not image_field:
        placeholder = image_placeholder()
        return mark_safe(f'<img src="{placeholder}" alt="{alt_text}" class="{class_name}" loading="lazy">')
    
    # Get image URL
    image_url = image_field.url if hasattr(image_field, 'url') else str(image_field)
    
    # Generate placeholder
    placeholder = image_placeholder()
    
    # Build lazy loading image
    img_tag = f'''
    <img src="{placeholder}" 
         data-src="{image_url}" 
         alt="{alt_text}" 
         class="{class_name} lazy-image" 
         loading="lazy">
    '''
    
    return mark_safe(img_tag)


@register.simple_tag
def progressive_image(image_field, alt_text="", size=None, class_name=""):
    """Generate progressive loading image (blurry placeholder to full image)"""
    if not image_field:
        return mark_safe(f'<img src="{image_placeholder()}" alt="{alt_text}" class="{class_name}">')
    
    # Generate tiny placeholder (very low quality)
    tiny_url = thumbnail(image_field, "20x20", quality=20)
    
    # Get full image URL
    full_url = image_field.url if hasattr(image_field, 'url') else str(image_field)
    
    # Generate medium quality preview
    medium_url = thumbnail(image_field, size or "400x300", quality=60)
    
    img_tag = f'''
    <div class="progressive-image-container {class_name}">
        <img src="{tiny_url}" 
             data-src="{medium_url}" 
             data-full="{full_url}" 
             alt="{alt_text}" 
             class="progressive-image" 
             loading="lazy">
    </div>
    '''
    
    return mark_safe(img_tag)


@register.simple_tag
def image_alt_text(image_field, fallback=""):
    """Generate appropriate alt text for images"""
    if not image_field:
        return fallback
    
    # Try to get meaningful alt text from image
    if hasattr(image_field, 'title') and image_field.title:
        return image_field.title
    elif hasattr(image_field, 'description') and image_field.description:
        return image_field.description[:100]
    elif hasattr(image_field, 'name') and image_field.name:
        # Remove file extension
        name = os.path.splitext(image_field.name)[0]
        # Replace underscores and hyphens with spaces
        name = name.replace('_', ' ').replace('-', ' ')
        return name.title()
    else:
        return fallback


# CSS for progressive images
PROGRESSIVE_IMAGE_CSS = '''
.progressive-image-container {
    position: relative;
    overflow: hidden;
}

.progressive-image {
    transition: filter 0.3s ease;
    filter: blur(5px);
}

.progressive-image.loaded {
    filter: blur(0);
}

.lazy-image {
    transition: opacity 0.3s ease;
}

.lazy-image.loaded {
    opacity: 1;
}
'''
