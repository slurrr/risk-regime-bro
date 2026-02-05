# Risk Regime Metric: Alt Risk Appetite vs BTC

## Logic and Math Layer

### Inputs

- Benchmark: **BTC**
- Basket: **N alts**, always containing ≥1 symbol per **bucket**:
	- **Majors** (ETH, SOL, BNB…)
	- **Large alts** (top cap non-majors)
	- **Midcaps**
	- **High beta / perp-driven**
	- **Memes**

Basket selection rule (dynamic): top by **activity** (e.g., 24h USD volume + perp OI), per bucket.

---

## Step 1 — Per-symbol relative performance vs BTC

For each alt $i$ over lookback $L$ :

$$
r_i = \ln\left(\frac{P_i(t)}{P_i(t-L)}\right) - \ln\left(\frac{P_{BTC}(t)}{P_{BTC}(t-L)}\right)
$$

Interpretation:

- $r_i > 0$ : alt outperforming BTC (risk-seeking)
- $r_i < 0$ : alt underperforming BTC (risk-averse)

---

## Step 2 — Bucket-level strength + breadth

For each bucket $b$ with symbols $i \in b$ :

**Strength**

$$
S_b = \frac{1}{|b|}\sum_{i \in b} r_i
$$

**Breadth**

$$
B_b = \frac{1}{|b|}\sum_{i \in b}\mathbb{1}[r_i > 0]
$$

Bucket score (simple, interpretable):

$$
Q_b = S_b \cdot (2B_b - 1)
$$
- $2B_b-1$ maps breadth to $[-1, +1]$
- So a bucket only scores big if **outperformance is broad**, not just 1 coin.

---

## Step 3 — Risk ladder weighting

Assign risk weights (distance from BTC):

- Majors $w=1$
- Large alts $w=2$
- Midcaps $w=3$
- High beta $w=4$
- Memes $w=5$

---

## Step 4 — Final metric (single number)

$$
\textbf{RISK}(t) = \sum_b w_b \cdot Q_b
$$

That’s it.

---

## Readouts you asked for (intricacies)

### 1) “Memes are outperforming the rest”

Compute **meme dominance**:

$$
\text{MemeDom} = \frac{w_{meme}Q_{meme}}{\sum_b |w_b Q_b|}
$$

High MemeDom + positive RISK = **high risk-on**, frothy.

### 2) “Risk on/off and extent”

- **Risk-on**: RISK > 0
- **Risk-off**: RISK < 0
- **Extent**: magnitude $|\text{RISK}|$

If you want a bounded dial without “normalization,” use a pure squash (not data-dependent):

$$
\text{Dial} = \tanh(\text{RISK})
$$

Still the same metric, just mapped to $[-1,1]$ .

---

## How it matches your mental model

- **BTC rallies, alts not drained** → many $r_i \ge 0$ → $B_b$ high → RISK positive.
- **BTC shaky, alts catch up** → $r_i>0$ even while BTC weak → buckets positive, especially mid/high beta → RISK strongly positive.
- **BTC consolidates, alts dead** → $r_i<0$ broadly → $B_b$ low → RISK negative.
- **BTC mild dump, alts bleed out** → $r_i\ll 0$ , especially high-beta/memes → heavily negative RISK (extreme risk-off).

---
## Timeframe Stack
If you want one extra layer *without* “smoothing”: compute it at multiple $L$ (e.g., 1h, 6h, 1d) and view as a stack. Same metric, different lens.

---
## Divergence

that seems decent what about "market looks shit, but everyone is gambling on memes"?

---

That’s a **divergent speculation regime** — and your metric already exposes it structurally without adding new machinery.

Let’s walk it through using the same components.

---

## Situation - divergent speculation regime

**“Market looks bad, but memes are ripping.”**

Meaning in raw terms:

- BTC weak or flat
- Majors / large alts underperforming BTC
- Midcaps mixed
- Memes strongly outperforming BTC

So per bucket:

| Bucket | $S_b$ | $B_b$ | $Q_b$ |
| --- | --- | --- | --- |
| Majors | negative | low | negative |
| Large alts | negative | low | negative |
| Midcaps | small | mixed | small |
| High beta | positive | decent | positive |
| Memes | strongly positive | high | **very positive** |

---

## What happens to the main metric

$$
RISK = \sum w_b Q_b
$$

Because memes have **highest weight**, they can push RISK **positive or near zero** even while most of the market is weak.

That’s the *tell*.

---

## Detecting this specific regime

Define:

### 1️⃣ Structural Risk Breadth

$$
Breadth_{total} = \frac{\sum_i \mathbb{1}[r_i > 0]}{N}
$$

Low in this regime.

---

### 2️⃣ Speculative Concentration

$$
SpecConc = \frac{w_{meme}Q_{meme}}{\sum_b |w_b Q_b|}
$$

High in this regime.

---

## The Pattern Signature

| Metric | Value |
| --- | --- |
| **RISK** | Mildly positive or near 0 |
| **Breadth\_total** | Low |
| **SpecConc** | Very high |

---

## Interpretation

This is **not true risk-on**.  
It is **terminal / localized risk-seeking**.

Capital is not rotating across the curve.  
It is skipping structure and going straight to the casino.

Psychology:

- Traders don’t trust majors
- No belief in sustainable trend
- But still chasing volatility

This usually appears:

- Late in downtrends
- During distribution
- In chop before a leg down
- Near local exhaustion tops

---

## Label for this regime

**“Speculative Flight”**  
or  
**“Degenerate Risk-On / Structural Risk-Off”**

---

## Why this matters

Your main RISK metric alone says:

> “Some risk appetite exists.”

But the **distribution of where that risk lives** says:

> “This is unhealthy risk. Fragile. Short-lived.”

So the full read is not a single number — it's:

**RISK (level)** + **Breadth (how many)** + **SpecConc (where on the ladder)**

That combination distinguishes:

| State | Meaning |
| --- | --- |
| High RISK + high breadth | Sustainable risk-on |
| High RISK + high SpecConc | Frothy / unstable |
| Low RISK + high SpecConc | **Market looks bad but memes gambling** ← your case |
| Low RISK + low SpecConc | Clean risk-off |

---

You don’t need new math.  
This regime falls out naturally from **how the bucket contributions distribute**, not from the headline score.

---

## Translation Layer

Ok so pretty good metric but a lot's left to interpretation. create a semantic translator that takes what the metric spits out and translates it into relatable crypto bro regime labeling. should be able to determine degrees within or if the metric doesn't have a perfect regime it still spits out something coherent that tells you you are kinda between regimes

---
## Semantic Translation Interpreter Layer

Good — now we’re building the **interpreter layer**, not changing the metric.

This is a **semantic translator** that turns raw outputs into human regime language.

---

## Inputs (from your metric)

At time **t**:

- **RISK** = overall risk appetite score
- **Breadth\_total** = fraction of alts outperforming BTC
- **SpecConc** = share of risk coming from memes/high-beta
- **MajorsScore** = $w_{majors}Q_{majors}$
- **MidScore** = midcap contribution
- **MemeScore** = meme contribution

---

## Step 1 — Convert numbers to semantic intensities

### Risk Level

| RISK | Label |
| --- | --- |
| ≫ positive | **Full Send** |
| moderately + | **Risk On** |
| near 0 | **Chop / Indecision** |
| moderately − | **Risk Off** |
| ≪ negative | **Capitulation Mode** |

---

### Breadth (how many coins participating)

| Breadth\_total | Label |
| --- | --- |
| High | **Broad** |
| Medium | **Selective** |
| Low | **Narrow** |

---

### Speculation Location

| SpecConc | Label |
| --- | --- |
| High | **Casino Led** |
| Medium | **Balanced** |
| Low | **Structure Led** |

---

## Step 2 — Regime Archetypes (pattern recognition)

We classify by *shape*, not just value.

---

### 🟢 Healthy Risk-On

**Condition**

- RISK > 0
- Breadth high
- SpecConc medium or low

**Output**

> **“Broad Risk-On — Rotation Is Real”**

Meaning: capital moving across curve, sustainable.

---

### 🟡 Frothy Risk-On

**Condition**

- RISK > 0
- SpecConc high
- Breadth medium/low

**Output**

> **“Degenerate Send — Memes Running the Market”**

Meaning: late-cycle, unstable, hype-driven.

---

### 🔵 Rotation / Transition

**Condition**

- RISK near 0
- MidScore > MajorsScore
- Breadth medium

**Output**

> **“Rotation Phase — Capital Shifting Under the Hood”**

---

### 🟠 Structural Risk-Off

**Condition**

- RISK < 0
- MajorsScore weak
- Breadth low

**Output**

> **“Risk-Off — Capital Hiding in BTC”**

---

### 🔴 Panic / Liquidation Regime

**Condition**

- RISK ≪ 0
- MemeScore very negative
- Breadth very low

**Output**

> **“Liquidation Mode — Alts Getting Nuked”**

---

### 🟣 Speculative Divergence (your earlier scenario)

**Condition**

- RISK ≤ 0
- SpecConc high
- MajorsScore negative

**Output**

> **“Shit Market, Memes Pumping — Casino Flight”**

---

## Step 3 — Degree Modifiers (intensity words)

Attach strength adjective from |RISK|:

| Magnitude | Modifier |
| --- | --- |
| Extreme | **Violent** |
| Strong | **Heavy** |
| Mild | **Light** |

Example:

> **“Heavy Risk-Off — Capital Hiding in BTC”**  
> **“Violent Degenerate Send — Memes Running the Market”**

---

## Step 4 — Final Output Format

The translator returns:

**Primary Regime**  
**Participation Descriptor**  
**Risk Structure Descriptor**

Example outputs:

- **“Broad Risk-On — Rotation Is Real”**
- **“Violent Degenerate Send — Memes Running the Market”**
- **“Light Risk-Off — Capital Hiding in BTC”**
- **“Shit Market, Memes Pumping — Casino Flight”**
- **“Choppy Transition — No Clear Risk Control”**

---

## Key Property

This system:

- Never returns nothing
- If metrics conflict, it defaults to **Transition / Mixed** regime
- Uses the *distribution of risk*, not just level