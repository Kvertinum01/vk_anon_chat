from vkbottle import LoopWrapper

from typing import List

from src.config_reader import PAY_TOKEN
from src.chat_manager.cloudpayments import CloudPayments
from src.models.user_model import User
from src.models.db import session

from sqlalchemy import select, update, and_


cloud_payments = CloudPayments(PAY_TOKEN)
lw = LoopWrapper()


async def on_shutdown():
    await session.close()


lw.on_shutdown.append(on_shutdown())


@lw.interval(minutes=5)
async def check_vip():
    all_with_vip_ex = await session.execute(
        select(User)
        .where(and_(User.vip_status == True, User.platform == "vk"))
    )

    all_with_vip: List[User] = [curr_user[0] for curr_user in all_with_vip_ex.fetchall()]
    
    if not all_with_vip:
        return
    
    await cloud_payments.setup()
    
    for user_inf in all_with_vip:
        sub_inf = await cloud_payments.method("subscriptions/get", {"Id": user_inf.sub_id})

        if sub_inf["Status"] == "Active":
            continue
        
        await session.execute(
            update(User)
            .where(and_(User.id == user_inf.id, User.platform == "vk"))
            .values(
                vip_status = False
            )
        )
        await session.commit()

