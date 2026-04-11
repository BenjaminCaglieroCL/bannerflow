from django.core.management.base import BaseCommand
from django.db import transaction
from appflow.models import BannerTemplate
import json


class Command(BaseCommand):
    help = 'Convert existing templates to multi-format structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be converted without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        templates = BannerTemplate.objects.all()
        converted_count = 0
        skipped_count = 0
        
        for template in templates:
            # Check if already multi-format
            if self.is_multi_format(template.canvas_data):
                self.stdout.write(f'Skipping {template.name} - already multi-format')
                skipped_count += 1
                continue
                
            # Convert to multi-format
            if not dry_run:
                with transaction.atomic():
                    self.convert_template(template)
            else:
                self.stdout.write(f'Would convert: {template.name}')
                
            converted_count += 1
        
        style = self.style.SUCCESS if not dry_run else self.style.WARNING
        self.stdout.write(
            style(f'Processed {converted_count} templates, skipped {skipped_count}')
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Run without --dry-run to apply changes'))
    
    def is_multi_format(self, canvas_data):
        """Check if canvas_data is already in multi-format structure"""
        if not isinstance(canvas_data, dict):
            return False
        
        # Check for format keys
        format_keys = ['1:1', '4:5', '1.91:1', '9:16']
        return any(key in canvas_data for key in format_keys)
    
    def convert_template(self, template):
        """Convert single canvas_data to multi-format structure"""
        original_data = template.canvas_data or {}
        
        # Create multi-format structure
        multi_format_data = {
            '1:1': self.adapt_canvas_for_format(original_data, '1:1'),
            '4:5': self.adapt_canvas_for_format(original_data, '4:5'), 
            '1.91:1': self.adapt_canvas_for_format(original_data, '1.91:1'),
            '9:16': self.adapt_canvas_for_format(original_data, '9:16')
        }
        
        template.canvas_data = multi_format_data
        template.save()
        
        self.stdout.write(f'Converted: {template.name}')
    
    def adapt_canvas_for_format(self, canvas_data, format_ratio):
        """Adapt canvas data for specific format while preserving relative positions"""
        if not canvas_data:
            return {}
            
        # Format dimensions (display size - 540px base)
        format_dimensions = {
            '1:1': {'width': 540, 'height': 540},      # Square
            '4:5': {'width': 540, 'height': 675},      # Vertical  
            '1.91:1': {'width': 540, 'height': 283},   # Horizontal
            '9:16': {'width': 540, 'height': 960}      # Stories
        }
        
        adapted_data = canvas_data.copy()
        
        # Update canvas dimensions if present
        if format_ratio in format_dimensions:
            dims = format_dimensions[format_ratio]
            adapted_data['width'] = dims['width']
            adapted_data['height'] = dims['height']
        
        # Adapt object positions for different aspect ratios
        if 'objects' in adapted_data:
            adapted_data['objects'] = self.adapt_objects_for_format(
                adapted_data['objects'], format_ratio
            )
        
        return adapted_data
    
    def adapt_objects_for_format(self, objects, format_ratio):
        """Adapt object positions and sizes for different formats"""
        if not objects:
            return []
            
        adapted_objects = []
        
        for obj in objects:
            adapted_obj = obj.copy()
            
            # Preserve object properties but adapt positioning
            # For now, keep same positions - user will fine-tune in editor
            # In future versions, we could implement smart repositioning logic
            
            adapted_objects.append(adapted_obj)
        
        return adapted_objects