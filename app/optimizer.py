"""Static weighted covered-unit MILP, not dynamic inventory optimality."""
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from .planning import allocate

def optimize(request, totals, time_limit=2.):
    base=allocate(request,totals); rows=base['rows']; n=len(rows)
    # x packs, y activated, z covered units. Maximise sum priority*z.
    c=np.zeros(3*n); lower=np.zeros(3*n); upper=np.zeros(3*n)
    constraints=[]; lo=[]; hi=[]
    def add(a,l,h): constraints.append(a); lo.append(l); hi.append(h)
    budget=np.zeros(3*n); capacity=np.zeros(3*n)
    for i,r in enumerate(rows):
        maximum=r['requested_units']//r['pack']; minimum=r['first_order_minimum']//r['pack']
        upper[i]=maximum; upper[n+i]=1; upper[2*n+i]=max(0,totals[r['sku']]-r['on_hand']-r['on_order'])
        c[2*n+i]=-r['priority']; budget[i]=r['pack']*r['unit_cost_pence']; capacity[i]=r['pack']
        a=np.zeros(3*n); a[i]=1; a[n+i]=-maximum; add(a,-np.inf,0)
        a=np.zeros(3*n); a[i]=1; a[n+i]=-minimum; add(a,0,np.inf)
        a=np.zeros(3*n); a[2*n+i]=1; a[i]=-r['pack']; add(a,-np.inf,0)
    add(budget,0,request.budget_pence)
    occupied=sum(x.on_hand+x.on_order for x in request.items)
    add(capacity,0,request.capacity_units-occupied)
    result=milp(c,integrality=np.r_[np.ones(2*n),np.zeros(n)],bounds=Bounds(lower,upper),
                constraints=LinearConstraint(np.array(constraints),lo,hi),options={'time_limit':time_limit})
    if not result.success:
        return {**base,'solver_status':int(result.status),'solver_message':str(result.message),'fallback':'greedy feasible fallback','optimality_claim':False}
    for i,r in enumerate(rows):
        r['order_units']=int(round(result.x[i]))*r['pack']; r['spend_pence']=r['order_units']*r['unit_cost_pence']
        r['uncovered_target_units']=r['requested_units']-r['order_units']; r['reason']='Static weighted coverage optimum; review uncovered target'
    spent=sum(r['spend_pence'] for r in rows)
    return {**base,'policy':'static_milp_weighted_covered_units','spent_pence':spent,
            'remaining_budget_pence':request.budget_pence-spent,'occupied_units_after_plan':occupied+sum(r['order_units'] for r in rows),
            'solver_status':int(result.status),'solver_message':str(result.message),'mip_gap':float(result.mip_gap),
            'objective_covered_units':float(-result.fun),'optimality_claim':'static specified objective only','rows':rows}
