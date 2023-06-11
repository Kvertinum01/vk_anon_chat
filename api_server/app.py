import json

from fastapi import FastAPI, Request
from datetime import datetime

from src.chat_manager.cloudpayments import CloudPayments, CloudPaymentsApiError
from src.repositories.user import UserRepository
from src.config_reader import PAY_TOKEN, sub_info


app = FastAPI()
cloud_payments = CloudPayments(PAY_TOKEN)


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
    
    payment_token = full_payment_inf.get("Token")
    account_id = full_payment_inf.get("AccountId")

    json_data_str = full_payment_inf.get("JsonData")
    json_data = json.loads(json_data_str)
    sub_id = int(json_data["sub_id"])

    date_iso = full_payment_inf.get("ConfirmDateIso")
    date_dt = datetime.fromisoformat(date_iso)
    start_date: datetime = date_dt + sub_info[sub_id]["end"]

    sub_resp = await cloud_payments.method("subscriptions/create", {
        "Token": payment_token,
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

    user_rep = UserRepository(account_id)
    await user_rep.set_vip(sub_resp["Id"])

    return {"code": 0}