from pydantic import BaseModel


class GeneratePayment(BaseModel):
    amount: int
    description: str
    user_id: str
    confiramtion: bool
    sub_id: int
