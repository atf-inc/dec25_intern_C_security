#!/usr/bin/env python3
"""
Data Collection Script for Phishing Detection Evaluation

Collects phishing and benign email samples from various sources:
- PhishTank API (recent phishing samples)
- Kaggle datasets (if available)
- Synthetic samples via Gemini API
- Benign corporate email samples

Usage:
    python collect_data.py --phishing 100 --benign 100
"""

import json
import requests
import asyncio
from typing import List, Dict, Any
from pathlib import Path
import argparse
from datetime import datetime

# Add backend to path for importing services
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

class DataCollector:
    """Collects email samples for evaluation."""
    
    def __init__(self):
        self.datasets_dir = Path(__file__).parent.parent / "datasets"
        self.datasets_dir.mkdir(exist_ok=True)
        
    def collect_phishing_samples(self, count: int = 100) -> List[Dict[str, Any]]:
        """Collect phishing email samples."""
        print(f"🎣 Collecting {count} phishing samples...")
        
        samples = []
        
        # Method 1: PhishTank API (if available)
        try:
            phishtank_samples = self._get_phishtank_samples(count // 2)
            samples.extend(phishtank_samples)
            print(f"✅ Collected {len(phishtank_samples)} from PhishTank")
        except Exception as e:
            print(f"⚠️ PhishTank failed: {e}")
        
        # Method 2: Hardcoded realistic phishing samples
        hardcoded_samples = self._get_hardcoded_phishing_samples()
        samples.extend(hardcoded_samples[:count - len(samples)])
        
        # Method 3: Generate synthetic samples if needed
        remaining = count - len(samples)
        if remaining > 0:
            synthetic_samples = self._generate_synthetic_phishing(remaining)
            samples.extend(synthetic_samples)
        
        print(f"✅ Total phishing samples collected: {len(samples)}")
        return samples[:count]
    
    def collect_benign_samples(self, count: int = 100) -> List[Dict[str, Any]]:
        """Collect benign email samples."""
        print(f"📧 Collecting {count} benign samples...")
        
        samples = []
        
        # Method 1: Hardcoded business emails
        business_samples = self._get_business_email_samples()
        samples.extend(business_samples)
        
        # Method 2: Newsletter/marketing samples
        marketing_samples = self._get_marketing_email_samples()
        samples.extend(marketing_samples)
        
        # Method 3: Generate additional if needed
        remaining = count - len(samples)
        if remaining > 0:
            synthetic_samples = self._generate_synthetic_benign(remaining)
            samples.extend(synthetic_samples)
        
        print(f"✅ Total benign samples collected: {len(samples)}")
        return samples[:count]
    
    def _get_phishtank_samples(self, count: int) -> List[Dict[str, Any]]:
        """Get samples from PhishTank API (placeholder - requires API key)."""
        # Note: PhishTank requires registration for API access
        # For now, return empty list
        return []
    
    def _get_hardcoded_phishing_samples(self) -> List[Dict[str, Any]]:
        """Realistic phishing email samples for testing."""
        return [
            {
                "subject": "Urgent: Your PayPal Account Will Be Suspended",
                "from_email": "security@paypal-verification.com",
                "raw_text": "Dear Customer, We have detected suspicious activity on your PayPal account. Click here to verify your identity immediately or your account will be suspended within 24 hours. Verify Now: http://paypal-secure-login.ru/verify",
                "visible_links": [
                    {"uri": "http://paypal-secure-login.ru/verify", "anchor_text": "Verify Now"}
                ],
                "label": "phishing"
            },
            {
                "subject": "Action Required: Bank of America Security Alert",
                "from_email": "alerts@bankofamerica-security.net",
                "raw_text": "Your account has been temporarily locked due to multiple failed login attempts. Please confirm your identity by clicking the link below. Unlock Account: https://boa-secure.tk/unlock?token=abc123",
                "visible_links": [
                    {"uri": "https://boa-secure.tk/unlock?token=abc123", "anchor_text": "Unlock Account"}
                ],
                "label": "phishing"
            },
            {
                "subject": "Microsoft Account Verification Required",
                "from_email": "no-reply@microsoft-security.org",
                "raw_text": "We noticed a sign-in attempt from an unrecognized device. If this wasn't you, please verify your account immediately. Your account will be disabled in 2 hours if not verified. Verify: http://microsoft-verify.ml/secure",
                "visible_links": [
                    {"uri": "http://microsoft-verify.ml/secure", "anchor_text": "Verify"}
                ],
                "label": "phishing"
            },
            {
                "subject": "Amazon Prime Membership Expired - Renew Now",
                "from_email": "prime@amazon-renewal.co",
                "raw_text": "Your Amazon Prime membership has expired. Renew now to continue enjoying free shipping and exclusive deals. Renew Prime: http://amazon-prime-renewal.tk/renew",
                "visible_links": [
                    {"uri": "http://amazon-prime-renewal.tk/renew", "anchor_text": "Renew Prime"}
                ],
                "label": "phishing"
            },
            {
                "subject": "IRS Tax Refund - Claim Your $2,847 Refund",
                "from_email": "refunds@irs-treasury.gov.fake",
                "raw_text": "The IRS has approved your tax refund of $2,847. Click here to claim your refund before it expires. Claim Refund: http://irs-refund-portal.ml/claim?id=12345",
                "visible_links": [
                    {"uri": "http://irs-refund-portal.ml/claim?id=12345", "anchor_text": "Claim Refund"}
                ],
                "label": "phishing"
            }
        ]
    
    def _get_business_email_samples(self) -> List[Dict[str, Any]]:
        """Legitimate business email samples."""
        return [
            {
                "subject": "Weekly Team Meeting - Thursday 2PM",
                "from_email": "sarah.johnson@company.com",
                "raw_text": "Hi team, Our weekly sync is scheduled for Thursday at 2PM in Conference Room B. Agenda: Q4 planning, budget review, and project updates. Please bring your status reports. Thanks, Sarah",
                "visible_links": [],
                "label": "benign"
            },
            {
                "subject": "Invoice #INV-2024-001234 - Payment Due",
                "from_email": "billing@acmecorp.com",
                "raw_text": "Dear Customer, Please find attached invoice INV-2024-001234 for services rendered in November 2024. Payment is due within 30 days. Contact us with any questions. Best regards, Acme Corp Billing",
                "visible_links": [],
                "label": "benign"
            },
            {
                "subject": "Project Milestone Completed Successfully",
                "from_email": "project.manager@techstartup.io",
                "raw_text": "Great news! The development team has successfully completed Phase 2 of the mobile app project. All features are tested and ready for deployment. Next milestone: user acceptance testing begins Monday.",
                "visible_links": [],
                "label": "benign"
            },
            {
                "subject": "Holiday Schedule - Office Closure Dates",
                "from_email": "hr@company.com",
                "raw_text": "Please note that our offices will be closed December 24-26 and January 1st for the holidays. Emergency contact information is available on the company intranet. Happy holidays! HR Team",
                "visible_links": [],
                "label": "benign"
            },
            {
                "subject": "Quarterly Performance Review Scheduled",
                "from_email": "manager@department.com",
                "raw_text": "Your Q4 performance review is scheduled for next Friday at 3PM. Please prepare your self-assessment and bring examples of key accomplishments. Looking forward to our discussion.",
                "visible_links": [],
                "label": "benign"
            }
        ]
    
    def _get_marketing_email_samples(self) -> List[Dict[str, Any]]:
        """Legitimate marketing/newsletter samples."""
        return [
            {
                "subject": "Your Weekly Newsletter - Tech Industry Updates",
                "from_email": "newsletter@techcrunch.com",
                "raw_text": "This week in tech: AI breakthroughs, startup funding rounds, and industry analysis. Read our top stories and stay informed about the latest developments in technology.",
                "visible_links": [
                    {"uri": "https://techcrunch.com/newsletter", "anchor_text": "Read Full Newsletter"}
                ],
                "label": "benign"
            },
            {
                "subject": "20% Off Your Next Purchase - Limited Time Offer",
                "from_email": "offers@retailstore.com",
                "raw_text": "Exclusive offer for our valued customers! Get 20% off your next purchase with code SAVE20. Valid until end of month. Shop now and save on your favorite items.",
                "visible_links": [
                    {"uri": "https://retailstore.com/shop", "anchor_text": "Shop Now"}
                ],
                "label": "benign"
            }
        ]
    
    def _generate_synthetic_phishing(self, count: int) -> List[Dict[str, Any]]:
        """Generate synthetic phishing samples (placeholder)."""
        # In a real implementation, this would use Gemini API to generate samples
        print(f"📝 Generating {count} synthetic phishing samples...")
        return []
    
    def _generate_synthetic_benign(self, count: int) -> List[Dict[str, Any]]:
        """Generate synthetic benign samples (placeholder)."""
        # In a real implementation, this would use Gemini API to generate samples
        print(f"📝 Generating {count} synthetic benign samples...")
        return []
    
    def save_dataset(self, samples: List[Dict[str, Any]], filename: str):
        """Save samples to JSON file."""
        filepath = self.datasets_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "total_samples": len(samples),
                    "source": "ATF CyberX Data Collector"
                },
                "samples": samples
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {len(samples)} samples to {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Collect email samples for evaluation")
    parser.add_argument("--phishing", type=int, default=50, help="Number of phishing samples")
    parser.add_argument("--benign", type=int, default=50, help="Number of benign samples")
    
    args = parser.parse_args()
    
    collector = DataCollector()
    
    # Collect phishing samples
    phishing_samples = collector.collect_phishing_samples(args.phishing)
    collector.save_dataset(phishing_samples, "phishing_samples.json")
    
    # Collect benign samples
    benign_samples = collector.collect_benign_samples(args.benign)
    collector.save_dataset(benign_samples, "benign_samples.json")
    
    # Create combined dataset
    all_samples = phishing_samples + benign_samples
    collector.save_dataset(all_samples, "combined_dataset.json")
    
    print(f"\n🎉 Dataset collection complete!")
    print(f"📊 Total samples: {len(all_samples)}")
    print(f"🎣 Phishing: {len(phishing_samples)}")
    print(f"📧 Benign: {len(benign_samples)}")

if __name__ == "__main__":
    main()