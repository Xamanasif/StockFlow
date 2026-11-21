"""Deterministic greedy heuristic. Not an optimal purchasing policy or profit forecast."""
import math
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Item(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    sku: str = Field(min_length=1, max_length=80)
    unit_cost_pence: int = Field(gt=0, le=100000000)
    on_hand: int = Field(ge=0, le=10000000)
    on_order: int = Field(default=0, ge=0, le=10000000)
    lead_days: int = Field(default=7, ge=0, le=60)
    pack: int = Field(default=1, gt=0, le=10000)
    moq: int = Field(default=1, gt=0, le=10000)
    priority: float = Field(default=1, gt=0, le=10)

class PlanRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    budget_pence: int = Field(default=100000, ge=0, le=1000000000)
    capacity_units: int = Field(default=1000, ge=0, le=10000000)
    horizon_days: int = Field(default=14, ge=1, le=30)
    items: list[Item] = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def unique_skus(self):
        if len({x.sku for x in self.items}) != len(self.items):
            raise ValueError('Duplicate SKU assumptions')
        return self

def allocate(request, forecast_totals):
    rows = []
    occupied = sum(x.on_hand + x.on_order for x in request.items)
    if occupied > request.capacity_units:
        raise ValueError('Existing stock plus on-order already exceeds capacity')
    for item in sorted(request.items, key=lambda x: x.sku):
        expected = float(forecast_totals[item.sku])
        if not math.isfinite(expected) or expected < 0:
            raise ValueError('Forecast must be finite and nonnegative')
        gap = max(0, expected - item.on_hand - item.on_order)
        target = int(math.ceil(gap / item.pack) * item.pack)
        minimum = int(math.ceil(item.moq / item.pack) * item.pack)
        if 0 < target < minimum:
            target = minimum
        rows.append({'sku': item.sku, 'expected_sales_units': round(expected, 4),
                     'on_hand': item.on_hand, 'on_order': item.on_order,
                     'requested_units': target, 'order_units': 0,
                     'unit_cost_pence': item.unit_cost_pence,
                     'pack': item.pack, 'first_order_minimum': minimum,
                     'priority': item.priority})
    spent, used = 0, occupied
    # Each iteration adds at least one unit; a hard cap prevents unbounded service work.
    iterations = 0
    while iterations < 10000:
        options = []
        for row in rows:
            step = row['first_order_minimum'] if row['order_units'] == 0 else row['pack']
            remaining = row['requested_units'] - row['order_units']
            cost = step * row['unit_cost_pence']
            if remaining < step or spent + cost > request.budget_pence or used + step > request.capacity_units:
                continue
            uncovered = max(0, row['expected_sales_units'] - row['on_hand'] - row['on_order'] - row['order_units'])
            score = min(step, uncovered) * row['priority'] / cost
            if score > 0:
                options.append((score, row['sku'], row, step, cost))
        if not options:
            break
        options.sort(key=lambda x: (-x[0], x[1]))
        _, _, row, step, cost = options[0]
        row['order_units'] += step
        spent += cost
        used += step
        iterations += 1
    for row in rows:
        row['spend_pence'] = row['order_units'] * row['unit_cost_pence']
        row['uncovered_target_units'] = row['requested_units'] - row['order_units']
        row['reason'] = ('No replenishment target' if row['requested_units'] == 0 else
                         'Target covered' if row['uncovered_target_units'] == 0 else
                         'Target partly or wholly uncovered under budget, capacity or lot constraints')
    return {'policy': 'greedy_priority_weighted_coverage_per_penny', 'optimality_claim': False,
            'spent_pence': spent, 'remaining_budget_pence': request.budget_pence - spent,
            'occupied_units_after_plan': used, 'iteration_limit_reached': iterations == 10000,
            'rows': rows,
            'limitations': ['Assumed inventory, costs and lead times; not historical stock measurements.',
                            'Static aggregate coverage, not a time-phased stockout simulator.',
                            'On-order arrivals assumed available in the planning coverage window.',
                            'Capacity measured in units, not volume; no supplier reliability model.',
                            'Priority-weighted coverage is not profit or guaranteed service level.']}

