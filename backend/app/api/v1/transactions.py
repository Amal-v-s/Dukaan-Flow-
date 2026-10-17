from typing import List, Literal, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.seed_data import seed_service

router = APIRouter(prefix="/api/v1", tags=["Transactions"])


class TransactionDTO(BaseModel):
    id: str
    type: str
    description: str
    category: Optional[str] = None
    amount_paise: int
    date: str
    direction: Literal["inflow", "outflow"]
    payment_method: str = "cash"


class TransactionListResponse(BaseModel):
    items: List[TransactionDTO]
    total_count: int


@router.get("/transactions", response_model=TransactionListResponse)
def list_transactions(direction: Optional[str] = None):
    txs = seed_service.get_transactions()
    items = []
    for t in txs:
        if direction and t["direction"] != direction:
            continue
        items.append(
            TransactionDTO(
                id=t["id"],
                type=t["type"],
                description=t["description"],
                category=t.get("category"),
                amount_paise=t["amount_paise"],
                date=t["date"],
                direction=t["direction"],
                payment_method=t.get("payment_method", "cash"),
            )
        )
    return TransactionListResponse(items=items, total_count=len(items))
