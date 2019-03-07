class Hospital:

    def __init__(self, item_ids, ordering_policies, item_delivery_times, item_stochastic_demands, initial_inventory,
                 outstanding_orders, surgeries=[], booking_lead_time=14):
        # hospital parameters, these are set at the start of the simulation and do not change
        #   item_ids to simulate
        #   ordering policy
        #   order lead time distribution
        #   stochastic demand distribution

        # list
        self.item_ids = item_ids
        self.surgeries = surgeries
        # dictionaries
        # item_id : policy_obj
        self.ordering_policies = ordering_policies
        # item_id: NumberGenerator
        self.order_lead_times = item_delivery_times

        # Demand side
        # item_id: NumberGenerator, random demand for items (no surgeries)
        self.item_stochastic_demands = item_stochastic_demands

        # surgery_label: {item_id: NumberGenerator}
        # lookup table for item usage by surgery label
        self.surgery_item_usage = None

        # surgery_label: NumberGenerator
        # random demand for unbooked surgeries
        self.surgery_stochastic_demand = None

        # surgery_label: NumberGenerator
        # random demand for booked surgeries
        self.booked_surgery_stochastic_demand = None

        # State variables of the hospital
        #   inventory, stock of items
        #   outstanding orders

        # initial inventory level for each item
        self.inventory = initial_inventory
        assert (item_id in initial_inventory for item_id in item_ids)

        # outstanding orders
        self.orders = outstanding_orders if outstanding_orders else {item_id: set() for item_id in item_ids}

        # keep track of booking_lead_time number of surgeries in the future
        self.surgery_schedule = {surgery: [0]*booking_lead_time for surgery in surgeries}

        # Performance measures to collect
        #   stock out events

        # dict storing list of times of stockout events per item
        self.stockouts = {item_id: [] for item_id in item_ids}
        self.historical_inventory_levels = {item_id: [initial_inventory[item_id]] for item_id in item_ids}
        self.historical_orders = {item_id: [] for item_id in item_ids}
        self.historical_deliveries = {item_id: [] for item_id in item_ids}
        self.historical_demand = {item_id: [] for item_id in item_ids}

    def set_surgery_item_usage(self, surgery_item_usage):
        self.surgery_item_usage = surgery_item_usage

    def set_surgery_stochastic_demand(self, surgery_stochastic_demand):
        self.surgery_stochastic_demand = surgery_stochastic_demand

    def set_booked_surgery_stochastic_demand(self, booked_surgery_stochastic_demand):
        self.booked_surgery_stochastic_demand = booked_surgery_stochastic_demand

    def set_sim_time(self, sim_time):
        self.historical_inventory_levels = {item_id: [0] * sim_time for item_id in self.item_ids}
        self.historical_orders = {item_id: [0] * sim_time for item_id in self.item_ids}
        self.historical_deliveries = {item_id: [0] * sim_time for item_id in self.item_ids}
        self.historical_demand = {item_id: [0] * sim_time for item_id in self.item_ids}

    def clean_data(self, warm_up):
        for item_id in self.item_ids:
            print(item_id)
            # self.historical_inventory_levels[item_id] = self.historical_inventory_levels[item_id][warm_up:]
            # self.historical_orders[item_id] = self.historical_orders[item_id][warm_up:]
            # self.historical_deliveries[item_id] = self.historical_deliveries[item_id][warm_up:]
            # self.historical_demand[item_id] = self.historical_demand[item_id][warm_up:]

