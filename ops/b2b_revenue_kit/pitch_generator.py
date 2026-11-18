#!/usr/bin/env python3
"""
MONARCH® B2B Outreach & Pitch Generator
Zero-excuse pitch builder embedding live 3D showreel proof + Client Portal.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PROOF_B2B_URL = "https://drive.google.com/file/d/135l95ZXiJMnVUGI33RYO-cBUC1FeSVgd/view?usp=drivesdk"
PROOF_3D_URL = "https://drive.google.com/file/d/11rA2TXann9own5xforYa1xE5kbGaAdSd/view?usp=drivesdk"
PORTAL_URL = "https://monarch-workspace-beryl.vercel.app/?portal=MON-DEMO26"
PORTFOLIO_URL = "https://adil-chandio.github.io/portfolio/"


def build_pitch(brand: str, founder: str, angle: str, offer: str, lang: str) -> dict:
    if lang == "ur":
        subject = f"{brand} ke liye 3D Commercial Reel + Launch Upgrade — MONARCH®"
        offer_line = {
            "reel": "48–72 hours me 3 high-retention 1080p 3D/AI commercial reels (PKR 45,000)",
            "film": "4–5 days me 60s Flagship 3D Brand Launch Film (PKR 85,000)",
            "bundle": "5–7 days me Custom Dark-Luxury Launch Website + 3D Commercial Reel (PKR 150,000)",
        }[offer]
        body = f"""Assalam-o-Alaikum {founder},

Maine {brand} ki online presence aur content check kiya — {angle}.

Hum MONARCH® Studio me {offer_line} tayyar karte hain. Sabse pehle aapko humare private Client Portal me live watermarked preview milta hai — jab 100% pasand aaye tab SadaPay / Raast / Easypaisa se master files unlock karen:

• B2B 3D Commercial Reel: {PROOF_B2B_URL}
• Custom 3D World Proof: {PROOF_3D_URL}
• Interactive Client Portal: {PORTAL_URL}
• Portfolio: {PORTFOLIO_URL}

Kya main {brand} ke liye 2 short hook concepts bhejun?

Adil Chandio — Founder, MONARCH® Studio
workadilchandio@gmail.com"""
    else:
        subject = f"3D launch upgrade for {brand} — MONARCH® Studio"
        offer_line = {
            "reel": "3 frame-accurate 1080p 3D/kinetic launch reels in 48–72h ($350)",
            "film": "a 60s flagship 3D commercial launch film in 4–5 days ($750)",
            "bundle": "an interactive dark-luxury launch site + 3D launch reel in 5–7 days ($1,500)",
        }[offer]
        body = f"""Hi {founder},

Checked out {brand} — {angle}.

At MONARCH® Studio, we produce {offer_line} (-14 LUFS broadcast mix, real 3D staging, zero stock fluff). You inspect every watermarked cut inside a private Client Portal first and only unlock final masters once approved (Card / Apple Pay / 0%-fee Contra escrow / USDC):

• B2B 3D Launch Commercial: {PROOF_B2B_URL}
• Custom 3D World Proof: {PROOF_3D_URL}
• Live Client Portal Demo: {PORTAL_URL}
• Portfolio Archive: {PORTFOLIO_URL}

Open to me sending over 2 custom hook concepts for {brand} tomorrow?

Best,
Adil Chandio — Founder, MONARCH® Studio
workadilchandio@gmail.com"""
    return {"brand": brand, "founder": founder, "offer": offer, "lang": lang, "subject": subject, "body": body}


def main() -> None:
    p = argparse.ArgumentParser(description="Generate ready-to-send MONARCH® B2B pitches.")
    p.add_argument("--brand", required=True, help="Target company/brand name")
    p.add_argument("--founder", default="Team", help="Founder or contact first name")
    p.add_argument("--angle", default="strong product, though your landing & short-form hooks leave conversions on the table", help="Specific observation/gap")
    p.add_argument("--offer", choices=["reel", "film", "bundle"], default="bundle")
    p.add_argument("--lang", choices=["en", "ur"], default="en")
    p.add_argument("--json", action="store_true", help="Output JSON")
    args = p.parse_args()

    res = build_pitch(args.brand, args.founder, args.angle, args.offer, args.lang)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"SUBJECT: {res['subject']}\n")
        print(res["body"])


if __name__ == "__main__":
    main()
