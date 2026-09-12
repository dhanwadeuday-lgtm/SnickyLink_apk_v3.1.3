import uuid
from sqlalchemy.orm import Session
from ..models.snick import Snick, SnickPillar

def seed_snicks_pool(db: Session):
    """
    Seeds the snicks pool with some sample data.
    """
    sample_snicks = [
        ("Morning Walk", "Take a 15-minute walk together", "Health", 1, SnickPillar.WELLNESS),
        ("Deep Talk", "Ask each other: What is your biggest dream for us this year?", "Emotion", 2, SnickPillar.CONNECTION),
        ("Random Act", "Do one chore the other person hates", "Service", 1, SnickPillar.IMPACT),
        ("Growth Chat", "Share one thing you learned this week", "Mindset", 1, SnickPillar.GROWTH),
        ("Quick Hug", "Give each other a 30-second hug", "Affection", 1, SnickPillar.CONNECTION),
        ("Gratitude", "Tell your partner 3 things you appreciate about them", "Emotion", 1, SnickPillar.CONNECTION),
        ("Digital Detox", "No phones for 1 hour tonight", "Presence", 2, SnickPillar.WELLNESS),
        ("Future Planning", "Pick a city you both want to visit", "Dreams", 1, SnickPillar.GROWTH),
        ("Compliment", "Compliment your partner's style today", "Affection", 1, SnickPillar.CONNECTION),
        ("Kindness", "Send a supportive text to someone in your shared circle", "Service", 1, SnickPillar.IMPACT),
    ]

    for title, desc, cat, diff, pillar in sample_snicks:
        snick = Snick(
            title=title,
            description=desc,
            category=cat,
            difficulty=diff,
            pillar=pillar
        )
        db.add(snick)

    db.commit()
