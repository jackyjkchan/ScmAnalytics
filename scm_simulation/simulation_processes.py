def book_surgeries(env, hospital):
    """Process: Generates random number of surgeries to book K days into the future. This process assumes that at every
    period, we will book all surgeries K periods away. This is a simplification of having surgeons make their surgery
    schedules known 2 weeks in advance.
    """
    while True:
        yield env.timeout(1)

        for surgery in hospital.surgeries:
            num_surgeries = int(hospital.booked_surgery_stochastic_demand[surgery].gen())
            hospital.surgery_schedule[surgery].append(num_surgeries)
            hospital.surgery_schedule[surgery].pop(0)


def surgery_demand_stochastic(env, hospital):
    """Process: Generates random arrivals of surgeries that each consume random number of items
    surgery_demand_generator is a dictionary with {"surgery label": item_demand_generator}
    """
    while True:
        yield env.timeout(1)

        for surgery in hospital.surgeries:
            num_surgeries = int(hospital.surgery_stochastic_demand[surgery].gen())
            num_surgeries += hospital.surgery_schedule[surgery][0]
            for item_id in hospital.item_ids:
                d = 0
                d += sum(hospital.surgery_item_usage[surgery][item_id].gen() for i in range(0, num_surgeries))
                hospital.historical_demand[item_id][env.now] += d
                if hospital.inventory[item_id] < d:
                    hospital.inventory[item_id] = 0
                    hospital.stockouts[item_id].append(env.now)
                else:
                    hospital.inventory[item_id] -= d


def demand_stochastic(env, item_demand_generator, hospital):
    """Process: Consumes a number of each item based on a distribution to draw from"""
    while True:
        yield env.timeout(1)

        for item_id in hospital.item_ids:
            d = item_demand_generator[item_id].gen()
            hospital.historical_demand[item_id][env.now] += d
            #print("Demand:", d)
            #print("Current Inventory", hospital.inventory[item_id])
            if hospital.inventory[item_id] < d:
                #print("!Stock out!")
                hospital.inventory[item_id] = 0
                hospital.stockouts[item_id].append(env.now)
            else:
                #print("No Stockout")
                hospital.inventory[item_id] -= d
            #print("New Inventory:", hospital.inventory[item_id])


def ship_order(env, item_id, qty, delivery_time, hospital):
    """ Process: qty amount of item_id taking ship_time to arrive at the hospital.
    created by place_order process
    """
    while True:
        order_time = env.now
        yield env.timeout(delivery_time)
        hospital.inventory[item_id] += qty
        hospital.orders[item_id].remove((order_time, qty))
        hospital.historical_deliveries[item_id][env.now] += qty
        env.exit()


def place_order(env, ordering_policies, item_delivery_times, hospital):
    """Process: decision maker placing orders by implementing a given policy by calling policy.action(hospital)"""
    while True:
        yield env.timeout(1)

        for item_id in hospital.item_ids:
            order_qty = ordering_policies[item_id].action(hospital)
            #print("Placing order:", order_qty)
            hospital.orders[item_id].add((env.now, order_qty))
            hospital.historical_orders[item_id][env.now] += order_qty
            delivery_time = item_delivery_times[item_id].gen()

            env.process(ship_order(env, item_id, order_qty, delivery_time, hospital))


def hospital_bookkeeping(env, hospital):
    """Process: hospital does book keeping at EOD and tracks values they care about
     inventory level
     more to come...
     """
    while True:
        yield env.timeout(1)

        for item_id in hospital.item_ids:
            hospital.historical_inventory_levels[item_id][env.now]+=hospital.inventory[item_id]


def warm_up(env, warm_up_time, hospital):
    """Clear hospital stats"""
    while True:
        yield env.timeout(warm_up_time)

        # item_ids = hospital.item_ids
        # hospital.stockouts = {item_id: [] for item_id in item_ids}
        # hospital.historical_inventory_levels = {item_id: [hospital.inventory[item_id]] for item_id in item_ids}
        # hospital.historical_orders = {item_id: [] for item_id in item_ids}
        # hospital.historical_deliveries = {item_id: [] for item_id in item_ids}
        # hospital.historical_demand = {item_id: [] for item_id in item_ids}
        break
