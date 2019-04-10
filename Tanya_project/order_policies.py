import numpy as np


class OrderPolicy:
    def action(self, env, hospital):
        return 0


class POUTPolicy(OrderPolicy):

    def __init__(self, item_id, beta, level):
        self.item_id = item_id
        self.level = level
        self.beta = beta

    def action(self, currenttime, hospital):
        expected_demand = 0
        k = round(int(hospital.order_lead_times[self.item_id].mean()))
        if self.item_id in hospital.item_stochastic_demands:
            expected_demand += hospital.item_stochastic_demands[self.item_id].mean()
        for surgery in hospital.surgeries:
            expected_surgeries = hospital.surgery_stochastic_demand[surgery].mean()
            if len(hospital.surgery_schedule[surgery]) > currenttime + k:
                expected_surgeries += np.mean(hospital.surgery_schedule[surgery][currenttime:currenttime + k])
            else:
                expected_surgeries += np.mean(hospital.surgery_schedule[surgery][currenttime:])
            if self.item_id in hospital.surgery_item_usage[surgery]:
                expected_item_usage = hospital.surgery_item_usage[surgery][self.item_id].mean()
                expected_demand += expected_item_usage * expected_surgeries
        receipt = hospital.historical_deliveries[self.item_id][currenttime]
        inv = hospital.historical_inventory_levels[self.item_id][currenttime - 1] + receipt - expected_demand
        wip = 0
        if currenttime > 1:
            if currenttime - k >= 0:
                wip += np.mean(hospital.historical_orders[self.item_id][currenttime - k:currenttime - 1])
            else:
                wip += np.mean(hospital.historical_orders[self.item_id][:currenttime - 1])
        else:
            wip += hospital.historical_orders[self.item_id][0]
        orderqty = expected_demand + self.beta * (self.level + expected_demand * k - (inv + wip))
        return max(0, orderqty)


class POUTPolicyWithoutSchedule(OrderPolicy):

    def __init__(self, item_id, beta, level):
        self.item_id = item_id
        self.level = level
        self.beta = beta

    def action(self, currenttime, hospital):
        expected_demand = 0
        k = round(int(hospital.order_lead_times[self.item_id].mean()))
        if self.item_id in hospital.item_stochastic_demands:
            expected_demand += hospital.item_stochastic_demands[self.item_id].mean()
        for surgery in hospital.surgeries:
            expected_surgeries = hospital.surgery_stochastic_demand[surgery].mean()
            expected_surgeries += hospital.booked_surgery_stochastic_demand[surgery].mean()
            if self.item_id in hospital.surgery_item_usage[surgery]:
                expected_item_usage = hospital.surgery_item_usage[surgery][self.item_id].mean()
                expected_demand += expected_item_usage * expected_surgeries
        receipt = hospital.historical_deliveries[self.item_id][currenttime]
        inv = hospital.historical_inventory_levels[self.item_id][currenttime - 1] + receipt - expected_demand
        wip = 0
        if currenttime > 1:
            if currenttime - k >= 0:
                wip += np.mean(hospital.historical_orders[self.item_id][currenttime - k:currenttime - 1])
            else:
                wip += np.mean(hospital.historical_orders[self.item_id][:currenttime - 1])
        else:
            wip += hospital.historical_orders[self.item_id][0]
        orderqty = expected_demand + self.beta * (self.level + expected_demand * k - (inv + wip))
        return max(0, orderqty)


class DeterministicConDOIPolicyV2(OrderPolicy):

    def __init__(self, item_id, constant_days=5):
        self.item_id = item_id
        self.constant_days = constant_days

    def action(self, env, hospital):
        k = self.constant_days
        delivery_time = hospital.order_lead_times[self.item_id].mean()
        expected_demand = 0
        if self.item_id in hospital.item_stochastic_demands:
            expected_demand += hospital.item_stochastic_demands[self.item_id].mean()
        for surgery in hospital.surgeries:
            horizon = round(int(k+delivery_time))
            expected_surgeries = hospital.surgery_stochastic_demand[surgery].mean()
            expected_surgeries += np.mean(hospital.surgery_schedule[surgery][env.now: env.now+horizon]) \
                if len(hospital.surgery_schedule[surgery]) > env.now+horizon \
                else np.mean(hospital.surgery_schedule[surgery][env.now:])
            if self.item_id in hospital.surgery_item_usage[surgery]:
                expected_item_usage = hospital.surgery_item_usage[surgery][self.item_id].mean()
                expected_demand += expected_surgeries * expected_item_usage
        order_up_level = int((k + delivery_time) * expected_demand)
        outstanding_orders = sum(hospital.historical_deliveries[self.item_id][env.now + 1:]) \
            if len(hospital.historical_deliveries[self.item_id]) > (env.now + 1) \
            else 0
        qty = order_up_level - hospital.inventory[self.item_id] - outstanding_orders
        return max(0, qty)


class DeterministicConDOIPolicyV2WithoutSchedule(OrderPolicy):

    def __init__(self, item_id, constant_days=5):
        self.item_id = item_id
        self.constant_days = constant_days

    def action(self, env, hospital):
        k = self.constant_days
        delivery_time = hospital.order_lead_times[self.item_id].mean()
        expected_demand = 0
        if self.item_id in hospital.item_stochastic_demands:
            expected_demand += hospital.item_stochastic_demands[self.item_id].mean()
        for surgery in hospital.surgeries:
            expected_surgeries = hospital.surgery_stochastic_demand[surgery].mean()
            expected_surgeries += hospital.booked_surgery_stochastic_demand[surgery].mean()
            if self.item_id in hospital.surgery_item_usage[surgery]:
                expected_item_usage = hospital.surgery_item_usage[surgery][self.item_id].mean()
                expected_demand += expected_surgeries * expected_item_usage
        order_up_level = int((k + delivery_time) * expected_demand)
        outstanding_orders = sum(hospital.historical_deliveries[self.item_id][env.now + 1:]) \
            if len(hospital.historical_deliveries[self.item_id]) > (env.now + 1)             \
            else 0
        qty = order_up_level - hospital.inventory[self.item_id] - outstanding_orders
        return max(0, qty)
