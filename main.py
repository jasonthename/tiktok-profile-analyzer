import requests
from bs4 import BeautifulSoup
import json
import re
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from datetime import datetime
import pytz
import html

def convert_timestamp(timestamp):
    """Convert Unix timestamp to human readable date"""
    dt = datetime.fromtimestamp(timestamp, pytz.UTC)
    return dt.strftime("%B %d, %Y at %I:%M %p UTC")

def decode_text(text):
    """
    Decode text with proper emoji handling
    1. First decode Unicode escape sequences
    2. Then handle HTML entities
    3. Finally handle any remaining UTF-8 encoding
    """
    try:
        # Step 1: Handle Unicode escape sequences
        decoded = text.encode().decode('unicode-escape')
        # Step 2: Handle HTML entities
        decoded = html.unescape(decoded)
        # Step 3: Ensure proper UTF-8 encoding
        decoded = decoded.encode('latin1').decode('utf-8', errors='ignore')
        return decoded
    except Exception:
        # Fallback to basic decoding if the above fails
        return text.encode().decode('unicode-escape', errors='ignore')

def check_tiktok_profile(username):
    """
    Check a TikTok profile and extract public information including avatars
    """
    console = Console()
    
    url = f"https://www.tiktok.com/@{username}?lang=en"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'  # Ensure proper encoding
        
        # Check if profile exists
        if '"followerCount":' not in response.text or '"followingCount":' not in response.text:
            console.print(Panel(
                "[red]Profile not found! ❌[/red]",
                title=f"@{username}",
                border_style="red"
            ))
            return
            
        # Extract all required information using regex
        share_meta_match = re.search(r'"shareMeta":({[^}]+})', response.text)
        signature_match = re.search(r'"signature":"([^"]+)"', response.text)
        create_time_match = re.search(r'"createTime":(\d+)', response.text)
        bio_link_match = re.search(r'"bioLink":\{"link":"([^"]+)"', response.text)
        verified_match = re.search(r'"verified":(true|false)', response.text)
        nickname_match = re.search(r'"nickname":"([^"]+)"', response.text)
        
        # Extract avatar URLs
        avatar_larger_match = re.search(r'"avatarLarger":"([^"]+)"', response.text)
        avatar_medium_match = re.search(r'"avatarMedium":"([^"]+)"', response.text)
        avatar_thumb_match = re.search(r'"avatarThumb":"([^"]+)"', response.text)
        
        content = Text()
        
        # Add Nickname (if different from username)
        if nickname_match:
            nickname = decode_text(nickname_match.group(1))
            if nickname.lower() != username.lower():
                content.append("\n👤 Display Name:\n", style="bold cyan")
                content.append(f"{nickname}\n", style="cyan")
        
        if share_meta_match:
            share_meta = json.loads(share_meta_match.group(1))
            title = decode_text(share_meta.get('title', 'No title available'))
            desc = decode_text(share_meta.get('desc', 'No description available'))
            
            # Parse stats from description
            stats = re.findall(r'(\d+(?:\.\d+)?[kmKM]?) (?:Followers|Following|Likes)', desc)
            
            content.append("\n📊 Stats:\n", style="bold cyan")
            if stats:
                content.append(f"• Followers: ", style="dim")
                content.append(f"{stats[0]}\n", style="green bold")
                content.append(f"• Following: ", style="dim")
                content.append(f"{stats[1]}\n", style="blue bold")
                content.append(f"• Likes: ", style="dim")
                content.append(f"{stats[2]}\n", style="magenta bold")
        
        # Add Bio
        if signature_match:
            bio = decode_text(signature_match.group(1))
            content.append("\n📝 Bio:\n", style="bold yellow")
            content.append(f"{bio}\n", style="yellow")
        
        # Add Bio Link
        if bio_link_match:
            bio_link = decode_text(bio_link_match.group(1))
            content.append("\n🔗 Bio Link:\n", style="bold blue")
            content.append(f"{bio_link}\n", style="blue underline")
        
        # Add Creation Date
        if create_time_match:
            create_time = int(create_time_match.group(1))
            readable_time = convert_timestamp(create_time)
            content.append("\n📅 Profile Created:\n", style="bold green")
            content.append(f"{readable_time}\n", style="green")
        
        # Add Avatar URLs
        content.append("\n🖼️ Profile Pictures:\n", style="bold magenta")
        
        if avatar_larger_match:
            hd_avatar = decode_text(avatar_larger_match.group(1))
            content.append("• HD Quality (1080x1080):\n", style="dim")
            content.append(f"{hd_avatar}\n\n", style="magenta")
            
        if avatar_medium_match:
            medium_avatar = decode_text(avatar_medium_match.group(1))
            content.append("• Medium Quality (720x720):\n", style="dim")
            content.append(f"{medium_avatar}\n\n", style="magenta")
            
        if avatar_thumb_match:
            thumb_avatar = decode_text(avatar_thumb_match.group(1))
            content.append("• Thumbnail (100x100):\n", style="dim")
            content.append(f"{thumb_avatar}\n", style="magenta")
        
        # Add Verification Status
        if verified_match:
            is_verified = verified_match.group(1) == "true"
            content.append("\n✓ Verification Status:\n", style="bold cyan")
            if is_verified:
                content.append("Verified Account ✓\n", style="cyan bold")
            else:
                content.append("Not Verified\n", style="cyan")
            
        # Display in a nice panel
        title_prefix = "✓ " if verified_match and verified_match.group(1) == "true" else ""
        panel_title = f"[bold green]{title_prefix}{decode_text(username)}[/bold green]"
        
        console.print(Panel(
            content,
            title=panel_title,
            subtitle=f"[link={url}]{url}[/link]",
            border_style="green"
        ))
            
    except requests.RequestException as e:
        console.print(Panel(
            f"[red]Error accessing profile: {str(e)}[/red]",
            title="Error",
            border_style="red"
        ))

if __name__ == "__main__":
    console = Console()
    console.print("\n[bold cyan]🎵 TikTok Profile Analyzer 🎵[/bold cyan] [magenta]([/magenta][red]Made with ❤️ by Jason [link=https://twitter.com/j77cyber]@j77cyber[/link][/red][magenta])[/magenta]\n")
    
    while True:
        username = console.input("[yellow]Enter TikTok username (without @) or 'q' to quit:[/yellow] ")
        if username.lower() == 'q':
            break
            
        check_tiktok_profile(username.strip())
        print("\n" + "-"*50 + "\n")

    console.print("\n[cyan]Thanks for using TikTok Profile Analyzer! 👋[/cyan]\n")