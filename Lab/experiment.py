import asyncio
import logging
import random

from .lab import Lab
from .node import Node

async def generate_traffic(lab: Lab, mean_amount):
    async def generate_pay_invoice(sender_key: str, recipient_key: str, amount: int):
        try:
            recipient: Node = lab.nodes[recipient_key]
            invoice = await recipient.new_invoice(amount = amount, description = "Hello world")
            logging.info(f"INVOICE {sender_key} {recipient_key} {invoice}")
            sender: Node = lab.nodes[sender_key]
            pay = await sender.pay_invoice(invoice)
            logging.info(f"PAYMENT {sender_key} {recipient_key} {pay}")
            return pay
        except Exception as e:
            logging.error(f"PAYMENT {sender_key} {recipient_key} {amount} {e}")
            if isinstance(e, asyncio.CancelledError):
                raise

    generator = random.Random(f"{lab.name.split("_")[0]}:{lab.total_node_count}:{lab.total_channel_count}")
    node_keys: list[str] = list(lab.nodes)

    request_count: int  = lab.total_node_count // 4
    wait_interval: float = 10 / request_count

    logging.info(f"TRAFFIC_START {lab.name}")

    async with asyncio.TaskGroup() as group:
        while lab.status == Lab.Status.READY:
            for _ in range(request_count):
                sender_key: str = generator.choice(node_keys)
                recipient_key: str = generator.choice(node_keys)
                amount: int = int(generator.gauss(mean_amount, mean_amount * 0.25))
                group.create_task(
                    generate_pay_invoice(
                        sender_key,
                        recipient_key,
                        amount),
                    name = f"GENERATE_PAY_INVOICE {sender_key} {recipient_key} {amount}"
                )
                await asyncio.sleep(wait_interval)


    logging.info(f"TRAFFIC_STOP {lab.name}")
