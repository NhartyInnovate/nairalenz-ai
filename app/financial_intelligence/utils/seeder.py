from decimal import Decimal
import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.financial_intelligence.models.category import Category
from app.financial_intelligence.models.merchant import Merchant
from app.financial_intelligence.models.rule import CategorizationRule

logger = logging.getLogger("db_seeder")

async def seed_data_if_empty(db: AsyncSession) -> None:
    """
    Populates standard financial categories, default merchants with alias configurations,
    and priority categorization rules if the categories metadata table is empty.
    """
    # Check if category table has elements
    query = select(Category)
    result = await db.execute(query)
    if result.scalars().first() is not None:
        logger.info("Database metadata has already been seeded. Skipping.")
        return

    logger.info("Initializing database seed data...")

    # 1. Standard Category Nodes
    # Parent Categories
    living_parent = Category(id=uuid.uuid4(), name="Living Expenses", is_system=True)
    income_parent = Category(id=uuid.uuid4(), name="Income", is_system=True)
    financial_parent = Category(id=uuid.uuid4(), name="Financial", is_system=True)

    db.add_all([living_parent, income_parent, financial_parent])
    await db.flush()

    # Child Categories mapping
    categories_map = {
        "Food & Dining": living_parent.id,
        "Groceries": living_parent.id,
        "Transport": living_parent.id,
        "Fuel": living_parent.id,
        "Bills & Utilities": living_parent.id,
        "Healthcare": living_parent.id,
        "Education": living_parent.id,
        "Shopping": living_parent.id,
        
        "Salary": income_parent.id,
        "Investment": income_parent.id,
        "Transfers": income_parent.id,
        
        "Savings": financial_parent.id,
        "Loan": financial_parent.id,
        "Tax": financial_parent.id,
        "Charity": financial_parent.id,
        "Fees & Charges": financial_parent.id,
        "Entertainment": living_parent.id,
        "Cash Withdrawal": living_parent.id,
        "Uncategorized": None
    }

    db_categories = {}
    for name, parent_id in categories_map.items():
        cat = Category(id=uuid.uuid4(), name=name, parent_id=parent_id, is_system=True)
        db.add(cat)
        db_categories[name] = cat

    await db.flush()

    # 2. Default Merchants Setup
    merchants_data = [
        {
            "canonical_name": "Shoprite",
            "aliases": ["shoprite", "shoprite lekki", "shoprite store", "shoprite nig"],
            "merchant_type": "Groceries",
            "preferred_category": "Groceries"
        },
        {
            "canonical_name": "DSTV",
            "aliases": ["dstv", "dstv payment", "multichoice"],
            "merchant_type": "Entertainment",
            "preferred_category": "Entertainment"
        },
        {
            "canonical_name": "MTN",
            "aliases": ["mtn", "mtn data", "mtn airtime"],
            "merchant_type": "Bills & Utilities",
            "preferred_category": "Bills & Utilities"
        },
        {
            "canonical_name": "Airtel",
            "aliases": ["airtel", "airtel data", "airtel airtime"],
            "merchant_type": "Bills & Utilities",
            "preferred_category": "Bills & Utilities"
        },
        {
            "canonical_name": "Netflix",
            "aliases": ["netflix", "netflix sub"],
            "merchant_type": "Entertainment",
            "preferred_category": "Entertainment"
        },
        {
            "canonical_name": "Uber",
            "aliases": ["uber", "uber ride"],
            "merchant_type": "Transport",
            "preferred_category": "Transport"
        }
    ]

    for m_data in merchants_data:
        pref_cat = db_categories.get(m_data["preferred_category"])
        merchant = Merchant(
            id=uuid.uuid4(),
            canonical_name=m_data["canonical_name"],
            aliases=m_data["aliases"],
            merchant_type=m_data["merchant_type"],
            preferred_category_id=pref_cat.id if pref_cat else None,
            average_transaction_amount=Decimal("0.00"),
            transaction_count=0
        )
        db.add(merchant)

    # 3. Priority Categorization Rules
    rules_data = [
        ("uber", "Transport", 100),
        ("dstv", "Entertainment", 50),
        ("netflix", "Entertainment", 50),
        ("mtn", "Bills & Utilities", 50),
        ("airtel", "Bills & Utilities", 50),
        ("salary", "Salary", 10)
    ]

    for pattern, cat_name, priority in rules_data:
        cat = db_categories.get(cat_name)
        if cat:
            rule = CategorizationRule(
                id=uuid.uuid4(),
                category_id=cat.id,
                pattern=pattern,
                priority=priority,
                confidence=0.95,
                rule_version="1.0"
            )
            db.add(rule)

    await db.commit()
    logger.info("Database metadata seeding successfully finished!")
