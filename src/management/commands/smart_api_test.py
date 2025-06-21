"""
Django management command to test Smart API system.
Usage: python manage.py smart_api_test
"""

from django.core.management.base import BaseCommand, CommandError
from smart_api_integrations.examples import run_all_examples


class Command(BaseCommand):
    help = 'Test Smart API integration system with examples'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--provider',
            type=str,
            help='Test specific provider only',
        )
        parser.add_argument(
            '--list-providers',
            action='store_true',
            help='List available providers only',
        )
    
    def handle(self, *args, **options):
        try:
            if options['list_providers']:
                from smart_api_integrations.core.registry import list_providers, get_provider_info
                
                providers = list_providers()
                self.stdout.write(
                    self.style.SUCCESS(f'Found {len(providers)} providers:')
                )
                
                for provider_name in providers:
                    try:
                        provider_info = get_provider_info(provider_name)
                        endpoints = provider_info.get('endpoints', [])
                        self.stdout.write(f'  • {provider_name} ({len(endpoints)} endpoints)')
                        
                        if options['verbosity'] >= 2:
                            for endpoint_name in endpoints:
                                self.stdout.write(f'    - {endpoint_name}')
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'    Error loading {provider_name}: {e}')
                        )
            
            elif options['provider']:
                # Test specific provider
                provider_name = options['provider']
                self.test_provider(provider_name)
            
            else:
                # Run all examples
                self.stdout.write(
                    self.style.SUCCESS('Running Smart API examples...')
                )
                run_all_examples()
        
        except Exception as e:
            raise CommandError(f'Smart API test failed: {e}')
    
    def test_provider(self, provider_name):
        """Test a specific provider."""
        from smart_api_integrations.core.registry import get_client, get_provider_info
        
        try:
            # Check if provider exists
            provider_info = get_provider_info(provider_name)
            endpoints = provider_info.get('endpoints', [])
            self.stdout.write(
                self.style.SUCCESS(f'Testing provider: {provider_name}')
            )
            self.stdout.write(f'Available endpoints: {endpoints}')
            
            # Create client (without auth for basic test)
            client = get_client(provider_name)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Provider {provider_name} loaded successfully')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Provider {provider_name} test failed: {e}')
            ) 