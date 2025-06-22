#!/usr/bin/env python3
"""
Basic GitHub API Example using Smart API Integrations

This example demonstrates the core functionality of the smart-api-integrations
package with the GitHub API provider.

Prerequisites:
1. Install the package: pip install smart-api-integrations
2. Set your GitHub token: export GITHUB_TOKEN="your_token_here"
3. Set providers directory: export SMART_API_INTEGRATIONS_PROVIDERS_DIR="./providers"
"""

import os
from smart_api_integrations import GithubAPIClient


def main():
    """Basic GitHub API usage examples."""
    
    # Check if GitHub token is set
    if not os.environ.get('GITHUB_TOKEN'):
        print("❌ Please set your GITHUB_TOKEN environment variable")
        print("   Get a token at: https://github.com/settings/tokens")
        return
    
    print("🚀 Smart API Integrations - GitHub Example")
    print("=" * 50)
    
    # Initialize the GitHub client
    github = GithubAPIClient()
    
    # Example 1: Get authenticated user info
    print("\n1. Getting authenticated user information...")
    user = github.get_authenticated_user()
    
    if user.success:
        print(f"✅ Logged in as: {user.data['login']}")
        print(f"   Name: {user.data.get('name', 'Not set')}")
        print(f"   Public Repos: {user.data['public_repos']}")
    else:
        print(f"❌ Error: {user.error}")
        return
    
    # Example 2: Get a specific user (using direct parameter passing)
    print("\n2. Getting user information for 'octocat'...")
    octocat = github.get_user(username='octocat')
    
    if octocat.success:
        print(f"✅ User: {octocat.data['login']}")
        print(f"   Name: {octocat.data['name']}")
        print(f"   Followers: {octocat.data['followers']}")
        print(f"   Public Repos: {octocat.data['public_repos']}")
    else:
        print(f"❌ Error: {octocat.error}")
    
    # Example 3: Get repository information
    print("\n3. Getting repository information...")
    repo = github.get_repo(owner='octocat', repo='Hello-World')
    
    if repo.success:
        print(f"✅ Repository: {repo.data['full_name']}")
        print(f"   Description: {repo.data['description']}")
        print(f"   Stars: ⭐ {repo.data['stargazers_count']}")
        print(f"   Language: {repo.data['language']}")
    else:
        print(f"❌ Error: {repo.error}")
    
    # Example 4: List your repositories (with pagination)
    print("\n4. Listing your repositories...")
    repos = github.list_repos(params={'per_page': 5, 'sort': 'updated'})
    
    if repos.success:
        print(f"✅ Found {len(repos.data)} recent repositories:")
        for i, repo in enumerate(repos.data, 1):
            print(f"   {i}. {repo['name']} - {repo.get('description', 'No description')}")
    else:
        print(f"❌ Error: {repos.error}")
    
    print("\n🎉 Example completed successfully!")
    print("\nNext steps:")
    print("• Try the CLI: smart-api-integrations add-endpoints github --max-endpoints 5")
    print("• Check the documentation: docs/new_provider_integration_guide.md")
    print("• Add your own API provider following the integration guide")


if __name__ == "__main__":
    main() 