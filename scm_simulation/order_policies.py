class OrderPolicy:
    def action(self, hospital):
        return 0


class DeterministicConDOIPolicy(OrderPolicy):

    def __init__(self, item_id, constant_days=5):
        self.item_id = item_id
        self.constant_days = constant_days

    def action(self, hospital):
        expected_demand = 0
        if self.item_id in hospital.item_stochastic_demands:
            expected_demand += hospital.item_stochastic_demands[self.item_id].mean()
        for surgery in hospital.surgeries:
            if self.item_id in hospital.surgery_item_usage[surgery]:
                expected_surgeries = hospital.surgery_stochastic_demand[surgery].mean()
                expected_item_usage = hospital.surgery_item_usage[surgery][self.item_id]
                expected_demand += expected_surgeries * expected_item_usage

        delivery_time = hospital.order_lead_times[self.item_id].mean()
        order_up_level = int(expected_item_usage * delivery_time * self.constant_days)

        # print("order up level:", order_up_level)
        # print("inventory:", hospital.inventory[self.item_id])
        # print("outstanding orders:", sum(order[1] for order in hospital.orders[self.item_id]))
        qty = order_up_level\
            - hospital.inventory[self.item_id]\
            - sum(order[1] for order in hospital.orders[self.item_id])

        return max(0, qty)


class DeterministicConDOIPolicyV2(OrderPolicy):

    def __init__(self, item_id, constant_days=5):
        self.item_id = item_id
        self.constant_days = constant_days

    def action(self, hospital):
        expected_demand = 0
        if self.item_id in hospital.item_stochastic_demands:
            expected_demand += hospital.item_stochastic_demands[self.item_id].mean()
        for surgery in hospital.surgeries:
            if self.item_id in hospital.surgery_item_usage[surgery]:
                expected_surgeries = hospital.surgery_stochastic_demand[surgery].mean()
                expected_item_usage = hospital.surgery_item_usage[surgery][self.item_id].mean()
                expected_demand += expected_surgeries * expected_item_usage

        delivery_time = hospital.order_lead_times[self.item_id].mean()
        order_up_level = int((self.constant_days + delivery_time) * expected_demand)

        qty = order_up_level\
            - hospital.inventory[self.item_id]\
            - sum(order[1] for order in hospital.orders[self.item_id])
        #print("order up level:", order_up_level)
        #print("inventory:", hospital.inventory[self.item_id])
        #print("outstanding orders:", sum(order[1] for order in hospital.orders[self.item_id]))
        return max(0, qty)
