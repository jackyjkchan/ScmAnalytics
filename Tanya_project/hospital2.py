from hospital import Hospital


class Hospital2(Hospital):

    def __init__(self, item_ids,
                 ordering_policies,
                 item_delivery_times,
                 item_stochastic_demands,
                 initial_inventory,
                 outstanding_orders,
                 surgeries):

        Hospital.__init__(self, item_ids,
                          ordering_policies,
                          item_delivery_times,
                          item_stochastic_demands,
                          initial_inventory,
                          outstanding_orders,
                          surgeries)
        self.sum_surgery = {}
        self.new_booked_surgery_stochastic_demand = {}
        self.new_item_stochastic_demands = {}
        self.new_lead_times = {}
        self.new_surgery_item_usage = {}
        self.new_surgery_stochastic_demand = {}

    def setrandomvars(self, horizon):

        self.new_lead_times = {item: [self.order_lead_times[item].gen()
                                      for _ in range(0, horizon)] for item in self.item_ids}
        self.new_surgery_stochastic_demand = {surgery: [self.surgery_stochastic_demand[surgery].gen()
                                                        for _ in range(0, horizon)] for surgery in self.surgeries}
        self.new_booked_surgery_stochastic_demand = {surgery: [self.booked_surgery_stochastic_demand[surgery].gen()
                                                               for _ in range(0, horizon)]
                                                     for surgery in self.surgeries}
        self.sum_surgery = {surgery: [sum(self.new_booked_surgery_stochastic_demand[surgery][i],
                                          self.new_surgery_stochastic_demand[surgery][i])
                                      for i in range(0, horizon)] for surgery in self.surgeries}
        self.new_surgery_item_usage = {surgery: {item: [sum(self.surgery_item_usage[surgery][item].gen()
                                                            for _ in range(0, self.sum_surgery[surgery][i]))
                                                        for i in range(0, horizon)] for item in self.item_ids}
                                       for surgery in self.surgeries}
        self.new_item_stochastic_demands = {item: [self.item_stochastic_demands[item].gen()
                                                   for _ in range(0, horizon)] for item in self.item_ids}
