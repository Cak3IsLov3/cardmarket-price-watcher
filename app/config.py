import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pricewatcher.db")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
PRICE_GUIDE_URL = os.getenv(
    "PRICE_GUIDE_URL",
    "https://downloads.s3.cardmarket.com/productCatalog/priceGuide/price_guide_1.json",
)
SCRYFALL_USER_AGENT = os.getenv("SCRYFALL_USER_AGENT", "CardmarketPriceWatcher/0.1")
CARDMARKET_PRODUCT_URL = "https://www.cardmarket.com/en/Magic/Products?idProduct={id}"