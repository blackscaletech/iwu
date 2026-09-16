"""A conservative bounded-sum interval, not a universal confidence procedure."""
import math
from iwu import number,require,safe_sum


def bounded_sum_interval(estimate, block_ranges, alpha=.05):
    """Hoeffding interval for a sum of INDEPENDENT bounded random blocks.

    block_ranges[b] is a known upper minus lower range for block b; lower bounds
    are assumed zero. For independent Bernoulli task episodes use pi_i*h_i/n_i
    for EACH scheduled episode. Dependence within a block is allowed; ranges
    must then cover the entire block. Independence across blocks is an external
    assumption, not inferred from IDs. Does not include human-weight uncertainty.
    """
    number(estimate);require(0<alpha<1,"alpha must lie strictly between zero and one")
    require(bool(block_ranges),"nonempty blocks required")
    ranges=[number(x) for x in block_ranges]
    maximum=safe_sum(ranges)
    require(estimate<=maximum,"estimate outside bounds")
    # Scaling prevents squaring large ranges from overflowing unnecessarily.
    scale=max(ranges)
    radius=0. if scale==0 else scale*math.sqrt(.5*math.log(2/alpha)*safe_sum((x/scale)**2 for x in ranges))
    return [max(0.,estimate-radius),min(maximum,estimate+radius)]


def lower_confidence_credit(observed_lower, block_ranges, alpha=.05):
    """One-sided (1-alpha) lower confidence bound on expected fixed-registry credit.

    Uses ln(1/alpha), not the two-sided ln(2/alpha). `observed_lower` may
    conservatively count every missing assigned outcome as uncredited. This
    does NOT turn missing outcomes into a complete point estimate. Blocks and
    their range bounds include every assigned episode, observed or missing.
    """
    number(observed_lower);number(alpha,positive=True)
    require(alpha<1,"alpha must lie strictly between zero and one")
    require(bool(block_ranges),"nonempty blocks required")
    ranges=[number(x) for x in block_ranges]
    maximum=safe_sum(ranges)
    require(observed_lower<=maximum,"observed lower bound exceeds possible credit")
    scale=max(ranges)
    radius=0. if scale==0 else scale*math.sqrt(.5*math.log(1/alpha)*safe_sum((x/scale)**2 for x in ranges))
    return dict(lower_credit=max(0.,observed_lower-radius),one_sided_confidence=1-alpha,
                uncertainty_margin=radius,independent_blocks=len(ranges),maximum_credit=maximum,
                interpretation="Lower bound on expected fixed-registry credit, conditional on correct bounds, independent blocks and fixed weights; not next-task success probability.")


def incomplete_outcome_interval(observed_lower, observed_upper, block_ranges, alpha=.05):
    """Combine arbitrary missing-outcome bounds with the two-sided sampling bound."""
    number(observed_lower);number(observed_upper)
    require(observed_lower<=observed_upper,"reversed observed bounds")
    lo=bounded_sum_interval(observed_lower,block_ranges,alpha)[0]
    hi=bounded_sum_interval(observed_upper,block_ranges,alpha)[1]
    return [lo,hi]
