import json
import uuid

from api_server.models import GeneratePayment

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from datetime import datetime

from src.chat_manager.cloudpayments import CloudPayments, CloudPaymentsApiError
from src.models.db import session
from src.repositories.user import UserRepository
from src.config_reader import PAY_TOKEN, sub_info

from typing import Dict


app = FastAPI(docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

cloud_payments = CloudPayments(PAY_TOKEN)

payment_ids: Dict[str, GeneratePayment] = {}


@app.on_event("shutdown")
async def on_shutdown():
    await session.close()


@app.post("/get_payment/{payment_id}")
async def generate_payment(payment_id: str):
    if payment_id not in payment_ids:
        return {
            "status": "error",
            "message": "payment not found",
            "response": {},
        }
    
    payment_inf = payment_ids[payment_id].copy()
    
    user_inf = await UserRepository(payment_inf.user_id).get()

    if user_inf.vip_status:
        return {
            "status": "error",
            "message": "user already have vip status",
            "response": {},
        }
    
    return {
        "status": "success",
        "message": "",
        "response": payment_inf.json(),
    }


@app.post("/generate-url")
async def generate_url(payment_model: GeneratePayment):
    user_rep = UserRepository(payment_model.user_id)
    reg_status = await user_rep.check_reg()

    if not reg_status:
        return {
            "status": "error",
            "message": "user not found",
            "response": {},
        }

    payment_id = str(uuid.uuid4())
    payment_ids[payment_id] = payment_model

    return {
        "status": "success",
        "message": "",
        "response": {"payment_id": payment_id},
    }


@app.post("/fix-payment")
async def fix_payment(payment_model: Request):
    form_data = await payment_model.form()

    transaction_id = form_data.get("TransactionId")
    status = form_data.get("Status")

    if status != "Completed":
        return {"code": 0}
    
    await cloud_payments.setup()

    try:
        full_payment_inf = await cloud_payments.method("payments/get", {"TransactionId": transaction_id})
    except CloudPaymentsApiError:
        return {"code": 0}
    
    account_id = full_payment_inf.get("AccountId")
    
    user_rep = UserRepository(account_id)
    user_inf = await user_rep.get()

    if user_inf.vip_status:
        return {"code": 0}

    json_data_str = full_payment_inf.get("JsonData")
    json_data = json.loads(json_data_str)
    sub_id = int(json_data["sub_id"])

    date_iso = full_payment_inf.get("ConfirmDateIso")
    date_dt = datetime.fromisoformat(date_iso)
    start_date: datetime = date_dt + sub_info[sub_id]["end"]

    sub_resp = await cloud_payments.method("subscriptions/create", {
        "Token": full_payment_inf.get("Token"),
        "AccountId": account_id,
        "Description": full_payment_inf.get("Description"),
        "Email": full_payment_inf.get("Email"),
        "Amount": full_payment_inf.get("Amount"),
        "Currency": full_payment_inf.get("Currency"),
        "RequireConfirmation": False,
        "StartDate": start_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "Interval": sub_info[sub_id]["interval"],
        "Period": sub_info[sub_id]["period"],
    })

    await user_rep.set_vip(sub_resp["Id"])

    return {"code": 0}