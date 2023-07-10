import json
import uuid

from api_server.models import GeneratePayment
from api_server.db import UserRepository

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from datetime import datetime

from vkbottle import API

from payments.cloudpayments import CloudPayments, CloudPaymentsApiError
from src.config_reader import PAY_TOKEN, sub_info, api_config

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
        

def validate(must_data: list, json_data: dict):
    for m in must_data:
        if m not in json_data:
            return False
    return True


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
    
    if full_payment_inf.get("SubscriptionId") is not None:
        sub_inf = await cloud_payments.method("subscriptions/get", {"Id": user_inf.sub_id})
        next_date_iso = sub_inf["NextTransactionDateIso"]
        next_date = datetime.fromisoformat(next_date_iso)
        await user_rep.set_exp(next_date)
        return {"code": 0}
    
    json_data_str = full_payment_inf.get("JsonData")

    if user_inf.vip_status:
        return {"code": 0}

    json_data = json.loads(json_data_str)
    
    if not validate(["sub_id", "vk_group_id"], json_data):
        return {"code": 0}

    sub_id = int(json_data["sub_id"])
    group_id = json_data["vk_group_id"]

    date_iso = full_payment_inf.get("ConfirmDateIso")
    date_dt = datetime.fromisoformat(date_iso)
    start_date: datetime = date_dt + sub_info[sub_id]["end"]

    await API(api_config[group_id]).messages.send(
        account_id, random_id=0,
        message="✌ Благодарим за покупку\n"
        f"Теперь вы вип до {start_date.strftime('%d.%m.%Y')}"
    )

    sub_resp = await cloud_payments.method("subscriptions/create", {
        "Token": full_payment_inf.get("Token"),
        "AccountId": account_id,
        "Description": full_payment_inf.get("Description"),
        "Email": full_payment_inf.get("Email"),
        "Amount": sub_info[sub_id]["next"],
        "Currency": full_payment_inf.get("Currency"),
        "RequireConfirmation": False,
        "StartDate": start_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "Interval": sub_info[sub_id]["interval"],
        "Period": sub_info[sub_id]["period"],
    })

    try:
        await user_rep.set_vip(sub_resp["Id"], start_date)
    except Exception as e:
        print(e)
        return {"code": 0}

    return {"code": 0}