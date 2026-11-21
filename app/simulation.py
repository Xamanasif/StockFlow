"""Lost-sales scenario replay. Integer units/cash, explicit shared exogenous sequences."""
import hashlib
import json
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field
from .planning import PlanRequest, Item, allocate
from .optimizer import optimize
from .research import forecast, METHODS

class Scenario(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    days:int=Field(default=14,ge=1,le=28)
    budget_pence:int=Field(default=20000,ge=0,le=10000000)
    capacity_units:int=Field(default=1000,ge=0,le=100000)
    initial_stock:int=Field(default=20,ge=0,le=10000)
    unit_cost_pence:int=Field(default=100,gt=0,le=100000)
    holding_pence:int=Field(default=1,ge=0,le=10000)
    shortfall_pence:int=Field(default=200,ge=0,le=100000)
    order_cost_pence:int=Field(default=50,ge=0,le=100000)
    lead_days:int=Field(default=3,ge=0,le=30)
    pack:int=Field(default=2,ge=1,le=100)
    moq:int=Field(default=4,ge=1,le=100)
    variability:float=Field(default=0,ge=0,le=2)
    seed:int=Field(default=2026,ge=0,le=2147483647)

def replay(frame, skus, scenario, method, policy, demand=None):
    s=scenario; end=frame.date.max()-pd.Timedelta(days=8) # final window untouched
    start=end-pd.Timedelta(days=s.days-1)
    stock={k:s.initial_stock for k in skus}; initial=sum(stock.values())
    if initial>s.capacity_units: raise ValueError('Initial stock exceeds capacity')
    if policy not in ['fixed','greedy','milp'] or method not in METHODS: raise ValueError('Unknown policy/method')
    rng=np.random.default_rng(s.seed)
    # Generate once independently of policy/forecasts, including common lead-time draws.
    if demand is None:
        demand=[]
        for day in pd.date_range(start,end):
            demand.append({k:int(round(max(0,frame.loc[frame.is_sale & frame.sku.eq(k) & frame.date.eq(day),'quantity'].sum()*(rng.lognormal(-s.variability**2/2,s.variability) if s.variability else 1)))) for k in skus})
    if len(demand)!=s.days or any(set(d)!=set(skus) or any(not isinstance(v,int) or v<0 for v in d.values()) for d in demand):
        raise ValueError('Demand must have nonnegative integer units for every product/day')
    delays=np.random.default_rng(s.seed+1).integers(0,2,size=s.days).tolist()
    exogenous_hash=hashlib.sha256(json.dumps({'demand':demand,'delays':delays},sort_keys=True).encode()).hexdigest()
    pipeline=[]; cash=0; grants=0; purchase=holding=shortfall=ordering=fulfilled=total=arrived=placed=0; log=[]
    fixed={k:sum(v['units'] for v in forecast(frame,k,start-pd.Timedelta(days=1),7+s.lead_days,method)) for k in skus}
    for t,day in enumerate(pd.date_range(start,end)):
        if t%7==0: cash+=s.budget_pence; grants+=s.budget_pence
        due=[o for o in pipeline if o['arrival']==t]
        for o in due: stock[o['sku']]+=o['units']; arrived+=o['units']
        pipeline=[o for o in pipeline if o['arrival']>t]
        today_filled=0; today_demand=sum(demand[t].values())
        for k in skus:
            f=min(stock[k],demand[t][k]); stock[k]-=f; fulfilled+=f; total+=demand[t][k]; today_filled+=f
            shortfall+=(demand[t][k]-f)*s.shortfall_pence
        holding+=sum(stock.values())*s.holding_pence
        orders=[]
        if t%7==0:
            items=[Item(sku=k,unit_cost_pence=s.unit_cost_pence,on_hand=stock[k],on_order=sum(o['units'] for o in pipeline if o['sku']==k),
                        lead_days=s.lead_days,pack=s.pack,moq=s.moq) for k in skus]
            # Reserve maximum fixed order charges, return unused reserve afterward.
            reserve=len(skus)*s.order_cost_pence
            request=PlanRequest(items=items,budget_pence=max(0,cash-reserve),capacity_units=s.capacity_units,horizon_days=7)
            totals=fixed if policy=='fixed' else {k:sum(v['units'] for v in forecast(frame,k,day,7+s.lead_days,method)) for k in skus}
            allocation=optimize(request,totals) if policy=='milp' else allocate(request,totals)
            for r in allocation['rows']:
                if r['order_units'] and cash>=r['spend_pence']+s.order_cost_pence:
                    q=r['order_units']; placed+=q; cost=r['spend_pence']; purchase+=cost; ordering+=s.order_cost_pence; cash-=cost+s.order_cost_pence
                    o={'sku':r['sku'],'units':q,'arrival':t+max(1,s.lead_days+delays[t])}; pipeline.append(o); orders.append(o)
        outstanding=sum(o['units'] for o in pipeline)
        assert sum(stock.values())+outstanding<=s.capacity_units
        assert initial+arrived-fulfilled==sum(stock.values())
        assert placed-arrived==outstanding
        assert grants-purchase-ordering==cash
        log.append({'date':str(day.date()),'demand_units':today_demand,'fulfilled_units':today_filled,'stock_units':sum(stock.values()),
                    'pipeline_units':outstanding,'cash_pence':cash,'orders':orders})
    return {'method':method,'policy':policy,'label':'synthetic perturbation' if s.variability else 'observed-sales scenario replay',
            'seed':s.seed,'exogenous_sha256':exogenous_hash,'assumptions':s.model_dump(),'assumption_provenance':'all fields user scenario assumptions; currency GBP',
            'fulfilled_units':fulfilled,'proxy_demand_units':total,'fill_rate':fulfilled/total if total else None,'unmet_proxy_units':total-fulfilled,
            'purchase_pence':purchase,'holding_pence':holding,'shortfall_pence':shortfall,'ordering_pence':ordering,
            'scenario_cost_pence':purchase+holding+shortfall+ordering,'cash_grants_pence':grants,'cash_remaining_pence':cash,
            'average_stock_units':sum(r['stock_units'] for r in log)/s.days,'average_stock_capital_pence':sum(r['stock_units'] for r in log)*s.unit_cost_pence/s.days,
            'terminal_stock_units':sum(stock.values()),'terminal_pipeline_units':sum(o['units'] for o in pipeline),
            'terminal_pipeline_value_pence':sum(o['units'] for o in pipeline)*s.unit_cost_pence,'outstanding_unpaid_commitments_pence':0,
            'terminal_inventory_credit_pence':0,'days':log}

def compare(frame,skus,scenario):
    rows=[replay(frame,skus,scenario,m,p) for m in METHODS for p in ['fixed','greedy','milp']]
    for r in rows:
        r['pareto']=not any(o['scenario_cost_pence']<=r['scenario_cost_pence'] and o['unmet_proxy_units']<=r['unmet_proxy_units'] and
                            (o['scenario_cost_pence']<r['scenario_cost_pence'] or o['unmet_proxy_units']<r['unmet_proxy_units']) for o in rows)
    return rows
