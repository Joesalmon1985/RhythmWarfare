# OpenRA Red Alert behaviour specification for the rhythm battle simulation

Source: OpenRA checkout `WizardRTSHybrid/external/openra`, commit `e7e9e4ad270221d7fb9725b348c75504d48c1ebd`.
All paths below are relative to that checkout. Line numbers are from that commit.

Scope: the roster `e1`, `1tnk`, `heli`/`hpad`, `fact`, `weap`, `barr`, `powr`, `sbag`, `gun`, `sam`, the
"Rush AI" `SquadManagerBotModule` (with Normal/Turtle differences noted), and only the engine machinery those use.
Production/economy bot modules are deliberately omitted (production is driven by music input in our game).

Units of measure used throughout (OpenRA conventions you must keep):

| Quantity | OpenRA unit | Notes |
|---|---|---|
| Distance | `WDist` world unit; **1 cell = 1024** | `4c768` = 4*1024+768 = 4864 |
| Time | tick; **25 ticks/s** | a `ReloadDelay: 21` is 0.84 s |
| Speed | world units per tick | `Speed: 113` = 113 wu/tick = 2.76 cells/s |
| Angle | `WAngle`, **1024 = 360°** | `TurnSpeed: 20` = 7.03°/tick; "facing units" in missile code are 256 = 360° |
| HP/damage | integer; yaml `HP: 5000` is 5000 | no hidden scaling |
| Percentages | `Versus`, `Falloff`, `TerrainSpeeds`, modifiers are integer % | multiply and integer-truncate |

`Util.ApplyPercentageModifiers(value, mods)` = `value * Π(mod_i/100)` (decimal, truncated to int).

---

## 1. The bots: `SquadManagerBotModule` and the squad state machines

### 1.1 Parameters (defaults from `OpenRA.Mods.Common/Traits/BotModules/SquadManagerBotModule.cs` L53-94, overrides from `mods/ra/rules/ai.yaml`)

| Parameter | Default (C#) | Rush (`ai.yaml` L335-344) | Normal (L398-410) | Turtle (L447-461) | Meaning (what the code does with it) |
|---|---|---|---|---|---|
| `SquadSize` | 8 | **20** | 40 | 10 | Minimum idle ground units before an attack squad forms; also minimum total ground troops before a rush is attempted (L423-425, L447) |
| `SquadSizeRandomBonus` | 30 | 30 | 30 | 30 | `randomizedSquadSize = SquadSize + Random.Next(SquadSizeRandomBonus)` re-rolled every evaluation (L423) → 20..49 for Rush |
| `AssignRolesInterval` | 50 | 50 | 50 | 50 | Ticks between `FindNewUnits` sweeps (new own units get a role) (L369-373) |
| `RushInterval` | 600 | 600 | 600 | **100000** | Ticks between `TryToRushAttack` attempts (L347-351). Initial value randomised to `[RushInterval-RushInterval/20, RushInterval+RushInterval/20]` = 570..629 (L195-196) |
| `AttackForceInterval` | 75 | 75 | 75 | 75 | Ticks between squad state-machine updates; updates are spread across the interval (L353-367) |
| `MinimumAttackForceDelay` | 0 | 0 | 0 | **100000** | Ticks between `CreateAttackForce` checks; 0 means **every tick** (L375-379) |
| `RushAttackScanRadius` | 15 (cells) | 15 | 15 | 15 | Radius around each enemy construction yard scanned for defenders when deciding a rush (L467) |
| `ProtectUnitScanRadius` | 15 (cells) | 15 | 15 | **30** | Existing squads whose first unit is within this many cells of an attacker of our base are retargeted onto the attacker (L505) |
| `MaxBaseRadius` | 20 (cells) | 20 | 20 | 20 | Only used by MCV deployment logic in other modules; **not used anywhere in SquadManager/squad code** |
| `IdleScanRadius` | 10 (cells) | 10 | 10 | 10 | `GroundUnitsIdleState`: enemies within this radius **of the squad's target position** are the "enemy units" fed to the fuzzy attack/flee decision |
| `DangerScanRadius` | 10 (cells) | 10 | 10 | 10 | `StateBase.ShouldFlee` and all air-squad danger checks scan this radius around the squad centre (must be > 0) |
| `AttackScanRadius` | 12 (cells) | 12 | 12 | 12 | `GroundUnitsAttackMoveState`: when regrouped, look for the closest enemy within this radius of the leader → `GroundUnitsAttackState` |
| `ProtectionScanRadius` | 8 (cells) | 8 | **12** | **15** | Protection squad: search radius around its leader for an enemy to attack when its target is gone |
| `IgnoredEnemyTargetTypes` | empty | `AirborneActor` | `AirborneActor` | `AirborneActor` | Enemy actors whose enabled target types overlap this are never squad targets (so flying `heli` is never targeted by any squad; a **landed** heli is `GroundActor, Vehicle` and *is*) |
| `AirUnitsTypes` | empty | `mig, yak, heli, hind, mh60` | same | same | Own actor types routed into the single Air squad |
| `NavalUnitsTypes` | empty | `ss, msub, dd, ca, lst, pt` | same | same | (not in our roster) |
| `ExcludeFromSquadsTypes` | empty | `harv, mcv, dog, badr.bomber, u2` | same | + `mnly` | never given a squad role |
| `ConstructionYardTypes` | empty | `fact` | `fact` | `fact` | Enemy base centre for rushes; own random base centre for retreats |
| `ProtectionTypes` | empty | all buildings + `harv, mcv` (list in `ai.yaml` L343) | same | same | Own actor types whose damage triggers base protection; **includes `fact, weap, barr, powr, hpad, gun, sam`** but **not `sbag`**, not units |
| `AircraftTargetType` | `Air` | `AirborneActor` | same | same | Target type used to decide "this enemy is anti-air" |
| `IdleBaseUnitsMaximum` | — | — | — | — | **Flag:** not a SquadManager parameter at this commit; it lives in `UnitBuilderBotModule.cs` L30 (production, out of scope) |

Also relevant, hard-coded: `MaxRespondToAttackCooldown = 30` ticks (L119); the "stuck" timeout `63` ticks in ground states; protection `BackoffTicks = 4` squad updates; `MissileUnitMultiplier = 3` for air squads.

Order delivery: bot modules do not issue orders directly; `IBot.QueueOrder` enqueues (`Traits/Player/ModularBot.cs` L81-83) and each tick the bot issues `ceil(queue/5)` of the queued orders (`MinOrderQuotientPerTick = 5`, L34, L101-103). So a batch of N orders drains over at most ~5 ticks.

### 1.2 Core helpers (what "enemy" and "target" mean)

`IsPreferredEnemyUnit(a)` (L159-169): `a` alive, owner relationship Enemy, not a `Husk`, enabled target types non-empty and not overlapping `IgnoredEnemyTargetTypes`, and visible to the bot (`IsNotHiddenUnit`; no cloak in our roster → always true).

`FindEnemies(actors, sourceActor)` (L253-291): of `actors` keep preferred enemies against which **sourceActor** has an enabled `AttackBase` with a weapon valid for that target (`HasAnyValidWeapons`); compute `range = max weapon range vs that target`; keep only those reachable: there must be a path from source to the target centre **or** to one of 8 points on the circle of radius `range` around it (axis-aligned and diagonal, diagonal = range·√2/2). Returns `(Actor, Offset)` where Offset is the reachable offset with the smallest length (usually `Zero` for land vs land).

`FindClosestEnemy(source)` = closest-by-straight-line (`ClosestToIgnoringPath`) of `FindEnemies(World.Actors, source)` (all actors in the world). `FindClosestEnemy(source, radius)` = same over `FindActorsInCircle(source.CenterPosition, radius)` (L293-306).

`Squad.SetActorToTarget((actor, offset))` (`Squads/Squad.cs` L80-93): `TargetActor = actor`; `Target = Target.FromActor(actor)` if offset is zero else `Target.FromPos(actor.CenterPosition + offset)`.

`Squad.IsTargetValid(squadUnit)` (L98-120): target actor exists, in world, alive, not a husk, and `Target.IsValidFor` some squad unit; then **re-evaluates** `FindEnemies([TargetActor], squadUnit)` (reachability from the given unit) and refreshes the target; returns false if it became unreachable.

`Squad.CenterPosition()` = average of unit positions; `CenterUnit()` = unit closest to it (L126-135).

`StateBase` (`Squads/States/StateBase.cs`):
- `GoToRandomOwnBuilding` (L22-27): `Move` order for every unit to `RandomBuildingLocation` = location of a random own `Building` actor, else `GetRandomBaseCenter()` (random own `fact` location, else the initial base centre).
- `BusyAttack(a)` (L40-59): unit not idle and its current or next activity is of type `Attack` (infantry) or `FlyAttack` (aircraft). **Note:** the turreted tank's attack activity is `AttackFollow.AttackActivity`, which is *not* `Attack`, so tanks in `GroundUnitsAttackState` are re-ordered every squad update even while fighting (harmless: it is an AttackMove to the same target).
- `CanAttackTarget(a, target)` (L61-81): `a` has an `AttackBase` and any enabled armament whose weapon `IsValidTarget(target's enabled target types)`.
- `ShouldFlee(squad, fleeFn)` (L83-104): take all actors within `DangerScanRadius` cells of the squad centre; **if any own `Building` is in that circle → never flee**; else enemies = preferred enemies that have an `AttackBase`; if none → don't flee; else `fleeFn(enemies)`.
- `IsRearming(a)` (L106-109): current activity chain contains `Resupply` or `ReturnToBase`.
- `FullAmmo(pools)` all pools full; `HasAmmo(pools)` all pools non-empty (L111-127).
- `ReloadsAutomatically(pools, rearmable)` (L129-139): true if no `Rearmable` trait, or every pool is listed in `Rearmable.AmmoPools`. For `heli` (Rearmable with default pool "primary", AmmoPool name "primary") this returns **true**, which has consequences for the air states (see §2).

### 1.3 Per-tick manager pseudo-code (`AssignRolesToIdleUnits`, L338-383)

```
on_enable():                                         # TraitEnabled L192-202
    rushTicks            = rand(RushInterval - RushInterval/20, RushInterval + RushInterval/20)   # 570..629
    assignRolesTicks     = rand(0, AssignRolesInterval)          # 0..49
    attackForceTicks     = rand(0, AttackForceInterval)          # 0..74
    minAttackForceDelay  = rand(0, MinimumAttackForceDelay)      # 0 for Rush
    respondToAttackCooldown = 30

every tick (BotTick):
    for s in squads: s.units.remove_where(dead or not in world or not ours)
    squads.remove_where(units.empty)
    activeUnits.remove_where(cannot be ordered)
    idleBaseUnits.remove_where(cannot be ordered)

    if --rushTicks <= 0:      rushTicks = RushInterval;          TryToRushAttack()
    if --attackForceTicks <= 0:
        attackForceTicks = AttackForceInterval
        push every squad onto squadsPendingUpdate
    # spread squad updates across the interval:
    updateCount = ceil(squadsPendingUpdate.count / attackForceTicks)
    repeat updateCount: pop squad; if valid: squad.Update()      # runs the state's Tick once
    if --assignRolesTicks <= 0: assignRolesTicks = AssignRolesInterval; FindNewUnits()
    if --minAttackForceDelay <= 0: minAttackForceDelay = MinimumAttackForceDelay; CreateAttackForce()
    if respondToAttackCooldown-- == 30: ProtectOwn(protectFrom)   # runs exactly once, the tick after RespondToAttack armed it
```

Each squad's state `Tick` therefore runs **once per 75 ticks (3 s)**; a squad created between pushes waits for the next push (up to 75 ticks).

**FindNewUnits** (L385-417): every own actor with `IPositionable` (units; buildings too, but buildings have no Mobile and are filtered by later logic — in practice only give roles to units) not in `ExcludeFromSquadsTypes` and not yet in `activeUnits`:
- in `AirUnitsTypes` → added to the single Air squad (created if missing);
- in `NavalUnitsTypes` → Naval squad;
- else → `unitsHangingAroundTheBase` (the idle pool). Added to `activeUnits`.

Note the idle pool is never given orders by the manager itself: idle units stand where they were produced, auto-targeting (§3), until they are grabbed by `CreateAttackForce`, `TryToRushAttack`, or `ProtectOwn`.

**CreateAttackForce** (L419-435), Rush: evaluated **every tick**:
```
n = SquadSize + rand(0, SquadSizeRandomBonus)     # 20..49, new roll each tick
if idleBaseUnits.count >= n:
    squad = new Squad(Assault); squad.units = idleBaseUnits; idleBaseUnits.clear()
```
Because the roll repeats each tick, with `k ≥ 20` idle units the per-tick probability of forming is `(k-19)/30`; at 20 idle units expect ~30 ticks, at 30 ~3 ticks, at ≥ 49 immediately. No units are kept back for defence ("don't bother leaving any behind").

**TryToRushAttack** (L437-495), every `RushInterval`:
```
groundTroops = idleBaseUnits.count + Σ units of valid non-Air/non-Naval squads
if groundTroops < SquadSize: return
probe = random idle unit having an AttackBase; if none: return
enemyCYs = FindEnemies(all enemy 'fact' actors, probe)            # reachable, attackable
if empty: return
for cy in enemyCYs:
    defenders = FindEnemies( actors within RushAttackScanRadius(15c) of cy
                             that have an AttackBase and are not Air/Naval types, probe )
    if AttackOrFleeFuzzy.Rush.CanAttack(idleBaseUnits, defenders):
        target = defenders.empty ? cy : random(defenders)
        for every valid squad: squad.SetActorToTarget(target)      # ALL squads, incl. Air and Protection
        rush = squad of type Rush or new Squad(Rush, target)
        rush.units += idleBaseUnits; idleBaseUnits.clear()
        return
```
A rush retargets every existing squad (including the Air squad) onto one enemy; the Rush squad itself runs the same ground state machine as Assault (Squad.cs L56-62).

**Base protection** (`RespondToAttack` L549-559, `ProtectOwn` L497-540):
```
on own actor `self` damaged by `attacker` (ModularBot forwards every damage event on our actors):
    if respondToAttackCooldown > 0: ignore
    if self.type not in ProtectionTypes: ignore           # buildings (not sbag), harv, mcv
    if not IsPreferredEnemyUnit(attacker): ignore         # so an airborne heli attacking never triggers it (AirborneActor ignored)
    respondToAttackCooldown = 30; protectFrom = attacker

ProtectOwn(attacker):            # next tick
    if not IsPreferredEnemyUnit(attacker): return
    for s in valid squads:
        if FindEnemies([attacker], s.units.first).any()           # first unit can attack & reach it
           and |s.units.first.cell - attacker.cell|² <= ProtectUnitScanRadius²   # 15 cells
            s.SetActorToTarget(attacker)                          # existing squads swing onto the attacker
    protect = squad of type Protection or new Squad(Protection, attacker)
    for a in idleBaseUnits:
        if a has Mobile and FindEnemies([attacker], a).any(): move a into protect
        (aircraft not in AirUnitsTypes also go; others stay idle)
    if protect.valid and !protect.IsTargetValid(protect.CenterUnit()): protect.SetActorToTarget(attacker)
```
After the response the cooldown counts down 30 ticks before another attack can arm it, so base defence re-evaluates at most every ~31 ticks.

### 1.4 Ground squad state machine (`Squads/States/GroundStates.cs`; Assault, Rush and Naval squads)

`GroundStateBase` (L18-79):
- **Leader** (L26-31, `NewLeader` L33-55): elected once and kept while in the squad; among units with the most restrictive locomotor (fewest `TerrainSpeeds` entries; `foot` and `tracked` both have 7 entries in RA, so no filtering for our roster) pick the unit closest to the squad's average position. `NewLeaderAndFindClosestEnemy` (L62-66) forces a re-election then calls `FindClosestEnemy(leader)` over the whole world.
- `ShouldFlee(owner)` (L57-60) = `StateBase.ShouldFlee(owner, enemies => !AttackOrFleeFuzzy.Default.CanAttack(owner.Units, enemies))`.

States and their `Tick` (each runs once per 75 ticks):

**GroundUnitsIdleState** (L81-119) — initial state of a new squad:
```
if !IsTargetValid(Leader):
    t = NewLeaderAndFindClosestEnemy(); SetActorToTarget(t)
    if t.Actor == null: return                                    # nothing attackable anywhere: squad sits idle
enemyUnits = FindEnemies(owner, actors within IdleScanRadius(10c) of Target.CenterPosition)   # includes the target itself
if enemyUnits.empty: return
if AttackOrFleeFuzzy.Default.CanAttack(units, enemyUnits):
    order AttackMove(Target) for all units (one grouped order)
    state = GroundUnitsAttackMoveState
else:
    state = GroundUnitsFleeState
```
**GroundUnitsAttackMoveState** (L121-196):
```
if !IsTargetValid(Leader):
    t = NewLeaderAndFindClosestEnemy(); SetActorToTarget(t)
    if t.Actor == null: state = Flee; return
if leader.cell != lastLeaderCell: lastLeaderCell = leader.cell; lastUpdatedTick = now
if TargetActor != lastTarget:     lastTarget = TargetActor;     lastUpdatedTick = now
if now > lastUpdatedTick + 63: state = Idle; return     # "stuck" guard: leader did not change cell between two squad updates
near = units within (units.count / 3) cells of the leader         # WDist.FromCells(count)/3
if near.count < units.count:
    order Stop(leader)
    order AttackMove(leader.cell) for the stragglers (grouped)      # regroup on the leader
else:
    t = FindClosestEnemy(leader, AttackScanRadius 12c)
    if t.Actor != null: SetActorToTarget(t); state = GroundUnitsAttackState
    else: order AttackMove(Target) for all units
if ShouldFlee(): state = Flee
```
**GroundUnitsAttackState** (L198-253):
```
(same target-validity and stuck checks as above; stuck → Idle)
for a in units: if !BusyAttack(a): order AttackMove(a, Target)   # one order per unit
if ShouldFlee(): state = Flee
```
**GroundUnitsFleeState** (L255-269): `GoToRandomOwnBuilding(); state = Idle`; on leaving the state `UnregisterSquad` empties the squad and removes its units from `activeUnits`, so they are re-discovered by the next `FindNewUnits` as new idle base units.

Behavioural summary: a squad walks (attack-moving, so it engages anything in weapon range on the way, see §3) towards the **closest reachable enemy actor to its leader** (any type: unit, building, defence, wall is excluded only because `sbag` has `NoAutoTarget`… no — squads use `IsPreferredEnemyUnit`, which does *not* check `NoAutoTarget`; a wall is a valid squad target if it is the closest. Flag for tuning: you may want to exclude `Wall` from squad targets). When 12 cells from an enemy it locks onto the closest one and keeps re-issuing attack-moves to it. It retreats to a random own building when the fuzzy comparison in a 10-cell circle around its centre says so, unless an own building is within that circle. Whenever a squad's leader stops changing cells for ≥ 64 ticks (arrived, blocked, or fighting in place) the squad drops to Idle and immediately re-evaluates on its next update.

"AttackMove" order semantics (`Traits/AttackMove.cs` L82-100): target cell = cell containing the target's centre, clamped to map; destination = `NearestMoveableCell(cell)`; queue `AttackMoveActivity(MoveTo(dest, nearEnough = 8 cells))`. **Units stop once within 8 cells of the ordered cell** (`Move` with `nearEnough` 8*1024); the rest is done by auto-targeting.

### 1.5 Protection squad state machine (`Squads/States/ProtectionStates.cs`)

- `UnitsForProtectionIdleState` (L16-20): immediately → `UnitsForProtectionAttackState`.
- `UnitsForProtectionAttackState` (L23-67):
```
leader = Leader()
if !IsTargetValid(leader):
    t = FindClosestEnemy(leader, ProtectionScanRadius 8c)
    SetActorToTarget(t); if t.Actor == null: state = Flee; return
order AttackMove(Target) for all units (grouped)
if !IsTargetVisible:                        # target not viewable by the bot player
    if Backoff < 0: state = Flee; Backoff = 4; return
    Backoff--
else: Backoff = 4
```
- `UnitsForProtectionFleeState` (L69-83): `GoToRandomOwnBuilding(); state = Idle`; `Deactivate` → `UnregisterSquad` (units return to the idle pool).

So defenders chase the attacker; when it dies they pick the closest enemy within 8 cells of their leader; when nothing is near they walk back to a random own building and dissolve.

### 1.6 Attack-or-flee fuzzy logic (`Squads/AttackOrFleeFuzzy.cs`)

Inputs (L167-183):
- `OwnHealth`, `EnemyHealth` = `Σ HP / Σ MaxHP * 100` over actors with health (int, L185-203).
- `RelativeAttackPower` = `Σown power / Σenemy power * 100`, clamped 0..999; `999` if enemy set empty, `0` if own set empty (L205-227, L234-245). Per-actor power (L217-225): for each `Armament`: `totalReload = ReloadDelay + clamp(BurstDelays[0]*(Burst-1), 1, 200)`; for each `DamageWarhead`: `power += Damage * Burst / totalReload * 100` (integer division before ×100). Only actors with `AttackBaseInfo` count.
- `RelativeSpeed` = `avg(own Mobile.Speed) / avg(enemy Mobile.Speed) * 100`, clamped 0..999, only actors with `Mobile` (buildings, aircraft excluded). **Edge case:** if the enemy set has no Mobile actor the average is 0 → float division gives +∞ → clamp → 999 ("Fast"); if own has none → 0 ("Slow").

Roster power values (RA numbers): `e1` M1Carbine 1000·1/20·100 = **5000**; `1tnk` 25mm 2500/21=119 → **11900**; `gun` TurretGun 6000/30=200 → **20000**; `sam` Nike 4500/15=300 → **30000**; `heli` HellfireAA 3000·2/40=150 → 15000 + HellfireAG 6000·2/44=272 → 27200 = **42200**.

Membership functions (trapezoids `(a,b,c,d)`, L124-151):
- OwnHealth/EnemyHealth ∈ [0,100]: `NearDead (0,0,20,40)`, `Injured (30,50,50,70)`, `Normal (50,80,100,100)`.
- RelativeAttackPower/RelativeSpeed ∈ [0,1000]: `Weak (0,0,70,90)`, `Equal (85,100,100,115)`, `Strong/Fast (110,150,150,1000)`.
- Output AttackOrFlee ∈ [0,50]: `Attack (0,15,15,30)`, `Flee (25,35,35,50)`.
- Decision: Mamdani inference, result = centroid; `CanAttack = !NaN && result < 30.0` (L182). The fuzzy library is the NuGet package `OpenRA-FuzzyLogicLibrary 1.0.1` (not in tree); its Mamdani defaults are AND=min, OR=max, implication=min, aggregation=max, defuzzification=centroid — **flag: library source not in this checkout, defaults assumed**.

Rules. `Default` (L23-97): 
- Normal own health: Attack for every combination (1 rule).
- Injured: Attack if enemy NearDead; Attack if enemy Injured/Normal and power Equal/Strong; Attack if enemy Injured/Normal, power Weak and speed Slow; **Flee** if enemy Injured/Normal, power Weak and speed Equal/Fast; Attack for any enemy health/any power if speed Slow.
- NearDead: Attack if enemy NearDead/Injured and power Equal/Strong and speed Slow/Equal; Flee if enemy NearDead/Injured, power Weak, speed Equal/Fast; Flee if enemy Normal, power Weak, speed Equal/Fast; Flee if enemy Normal, power Equal/Strong, speed Fast; Flee if enemy Injured, power Equal, speed Fast.

`Rush` (L99-112) replaces only the Normal-own-health rules: Attack if power **Strong**; Flee if power Weak/Equal (Injured/NearDead rules are the defaults).

Crisp approximation that is faithful enough to port (document the deviation in your code):
```
func default_can_attack(ownHp, enemyHp, power, speed):   # percentages
    if ownHp >= 70: return true
    if ownHp > 40:                                       # "Injured" band
        if enemyHp < 30: return true
        if power >= 95: return true
        if speed <= 80: return true
        return false                                      # weak and not slower
    # NearDead
    if enemyHp < 60 and power >= 95 and speed <= 105: return true
    return false

func rush_can_attack(ownHp, enemyHp, power, speed):
    if ownHp >= 70: return power > 112                   # Strong membership > Equal membership
    return default_can_attack(ownHp, enemyHp, power, speed)
```
Note that `TryToRushAttack` with no defenders near the enemy `fact` gives power 999 and enemyHp 0 → always attack when own units are healthy.

---

## 2. Air squads (`Squads/States/AirStates.cs`)

One Air squad per bot holds every own `heli` (alive). It is created the first time a heli is found by `FindNewUnits` (every 50 ticks) and updated once per 75 ticks like any squad. In our game aircraft only exist on pads until a bass note launches them; see §2.5 for the mapping.

### 2.1 Helpers (`AirStateBase`, L18-81)

`CountAntiAirUnits(squad, actors)` (L22-50): count of actors that are **not aircraft** and have an enabled, unpaused `AttackBase` with any armament whose weapon `IsValidTarget(AircraftTargetType = AirborneActor)`. In our roster only **`sam`** counts (Nike valid vs `AirborneActor`); `e1`, `1tnk`, `gun` never do. (`heli`'s HellfireAA would, but aircraft are skipped.)

`NearToPosSafely(squad, pos, out target)` (L52-74): `near = preferred enemies within DangerScanRadius (10c) of pos`; if none → safe, target null; if `CountAntiAirUnits(near) * 3 < squad.Units.Count` → safe, `target = random(near)`; else unsafe.

`ShouldFlee` (L77-80) = `StateBase.ShouldFlee(squad, enemies => CountAntiAirUnits(enemies) * 3 > squad.Units.Count)` — i.e. flee when, within 10 cells of the squad centre, there is no own building and `3 × (#SAMs) > #helis`. With at most 5 helis per side: 1 SAM in range makes a squad of ≤ 2 flee; 2 SAMs make any squad flee (3·2 = 6 > 5).

### 2.2 `AirIdleState` (L83-159)

On `Activate`: build a shuffled list of grid cells: the map is divided into a grid of side `dangerRadius*141/100` (= 14 cells for radius 10); `columnCount = ceil(mapWidth/14)`, `rowCount = ceil(mapHeight/14)`; `airStrikeCheckIndices` = shuffled `[0 .. columns*rows)`. (**Flag:** the probe position is computed with `index % columns * dangerRadius + dangerRadius/2` — i.e. spaced 10 cells not 14, and in map-local `MPos` without adding `map.Bounds.X/Y` — a quirk in the source; replicate or simply probe a 10-cell lattice over the playable area.)

`Tick`:
```
if ShouldFlee(): state = AirFleeState; return
e = FindDefenselessTarget(); if e == null: return
SetActorToTarget((e, Zero)); state = AirAttackState
```
`FindDefenselessTarget` (L108-137): up to 3 lattice points per tick (`MaxCheckTimesPerTick = 2`, loop `<=`), advancing `checkedIndex` (wrapping):
```
pos = centre of lattice cell
if CountAntiAirUnits(actors on the line from squad centre to pos, width 10c) * 3 >= units.count: continue   # (note: condition is `< count → continue`, see flag)
if NearToPosSafely(pos, out enemy):
    if enemy == null: continue
    checkedIndex = random index
    return enemy
return null
```
**Flag (source quirk, L122-124):** the line check reads `if (CountAntiAirUnits(onLine) * 3 < Units.Count) continue;` — it *skips* lattice points whose approach path is **safe** and only proceeds when the path has enough AA to be dangerous (`AA*3 >= count`). Then `NearToPosSafely` requires the destination circle itself to be safe. Net effect in practice: with zero AA anywhere the line check always `continue`s and the air squad **never finds a target from this scan**; it only attacks through (a) `TryToRushAttack` retargeting every squad (incl. Air) onto the rush target, or (b) `ProtectOwn` retargeting squads within 15 cells of an attacker. Those set `TargetActor` directly but the Air squad stays in `AirIdleState` until… nothing moves it to `AirAttackState` except `FindDefenselessTarget`. So at this commit the AI air squad is effectively passive unless an enemy AA presence makes the quirky line test pass. **Recommendation for our game:** implement the obviously intended logic (`continue` when the line has *too much* AA, i.e. `AA*3 >= count`), and state in code that it deviates from `e7e9e4ad`.

### 2.3 `AirAttackState` (L161-206)

```
leader = CenterUnit()
if !IsTargetValid(leader):
    t = FindClosestEnemy(leader)                     # whole world, leader must have a valid weapon & reach (aircraft: always reachable)
    SetActorToTarget(t); if t.Actor == null: state = Flee; return
closest = unit closest to TargetActor
if !NearToPosSafely(closest.CenterPosition): state = Flee; return     # AA*3 >= count within 10c of our closest heli → flee
for a in units:
    if BusyAttack(a) or IsRearming(a): continue      # already FlyAttack-ing / resupplying
    pools = a.AmmoPools
    if !ReloadsAutomatically(pools, a.Rearmable) and !HasAmmo(pools): order ReturnToBase(a); continue
    if CanAttackTarget(a, TargetActor): order Attack(a, Target)
```
For `heli` `ReloadsAutomatically` is **true** (its only pool is in `Rearmable.AmmoPools`), so the explicit `ReturnToBase` branch never fires; empty helis are instead sent home by `FlyAttack` itself (§3.6). `CanAttackTarget` is true for any ground target (HellfireAG valid vs `GroundActor`) and for airborne targets (HellfireAA), but `IgnoredEnemyTargetTypes: AirborneActor` means squads never select airborne targets in the first place.

### 2.4 `AirFleeState` (L208-237)

```
for a in units:
    if IsRearming(a): continue
    if !ReloadsAutomatically(...) and !FullAmmo(pools): order ReturnToBase(a); continue      # never for heli (see above)
    order Move(a, RandomBuildingLocation())        # fly to a random own building
state = AirIdleState
```
So RA helis flee by flying over a random own building; they rearm only when `FlyAttack` sends them (out of ammo) or when the player/bot gives `ReturnToBase`.

### 2.5 Mapping to our game (take-off only on a successful bass note)

- Keep the Air squad bookkeeping, `CountAntiAirUnits`, `NearToPosSafely`, `ShouldFlee`, and the three states exactly, but gate **order issue** on airborne status: a heli sitting on its pad is not airborne (altitude 0 < `MinAirborneAltitude 1`), its `Attack` order would normally queue `TakeOff` first (`FlyAttack` L161). In our game: an `Attack`/`Move` order to a landed heli is deferred until the bass note; on the note, run `TakeOff` (vertical climb §3.6) and then the deferred `FlyAttack`.
- Everything after take-off applies unchanged: flee checks, target choice, the per-unit `Attack` order, `FlyAttack` range/hover/facing logic, running out of ammo → `ReturnToBase` → land on a free `hpad` → rearm 1 ammo / 50 ticks → `TakeOffOnResupply` (in our game: stay landed until the next bass note instead).
- The pad limit (5 pads/5 aircraft) replaces `Reservable`: a heli returning to base picks the closest own `hpad` not reserved by another heli (`ReturnToBase.ChooseResupplier`, `Activities/Air/ReturnToBase.cs` L26-37); if none is free it flies to within `WaitDistanceFromResupplyBase` 4c0 of the nearest pad at a random offset and hovers (L63-79), re-checking every update.

---

## 3. Unit combat semantics for the roster

### 3.1 Stats (`mods/ra/rules/*.yaml`)

| Actor | HP | Armor | Move Speed (wu/tick) | Body TurnSpeed | Locomotor | Weapons (Armament → weapon) | Attack trait |
|---|---|---|---|---|---|---|---|
| `e1` (`infantry.yaml` L71-104, `^Soldier` `defaults.yaml` L445-460, `^Infantry` L320-443) | 5000 | None | 54 | 512 (default = instant; `AlwaysTurnInPlace`) | foot | primary → `M1Carbine` (garrisoned `Vulcan` is a separate armament name, unused outside transports) | `AttackFrontal` FacingTolerance 0 |
| `1tnk` (`vehicles.yaml` L54-91, `^Vehicle` L237-313, `^TrackedVehicle` L315-318) | 23000 | Heavy | 113 | 20 (7.0°/tick) | tracked | primary → `25mm`, `LocalOffset 768,0,90`, `Recoil 85`, `RecoilRecovery 25`, `MuzzleSequence muzzle` | `AttackTurreted` (turret TurnSpeed 28, `RealignDelay` default 40) |
| `heli` (`aircraft.yaml` L273-353, `^Helicopter` L664-682, `^NeutralPlane` L582-655) | 12000 | Light | 149 (Aircraft.Speed) | 16 (Aircraft.TurnSpeed) | air: VTOL, CanHover, CanSlide, CruiseAltitude 1280, AltitudeVelocity 43, MaximumPitch 10°, IdealSeparation 1706, LandableTerrainTypes Clear/Rough/Road/Ore/Beach/Gems, Crushes crate/mine/infantry | PRIMARY → `HellfireAA` offsets `0,-213,-85 / 0,213,-85`; SECONDARY → `HellfireAG` offsets `0,213,-85 / 0,-213,-85`; both `PauseOnCondition: !ammo`; `AmmoPool Ammo 8` | `AttackAircraft` FacingTolerance 80, AttackType Hover, PersistentTargeting false, OpportunityFire false; `AutoTarget InitialStance/InitialStanceAI: HoldFire` |
| `gun` (`structures.yaml` L834-882, `^Defense` L777-794) | 40000 | Heavy | — | — | — | primary → `TurretGun`, `LocalOffset 512,0,112`, `MuzzleSequence muzzle` | `AttackTurreted`, turret TurnSpeed 48, InitialFacing 192, RealignDelay -1 |
| `sam` (L928-983) | 40000 | Heavy | — | — | — | primary → `Nike`, `LocalOffset 0,0,320`, `MuzzleSequence muzzle` | `AttackTurreted`, turret TurnSpeed 120, RealignDelay -1 |
| `fact` (L1152-1259) | 150000 | Wood | footprint 3×3 (+ bib row) | | | | |
| `weap` (L1039-1150) | 150000 | Wood | 3×2 (+ bib) | | | | |
| `barr` (L1767-1830) | 60000 | Wood | 2×2 (+ bib) | | | | |
| `powr` (L1650-1689) | 40000 | Wood | 2×2 (+ bib) | | | | |
| `hpad` (L1401-1460) | 80000 | Wood | 2×2 (+ bib); `Exit SpawnOffset 0,-256,0 Facing 896`; `Reservable`; `WithResupplyAnimation` | | | | |
| `sbag` (L2081-2101, `^Wall` L796-844) | 15000 | Wood | 1×1; `Crushable CrushClasses: wall`; `Targetable: GroundActor, DetonateAttack, Wall, NoAutoTarget` | | | | |

Target types: infantry `GroundActor, Infantry`; vehicles `GroundActor, Vehicle`; heli landed `GroundActor, Vehicle`, airborne `AirborneActor` (only!); buildings `GroundActor, C4, DetonateAttack, Structure` (+`Defense` for gun/sam); wall adds `Wall, NoAutoTarget`.

Terrain speeds (`mods/ra/rules/world.yaml` L12-23 foot, L57-67 tracked): foot Clear 100, Rough 89, Road 111, Bridge 111, Ore/Gems/Beach 89; tracked Clear 100, Rough 88, Road 125, Bridge 125, Ore/Gems/Beach 88. Crushes: foot `mine, crate`; tracked `wall, infantry, mine, crate` → **`1tnk` crushes `e1` and `sbag`** (helicopters also list infantry but cannot land on them in practice). Per-tick movement = `Speed * terrain% * Σ modifiers` (`Mobile.MovementSpeedForCell`, `Traits/Mobile.cs` L760-766); prone infantry ×50%.

Derived: `e1` 1.32 cells/s (Clear); `1tnk` 2.76 cells/s Clear, 3.45 on road; `heli` 3.64 cells/s. `1tnk` 360° body turn = 52 ticks; turret 180° = 19 ticks; `gun` turret 180° = 11 ticks; `sam` 180° = 5 ticks; `heli` 180° = 32 ticks. No acceleration anywhere (speed is applied in full from the first tick).

### 3.2 Weapons (`mods/ra/weapons/*.yaml`)

Common warhead semantics first:
- `SpreadDamage` (`Warheads/SpreadDamageWarhead.cs`): `Spread` default 43, `Falloff` default `[100, 37, 14, 5, 0]` at distances `[0, Spread, 2·Spread, 3·Spread, 4·Spread]` (linear interpolation between, `GetDamageFalloff`). Victims: every actor within `4·Spread` of the impact (`FindActorsOnCircle`); distance = distance from impact to the victim's closest **HitShape edge** (`DamageCalculationType.HitShape`), so a hit inside the shape is distance 0 = 100%. `damage = Damage × falloff% × Versus[armor]% × (prone etc.)` (`DamageWarhead.InflictDamage`, `Warheads/DamageWarhead.cs` L72-90); a missing `Versus` entry for an armour type means 100%. Warhead `ValidTargets`/`InvalidTargets` are matched against the victim's target types.
- `CreateEffect` (`Warheads/CreateEffectWarhead.cs`): picks a **random** entry of `Explosions` (L114), spawns it as a sprite effect from image `Image` (default **`explosion`**, L30) at the impact (`ImpactActors` decides whether the impact "sees" actors; `ForceDisplayAtGroundLevel` false).
- `LeaveSmudge` (`Warheads/LeaveSmudgeWarhead.cs` L34-71): with `Chance` 100, if the impact is ≤ `AirThreshold` 128 above ground, adds one smudge of `SmudgeType` to the impact cell (`Size [0,0]` = that cell only) if the terrain accepts it and no actor in the cell is invalid for the warhead. The `SmudgeLayer` (`world.yaml` L186-199): `Crater` uses sequence `craters` (random `cr1..cr6`), 25% chance of a `smoke_m idle` plume; `Scorch` uses `scorches` (`sc1..sc6`), 50% `scorch_flames`.
- Weapon-level `ValidTargets` (`OpenRA.Game/GameRules/WeaponInfo.cs` L107-116): weapon can target an actor if its enabled target types overlap `ValidTargets` and not `InvalidTargets`.

| Weapon (file:lines) | ReloadDelay | Burst / BurstDelays | Range / MinRange | Projectile | Damage warhead | Effects |
|---|---|---|---|---|---|---|
| `M1Carbine` (`smallcaliber.yaml` L256-284; inherits `^LightMG` L77-96 ← `^HeavyMG` L51-76) | 20 | 1 / [5] | 5c0 / 0 | `InstantHit`, `Blockable: true` (walls/blocking actors stop it) | Damage 1000, Spread 128, Versus None 150, Wood **30**, Light 40, Heavy 10, Concrete 10; DamageTypes `Prone50Percent, TriggerProne, DefaultDeath`; valid vs GroundActor/WaterActor | `piff` three times (delay 0, 2, 4 ticks) with Inaccuracy 171 (each piff is scattered randomly up to 171 wu); on water `water_piff` |
| `25mm` (`ballistics.yaml` L33-50 ← `^Cannon` L1-31) | **21** | 1 / [5] | **4c768** / 0 | `Bullet` Speed 853 wu/tick, Image `50CAL`, Shadow true, Inaccuracy 0, Blockable true (default), LaunchAngle 0 | Damage 2500, Spread 128, Versus None 32, Wood 52, Light 116, Heavy 48, Concrete 32; DamageTypes `Prone50Percent, TriggerProne, ExplosionDeath` | `small_explosion` (ground), `small_splash` (water); **no smudge** (`-Warhead@2Smu`), no impact sound |
| `TurretGun` (`ballistics.yaml` L80-88 ← `^Cannon`) | 30 | 1 / [5] | **6c512** / 0 | `Bullet` Speed 682, Image `120MM`, Shadow true | Damage 6000, Spread 128, Versus None 20, Wood 50, Light 75, Concrete 50, Heavy (unset → 100); `ExplosionDeath` | `LeaveSmudge Crater` (vs Ground, Infantry), `small_explosion` + `kaboom12.aud` |
| `HellfireAG` (`missiles.yaml` L78-95 ← `^AntiGroundMissile` L1-39) | 34 | **2** / [10] | 5c0 / **1c256** | `Missile` Speed 256, Acceleration 5 (default), HorizontalRateOfTurn 40, VerticalRateOfTurn 24 (default), RangeLimit 8c512, Inaccuracy 128 (Absolute), Image `DRAGON`, Shadow, Arm 2, Blockable false, ContrailLength 10, CloseEnough 298 (default) | Damage 6000, Spread 128, Versus None 30, Wood 90, Light 90, Heavy 100, Concrete 100; `ExplosionDeath`; valid vs GroundActor/WaterActor | `LeaveSmudge Crater`, `med_explosion` + `kaboom25.aud` |
| `HellfireAA` (`missiles.yaml` L96-114 ← `^AntiAirMissile` L41-50) | 30 | 2 / [10] | **4c0** / 1c256 | `Missile` Speed 492, HRoT 100, RangeLimit 7c0, Inaccuracy 128, CloseEnough 600, Image `DRAGON` | Damage 3000, Spread 128, Versus **Light 100** only (others unset → 100); valid vs **AirborneActor** only | `med_explosion_air`, ImpactActors false |
| `Nike` (`missiles.yaml` L142-158 ← `^AntiAirMissile`) | **15** | 1 / [5] | **7c512** / 0c512 | `Missile` Speed 341, Arm 3, Inaccuracy 0, HRoT 100, RangeLimit 11c0, Image `MISSILE` | Damage 4500, Spread 128, vs AirborneActor only | `med_explosion_air` + `kaboom25.aud` |
| `ZSU-23` (`smallcaliber.yaml` L17-21 ← `^AACannon` L1-15) | 6 | 2 / [0] | 10c0 | `InstantHit` | Damage 900, Spread 213, `Prone50Percent, TriggerProne, DefaultDeath`, vs AirborneActor | `small_explosion_air` |
| `FireballLauncher` (`other.yaml` L25-35 ← `^FireWeapon` L1-24) | 70 | 2 / [20] | 5c0 | `Bullet` Speed 250, Image `FB1`, TrailImage `fb2` | Damage 15000, Spread 213, Versus None 90, Wood 50, Tree 50, Light 50, Heavy 25, Concrete 20; `Prone50Percent, TriggerProne, FireDeath, Incendiary` | `LeaveSmudge Scorch` (not on Structure/Wall), `napalm` + `firebl3.aud`, ImpactActors false |

Firing cadence (`Traits/Armament.cs`, `CheckFire`/`UpdateBurst`): a weapon may fire when `FireDelay == 0`, turret (if any) has reached its desired facing exactly, target within `[MinRange, MaxRange]` (2D horizontal distance to any of the target's targetable positions; `Target.IsInRange`, `OpenRA.Game/Traits/Target.cs` L196-203) and the weapon is valid against the target. After each shot: if shots remain in the burst `FireDelay = BurstDelays[...]`, else `FireDelay = ReloadDelay` (≥1) and the burst resets. Barrel used: if `Burst == 1` cycle through `LocalOffset` entries, else `Barrels[Burst % Barrels.Length]` (heli: alternate the two pylons within a burst). The projectile is created `Armament.FireDelay` (0 for all roster units) ticks later; `Report` sound plays then. Each shot consumes `AmmoUsage 1` from the pool listed for that armament (`AmmoPool.Attacking`). The heli's single pool "primary" serves both armaments (`AmmoPool.Armaments` default `primary, secondary`), so one 2-missile burst costs 2 ammo and a full load of 8 is **4 bursts in total** (AG and AA combined), after which both armaments are paused (`PauseOnCondition: !ammo`).

Projectiles:
- `InstantHit`: resolves immediately on the target position; `Blockable` true for M1Carbine means `BlocksProjectiles` actors (walls) on the line stop it (sbag has no `BlocksProjectiles` in `^Wall` at this commit → bullets pass over sandbags; flag if your walls should block).
- `Bullet` (`Projectiles/Bullet.cs` L190-262): target point = target's closest targetable position (+ random inaccuracy offset scaled by distance/MaxRange for `InaccuracyType.Maximum`; 0 for 25mm/TurretGun). `length = max(dist / Speed, 1)` ticks; position lerps (quadratic arc with LaunchAngle 0 ⇒ straight). Explodes when `ticks >= length`, or earlier if `Blockable` and a blocking actor is between last and current position. Draws `Image` sequence `idle` facing the flight direction; `Shadow` draws a black copy at ground level.
- `Missile` (`Projectiles/Missile.cs`): launched at `Speed` with facing = muzzle facing, homes on the guided target each tick: horizontal facing turns by at most `HorizontalRateOfTurn` **facing units (256 = 360°)** per tick (HRoT 40 = 56°/tick; 100 = 141°/tick), vertical by `VerticalRateOfTurn` 24; speed accelerates by `Acceleration` 5/tick up to `Speed`; passive target gets `Inaccuracy` (Absolute) random offset at launch. Explodes when within `CloseEnough` of the target (298 wu AG / 600 AA), when it hits the ground, or after flying `RangeLimit` (fuel). Cannot explode before `Arm` ticks (2 / 3). `ContrailLength 10` draws a fading white trail; `TrailImage` (smokey) only on `Dragon` (not Hellfire).

Rough damage table (full falloff, no prone): M1Carbine vs e1 **1500** (4 shots kill, 1.6 s); vs 1tnk 100; vs buildings 300. 25mm vs e1 800 (7 shots), vs 1tnk 1200 (20 shots), vs heli(Light) 2900 (but cannot target airborne), vs buildings 1300. TurretGun vs e1 1200, vs 1tnk 6000 (4 shots), vs buildings 3000. HellfireAG vs e1 1800/missile, vs 1tnk 6000/missile, vs buildings 5400/missile. Nike vs airborne heli 4500 (3 hits). Prone infantry take 50% from `Prone50Percent` weapons (all of the above).

### 3.3 Auto-targeting (`Traits/AutoTarget.cs`, `Traits/AutoTargetPriority.cs`)

Stances: `HoldFire < ReturnFire < Defend < AttackAnything`. Initial stance: human-owned `InitialStance` (default **Defend**), bot-owned `InitialStanceAI` (default **AttackAnything**) (L52-55, L190). `heli` overrides both to **HoldFire** (`aircraft.yaml` L311-313). `AllowMove = AllowMovement && Stance > Defend` (L146) → bot ground units may move to engage; human Defend units may not.

Stance conditions (`defaults.yaml` L177-223): `^AutoTargetGround`/`^AutoTargetGroundAssaultMove` (e1, 1tnk, gun) grant `stance-attackanything` while in AttackAnything; `AutoTargetPriority@DEFAULT` (`!stance-attackanything && !assault-move`): `ValidTargets: Infantry, Vehicle, Ship, Underwater, Defense, Mine`, `InvalidTargets: NoAutoTarget`; `@ATTACKANYTHING` (`stance-attackanything || assault-move`) adds **`Structure`**. `^AutoTargetAir` (sam): `AirborneActor`, Invalid `NoAutoTarget`. `^AutoTargetAllAssaultMove` (heli): both ground and air lists. All priorities use the default `Priority = 1` (`AutoTargetPriority.cs` L30) → **no type preference; the closest valid target wins** (L459-465: higher priority, else shorter range). Consequence: bot (AttackAnything) units auto-engage buildings; human Defend units auto-engage units and defences (gun/sam) but **not** plain buildings unless Assault-moving (Ctrl). Sandbags (`NoAutoTarget`) are never auto-targeted by anyone.

Scan cadence: `MinimumScanTimeInterval 3`, `MaximumScanTimeInterval 8` → after each scan wait `rand(3, 8)` = 3..7 ticks (L80-83, L304). Scan range: `ScanRadius` -1 ⇒ `AttackBase.GetMaximumRange()` = max armament range (L312) → e1 5c, 1tnk 4c768, gun 6c512, sam 7c512, heli 5c (AG) — `FindActorsInCircle(self.CenterPosition, range)` (L365).

`ChooseTarget` filter per candidate (L376-467): must appear hostile; not `PreventsAutoTarget`; visible; at least one `AutoTargetPriority` whose relationship and target types match; `ChooseArmamentsForTarget` non-empty (weapon valid vs target); if `!allowMove` also require target inside `[MinRange, MaxRange]` of some armament; if `!allowTurn` require it inside the firing arc (`FacingTolerance`).

When scans happen:
- **Idle** (`TickIdle`, L277-284): every tick while idle, if `ScanOnIdle` and stance ≥ Defend: `ScanAndAttack(AllowMove, allowTurn = Stance > HoldFire)` → on success `AttackBase.AttackTarget(target, AutoTarget, queued=false, allowMove)`.
- **Damaged** (L224-275): if idle, stance ≥ ReturnFire, damage > 0, attacker exists: if no override target: if `!AllowMove` the attacker must be visible; must have a valid weapon vs the attacker; not friendly. If stance > ReturnFire first run a scan ignoring the interval; if it finds a target attack that instead; else attack the attacker (`Aggressor`). With `AllowMove` true (bot) a unit shot from beyond its range **walks towards the attacker**; with Defend (human) the attack activity has `move == null` and ends immediately if out of range.
- **Attack-moving** (`Activities/Move/AttackMoveActivity.cs` L54-86): while the child move runs, `ScanForTarget(AllowMove, allowTurn = true)` at the normal 3..7-tick rate; when the attack child finishes, an immediate scan (`ignoreScanInterval`). On a hit the move is cancelled and `GetAttackActivity(..., AttackSource.AttackMove, target, AllowMove, false)` is queued for every `AttackBase`; when no target, the move is (re)queued. Activity ends when the move completes with no target.
- **AttackFollow opportunity fire** (`Traits/Attack/AttackFollow.cs` L105-160) for 1tnk/gun/sam (heli has it off): every tick with no requested target, if `OpportunityFire` and stance ≥ Defend: `OpportunityTarget = ScanForTarget(self, allowMove=false, allowTurn=false)` → fires at anything in range while doing something else (moving, after an order ended). `PersistentTargeting` true: when an attack order ends/is cancelled the requested target becomes the opportunity target and keeps being fired on while in range (L60-71).

### 3.4 Attack activities, facing and chasing

Facing tolerance: `Util.FacingWithinTolerance(facing, desired, tol)` (`Util.cs` L120-127): `delta = (desired − facing) mod 1024; delta <= tol || delta >= 1024 − tol` (tol 0 ⇒ exact match). `Util.TickFacing` (L53-64): step towards the desired angle by `step`, snapping when closer than `step`.

**`e1` (`AttackFrontal`, `Activities/Attack.cs`)** — one `Attack` activity:
```
each tick:
  if no armament valid vs target: cancel
  recalculate target (hidden → use last seen position; if reached last-seen position give up)
  armaments = valid ones; minRange = max(MinRange), maxRange = min(MaxRange) over unpaused (5c0)
  if not in [minRange, maxRange]:
      if move == null: give up (status UnableToAttack → activity ends)
      queue child MoveWithinRange(target, minRange, maxRange)   # walks until in range; re-checked every tick
      return NeedsToMove
  if not TargetInFiringArc(FacingTolerance 0):
      facing = TickFacing(facing, yaw to target, TurnSpeed 512)  # instant (turn in place, no Turn activity)
      if still not in arc: return NeedsToTurn
  CheckFire on each armament (respects reload); return Attacking
activity ends when status == UnableToAttack (target dead/invalid/unreachable without move)
```
So an `e1` chases a moving target for as long as it is valid and visible, stopping to shoot whenever in range; there is **no leash**. The `AttackMove` source does not change this (except "attack moves never resupply", irrelevant to e1). With `allowMove=false` (human Defend auto-target) it only shoots targets already within 5 cells and does not pursue.

`MoveCooldownHelper` (`Activities/Move/MoveCooldownHelper.cs`): if a queued move completed because the destination was blocked, the attack activity waits `rand(20, 31)` ticks before pathing again (`Attack`: gives up after the cooldown unless retrying; `AttackFollow.AttackActivity` has `RetryIfDestinationBlocked = true`).

**`1tnk`, `gun`, `sam` (`AttackTurreted` ⊂ `AttackFollow`)** — `AttackFollow.AttackActivity` (`AttackFollow.cs` L231-464) + the trait's per-tick firing:
```
activity tick:
  if no valid armament: cancel
  target = recalculate; attack.SetRequestedTarget(target)
  lastVisibleMaximumRange = GetMaximumRangeVersusTarget; lastVisibleMinimumRange = GetMinimumRange
  if target can move (has IMove) and we can move: leeway = RangeMargin 1c0:
      maxRange = clamp(max − 1c, min(min + 1c, max), max(max − 1c, min))     # 1tnk closes to 3c768 of a moving target
  if ammo-less and Rearmable: (n/a for ground roster)
  if target within [minRange, maxRange]: wait here (return false; the trait fires)
  else if move == null or maxRange == 0: end
  else queue child MoveWithinRange(target, minRange, maxRange)
trait Tick (every tick):
  if RequestedTarget valid: IsAiming = CanAimAtTarget (in range and in firing arc, tolerance default 512 ⇒ any); if aiming: DoAttack
  else: opportunity targeting (above)
AttackTurreted.CanAttack: every turret FaceTarget(target) (turns by TurnSpeed per tick towards the target, L~230-245 of Turreted.cs); fire only when a turret has reached its desired facing exactly
```
Turret realign: `Turreted.Tick` — when not aiming, after `RealignDelay` ticks (1tnk 40; gun/sam −1 = never) the turret turns back to `InitialFacing` (relative to body) at `TurnSpeed`. The tank chases a moving target like infantry (no leash), the gun/sam cannot move so `MoveWithinRange` is never queued and the activity ends when the target leaves range (then `PersistentTargeting` keeps it as an opportunity target so it re-fires if the target comes back).

**`heli` (`AttackAircraft`, `Activities/Air/FlyAttack.cs`)**: see §3.6.

Stopping conditions common to all: target dead/removed, target no longer valid for any weapon (e.g. heli took off → `AirborneActor` → 25mm/M1 invalid → `Cancel`), `Stop` order (`AttackBase.OnStopOrder` cancels the activity unless it is a `Resupply`/`ReturnToBase`).

### 3.5 Infantry prone (`Traits/Infantry/TakeCover.cs`) and crushing (`Traits/Crushable.cs`)

`e1` (`^Soldier`): `TakeCover` `DamageModifiers: Prone50Percent: 50`, `DamageTriggers: TriggerProne`, `Duration: 50` ticks, `SpeedModifier` default 50, `ProneOffset 500,0,0` (muzzle moved forward), `ProneSequencePrefix "prone-"`.
```
on damaged (damage > 0 and warhead DamageTypes ∩ {TriggerProne} ≠ ∅):   # every roster weapon except none → all trigger it
    if !prone: prone = true
    remaining = 50
tick: if remaining > 0: remaining--; if prone and remaining == 0: prone = false
damage modifier while prone: 50% for warheads carrying Prone50Percent (all roster weapons), 100% otherwise
speed modifier while prone: 50%
render: sequence names get the "prone-" prefix (prone-stand, prone-run, prone-shoot)
```
Note `TakeCover` is a `Turreted` subclass with `HasAchievedDesiredFacing => true` (infantry has no real turret).

Crushing: a mover whose locomotor `Crushes` overlaps the victim's `CrushClasses` (e1 default `infantry`, sbag `wall`) and that is **not allied** with the victim (`CrushedByFriendlies` false) treats the cell as free (`Locomotor.IsBlockedBy`). On entering: `WarnCrush` → mobile victims have a `WarnProbability 75`% chance to queue `Nudge(crusher)` (step to an adjacent free cell); on actually overlapping: `OnCrush` → plays `CrushSound squishy2.aud` and kills the victim with the crusher locomotor's `CrushDamageTypes` (empty in RA) → `WithDeathAnimation.OnCrush` spawns `CrushedSequence die-crushed` (corpse). Sandbags are crushed by tanks the same way (no corpse sequence; wall disappears).

### 3.6 Aircraft movement and air attack (`Traits/Air/Aircraft.cs`, `Activities/Air/*.cs`)

- Airborne when altitude ≥ `MinAirborneAltitude` 1 (grants `airborne`); cruising when altitude == `CruiseAltitude` 1280 (grants `cruising`, enables `Hovers` bob and inter-aircraft repulsion).
- `FlyStep(speed, facing)` = `speed` wu along the facing (L628-636). `Fly.FlyTick` (`Fly.cs` L63-94): turn facing by `TurnSpeed` (16) towards desired; because `CanSlide` the movement vector uses the **desired** facing immediately (the body visibly rotates while already sliding); altitude moves toward desired by at most `move.HorizontalLength × tan(MaximumPitch 10°)` per tick. `VerticalTakeOffOrLandTick` (L102-115): pure vertical change of at most `AltitudeVelocity` 43 wu/tick (0 → 1280 in 30 ticks = 1.2 s) while turning to the desired facing.
- `TakeOff` (`TakeOff.cs`): VTOL → vertical climb to cruise altitude; `TakeoffSounds` none for heli. `Land` (`Land.cs` L240-250): VTOL → fly horizontally to the target position (exact), then vertical descent at 43/tick to ground (`LandAltitude` 0).
- `Fly` approach (`Fly.cs` L160-245): done when within the `[minRange, maxRange]` annulus (2D); inside min range: slide backwards; turn deadzone 2; "blocked" if moved < 64 wu in 5 ticks and near enough; final step snaps to the exact position.
- Repulsion (`Aircraft.cs` L456-539): only while cruising and not within `WaitDistanceFromResupplyBase` 4c of a reserved pad: for every other repulsable aircraft at the same cruise altitude within `IdealSeparation` 1706 wu add `d × 8192 / |d|²` (random unit direction if coincident); move by `FlyStep(MovementSpeed, force.yaw)` **in addition** to the activity's own move (so hovering helis drift apart).
- Idle (`OnBecomingIdle` L740-772, `IdleBehavior None`): on the ground: stay (take off only if the cell is not landable and no pad reservation); in the air: `FlyIdle` — a hovering heli (`CanHover`, `IdleSpeed` −1) simply hovers in place (no circling); `INotifyIdle` (AutoTarget) ticks but heli stance is HoldFire so it never auto-engages.

`FlyAttack` (`FlyAttack.cs` L75-182), per tick:
```
if no armament valid vs target: cancel
if ForceLanding: cancel
recalculate target; attackAircraft.SetRequestedTarget(target)
if (all armaments paused (no ammo) or invalid) and Rearmable and target visible:
    if source == AttackMove: end
    AbortOnResupply (true) → cancel queued activities, Queue(ReturnToBase); end       # out of ammo → go home
minimumRange = GetMinimumRangeVersusTarget (1c256 for Hellfires); if maxRange == 0 or < min: end
queue child TakeOff (no-op when airborne)
if not in [min, max] of lastVisibleMaximumRange (AG 5c0 vs ground, AA 4c0 vs air): queue child Fly.MoveWithinRange(target, min, max)
else if target was lost: end
else if not in firing arc (FacingTolerance 80 ≈ ±28°): facing = TickFacing(facing, yaw to target, TurnSpeed 16)     # hover and rotate
# AttackFollow.Tick fires each armament whose CanAimAtTarget (in range, in arc) and CheckFire passes
```
Ranges vs a target: `GetMaximumRangeVersusTarget` uses unpaused armaments valid vs that target → vs ground 5c0 (AG), vs airborne 4c0 (AA). `RangeMargin` 1c applies against moving targets as for the tank (closes to 4c0 of a moving tank). Because `OpportunityFire` is false, a heli fires **only** at its ordered target; because `PersistentTargeting` is false it stops firing the instant the order ends.

Rearm cycle (`ReturnToBase.cs` L54-110, `Resupply.cs`, `Rearmable.cs`): choose the closest own `hpad` that is free (`Reservable.IsAvailableFor`) with a path (air: always); reserve it; `MoveOntoTarget(pad, Exit.SpawnOffset 0,-256,0, Facing 896)` → `Land` at pad centre + offset; `Resupply`: once on the pad, `Docked` resets `RemainingTicks = ReloadDelay` (50); every tick `RearmTick`: for each non-full pool `--RemainingTicks <= 0` → `GiveAmmo(ReloadCount 1)` and reset → **1 ammo per 50 ticks, 8 ammo in 400 ticks (16 s) from empty**; `RearmSound` none. The pad's `WithResupplyAnimation` plays while `ResupplyType.Rearm|Repair` is active. When full: `TakeOffOnResupply: true` → `TakeOff` (or attack-move along the pad rally path if set), reservation released. (Our game: hold on the pad until the next bass note instead of auto take-off.)

### 3.7 Damage states (`Traits/Health.cs` L85-105) and derived conditions

| State | Condition |
|---|---|
| Undamaged | `HP == MaxHP` |
| Light | `75% <= HP < 100%` |
| Medium | `50% <= HP < 75%` |
| Heavy | `25% <= HP < 50%` |
| Critical | `0 < HP < 25%` |
| Dead | `HP <= 0` |

(`HP*100 < MaxHP*25` ⇒ Critical, etc.; integer math.) `GrantConditionOnDamageState@DAMAGED` (`ValidDamageStates: Light, Medium, Heavy, Critical`) grants `damaged` on all units for repair targeting. Art switching uses `RenderSprites.NormalizeSequence` (`Traits/Render/RenderSprites.cs` L85-91, L270-280): try prefixes in order `critical-` (Critical), `damaged-` (≥ Heavy), `scratched-` (≥ Medium), `scuffed-` (≥ Light), using the first prefixed sequence that exists; RA only defines `damaged-*` sequences, so **"damaged" art appears below 50% HP** for buildings, gun/sam turrets, `weap` door. `WithDamageOverlay` (`^Vehicle`): `smoke_m` `start` (49 frames) then `loop` (42 frames) looped `rand(1,3)` times, re-triggered, from `MinimumDamageState Heavy` (< 50%) up to Dead; so tanks smoke below half health. Repair: `RepairableBuilding RepairStep 700` HP per `RepairInterval 24` ticks (`Traits/Buildings/RepairableBuilding.cs` L28-31, step overridden in `^Building` L742) while repairing; `WithBuildingRepairDecoration` draws `allyrepair:repair` (loops, 160 ms/frame) at the building centre.

### 3.8 Death effects

- `e1`: `WithDeathAnimation` (`^Infantry` L361-369; `Traits/Render/WithDeathAnimation.cs` L72-100): sequence = `DeathSequence "die"` + suffix from the **first** `DeathTypes` key present in the killing warhead's `DamageTypes` (dictionary order: DefaultDeath→1, BulletDeath→2, SmallExplosionDeath→3, ExplosionDeath→4, FireDeath→5, ElectricityDeath→6). Roster mapping: M1Carbine/ZSU → `die1`; 25mm, TurretGun, Hellfire, UnitExplode*, BuildingExplode-less deaths → `die4`; FireballLauncher → `die5`; crushed → `die-crushed` (`CrushedSequence`, palette `effect`); killed with no damage types (e.g. `Kill()` by script) → nothing (`FallbackSequence` null). Palette `player` + owner.
- `1tnk`: no husk (`vehicles.yaml` L54-91 has no `SpawnActorOnDeath`). `FireWarheadsOnDeath Weapon UnitExplodeSmall` (`^Vehicle` L291-293; `explosions.yaml` L101-107): at the centre: `SpreadDamage` 4000, Spread 426, falloff over 4·426 = 1704 wu, Versus None 90, Wood 75, Light 60, Heavy 25, Concrete 100, `ExplosionDeath` (so a dying tank hurts nearby infantry for up to 3600); `LeaveSmudge Crater`; `CreateEffect large_explosion` + `kaboom15.aud`.
- `heli` airborne: `SpawnActorOnDeath HELI.Husk` (`husks.yaml`, `^HelicopterHusk` `defaults.yaml` L1123-1142): a husk with the `heli` image, `rotor` overlay still spinning, `smokey` trail every 3 ticks, `FallsToEarth Explosion: UnitExplodeHeli` (`Traits/Air/FallsToEarth.cs`: falls at `Velocity` 43 wu/tick, spins with unbounded `MaximumSpinSpeed`, `Moves` false ⇒ straight down); on hitting the ground `UnitExplodeHeli` (`explosions.yaml` L67-70): 5000 damage spread 426 + `napalm` effect + crater. Landed heli: `FireWarheadsOnDeath UnitExplode` (`self_destruct` effect, 5000 dmg, crater).
- Buildings: `FireWarheadsOnDeath Type: Footprint, Weapon: BuildingExplode` (`^BasicBuilding` L697-700; `explosions.yaml` L121-128): **on every footprint cell** a random one of `building, building_napalm, large_explosion, self_destruct, large_napalm` from image `explosion`, plus a `Crater` smudge in each cell (ValidTargets GroundActor, InvalidTargets Wall — the dying building is already removed, so craters land). `fact` and `powr` additionally spawn a permanent ruin sprite via `WithDeathAnimation DeathSequence: dead, UseDeathTypeSuffix: false` (`factdead.shp` / `powrdead.shp`, 800 ms tick). `gun`/`sam` (`^Defense`) use `SmallBuildingExplode` (same minus `large_napalm`). `ShakeOnDeath` shakes the camera. `sbag`: no explosion/animation (no `FireWarheadsOnDeath` in `^Wall`), `sandbag2.aud` on damage/destroy.

---

## 4. Presentation rules (sequence names per actor and state)

Sequence definitions: `mods/ra/sequences/{infantry,vehicles,aircraft,structures,misc}.yaml`. Default `Tick` per frame is 40 ms (one game tick) unless stated.

### 4.1 `e1` (`infantry.yaml` `e1:` block; traits `WithInfantryBody`, `WithDeathAnimation`, `TakeCover`)

| State | Sequence | Frames | Rule |
|---|---|---|---|
| standing | `stand` (frames 0-7, 8 facings) or `stand2` (8-15) | 1 | `PlayStandAnimation`: a random existing entry of `StandSequences: stand, stand2` each time the unit returns to standing |
| moving | `run` | 6 frames @100 ms, 8 facings | `MoveSequence "run"` while `Mobile.CurrentMovementTypes` has Horizontal |
| shooting | `shoot` | 8 frames @40 ms, 8 facings | `DefaultAttackSequence: shoot`; triggered by `INotifyAttack.PreparingAttack` (i.e. on each shot, at `ReloadDelay` cadence); plays once then stand. No `AttackSequences` per armament for e1 |
| idle fidget | `idle1` / `idle2` | 16 frames @120 ms, no facings | `IdleSequences: idle1, idle2`: when idle, after `rand(MinIdleDelay 30, MaxIdleDelay 110)` ticks play a random one, then stand and re-roll (`WithInfantryBody.cs` L203-213). Not while prone |
| prone | `prone-stand`/`prone-stand2` (frame 144 + facing·4), `prone-run` (144, 4 frames @100 ms), `prone-shoot` (192, 8 frames) | | prefix `prone-` applied to every sequence while `TakeCover` is prone. `liedown`/`standup` exist in the shp but **are not played by `WithInfantryBody`** (flag) |
| dying | `die1`…`die5` 8/8/8/12/18 frames @80 ms; `die6` electric (n/a) | | spawned as a sprite effect at the death position (§3.8), palette `player` |
| crushed | `die-crushed` (corpse1, 1600 ms) | | spawned at death, palette `effect`, `ZOffset -511` |

Facings are quantized to 8 (`QuantizeFacingsFromSequence: stand`).

### 4.2 `1tnk` (`vehicles.yaml` `1tnk:`; `WithFacingSpriteBody`, `WithSpriteTurret`, `WithMuzzleOverlay`, `WithDamageOverlay`)

- Body: `idle`, 32 facings (`UseClassicFacings`), frame chosen from body facing; no move animation.
- Turret: `turret` (frames 32-63, 32 facings) drawn at the turret's world facing; offset = `Turreted.Offset` (0) minus recoil: `WithSpriteTurret.Recoils` true ⇒ turret sprite shifted backwards along its facing by `Armament.Recoil` (set to 85 on each shot, decays 25/tick: 85→60→35→10→0).
- Muzzle flash: armament `MuzzleSequence muzzle` = `gunfire2.shp` 2 frames, image `1tnk`, palette `effect`, played once per shot (`INotifyAttack.Attacking`) at `MuzzleOffset` = `LocalOffset (768, 0, 90)` rotated by the turret facing (forward 768 wu from the centre, 90 up), drawn with `ZOffset` +2 above the body.
- Damage smoke: `smoke_m` `start`/`loop` offset (2,-5) px when HP < 50%.
- Death: `large_explosion` + crater (§3.8), no husk.

### 4.3 `heli` (`aircraft.yaml` `heli:`; `WithFacingSpriteBody`, `WithIdleOverlay@ROTORAIR/ROTORGROUND`, `WithShadow`, `Hovers@CRUISING`, `LeavesTrails`)

- Body `idle` 32 facings.
- Rotor overlay at `Offset 0,0,85` (85 wu above centre): airborne → `rotor` (lrotor.shp frames 0-3 looping, 40 ms = fast spin); on the ground → `slow-rotor` (frames 4-11, 40 ms). Switch is on the `airborne` condition (altitude ≥ 1).
- Shadow: `WithShadow Offset 43,128,0, ZOffset -129` (`Traits/Render/WithShadow.cs` L50-61): the body sprite is re-drawn tinted black (alpha 140/255) at `position + (43,128,0) − (0,0,altitude)`, i.e. on the ground directly beneath the aircraft plus a small (43,128) wu offset, drawn behind the body. Because RA's renderer maps world Z to screen-up, the shadow sits `altitude` wu lower on screen than the body (1280 wu = 1.25 cells at cruise) and converges with it as the heli lands.
- Hover bob while cruising (`Hovers`, `Traits/Render/Hovers.cs`): visual Z offset = `InitialHeight 43 + BobDistance(−43) × sin(2π·t/24)` (period `Ticks 6 × 4` = 24 ticks), i.e. the sprite bobs between 0 and 43 wu above its true altitude; rises over `RiseTicks 20` when enabled.
- Smoke trail `smokey` from offset (−427,0,0) every 3 ticks while `enable-smoke` (granted at Heavy/Critical damage by `GrantConditionOnDamageState@SmokeTrail` default `Heavy, Critical`).
- Landing/rearming: the **pad** animates: `hpad` `active` (frames 1-6 @100 ms, looping) via `WithResupplyAnimation Sequence "active"` while a heli is being rearmed/repaired; `damaged-active` when the pad is below 50%. The heli lands at pad centre + (0,−256) facing 896 (NW) and sits with `slow-rotor`. There is no `WithDockingAnimation` on `hpad` at this commit.
- Husk: `heli` image, `rotor` overlay (fast) while falling, `smokey` trail.

### 4.4 Buildings (`structures.yaml` sequences; `WithSpriteBody`, `WithMakeAnimation`, `WithBuildingBib`, …)

Common: on creation `WithMakeAnimation` plays `make` once (grants `build-incomplete` meanwhile: defences cannot fire, `AttackTurreted PauseOnCondition: build-incomplete`), then `idle` loops. Below 50% HP every body/overlay sequence swaps to its `damaged-` variant where one exists. `WithBuildingBib` (`OpenRA.Mods.Cnc/Traits/Render/WithBuildingBib.cs`): draws sequence `bib` as `rows × width` tiles (`rows = HasMinibib ? 1 : 2`) in the bottom rows of the footprint, frame index `i = col + row·width`, terrain palette, decoration (not tinted). Repair decoration `allyrepair:repair` at centre while repairing.

| Actor | Body | Damaged | Make | Overlays / notes | Bib |
|---|---|---|---|---|---|
| `fact` | `idle` (fact.shp f0) | `damaged-idle` (f26) | `make` factmake.shp | `build` (f1-25) / `damaged-build` played by `WithBuildingPlacedAnimation` when a building is placed; `dead` ruin (factdead.shp) stays after death | `bib2` (2 rows × 3) |
| `weap` | `idle` | `damaged-idle` (f1) | `make` weapmake.shp (`place` f14 is the placement preview) | `WithProductionDoorOverlay Sequence build-top` (weap3.shp 10 frames): door opens frame-by-frame (`PlayFetchDirection` towards the last frame) when a unit is produced and closes once the unit has left the exit cell; `damaged-build-top` (weap2.shp f4-7). **Flag:** `weap` has **no `WithProductionOverlay`** at this commit; there is no "producing" animation besides the door | `bib2` |
| `barr` | `idle` 10 frames looping (flag waving), `Offset 0,-6` | `damaged-idle` (f10-19, 10 frames) | `make` barrmake.shp | no `WithIdleOverlay`; the flag is part of `idle` | `bib3` (2×2) |
| `powr` | `idle` (static) | `damaged-idle` (f1) | `make` powrmake.shp | `dead` ruin (powrdead.shp); `ScalePowerWithHealth` (n/a) | `bib3` |
| `hpad` | `idle` (`ZOffset -1023`, drawn under aircraft) | `damaged-idle` (f7) | `make` hpadmake.shp | `active`/`damaged-active` during resupply (§4.3) | `bib3` |
| `gun` | `idle` = gunmake.shp frame 0 (empty placeholder) | — | `make` gunmake.shp | `WithSpriteTurret` `turret` gun.shp 32 facings; `WithTurretAttackAnimation Sequence recoil` (frames 32-63, 32 facings) played once per shot at `PreparingAttack` (Delay 0), then back to `turret`; `damaged-turret` (f64), `damaged-recoil` (f96) below 50%; muzzle `muzzle` gunfire2 5 frames at `LocalOffset 512,0,112` rotated by turret facing; turret `Recoils: false` | minibib `mbGUN` (1 row × 1) |
| `sam` | `idle` placeholder (gunmake f0) | — | `make` sammake.shp (`Offset -1,-2`) | `turret` sam2.shp 32 facings (`Offset -1,-2`), `damaged-turret` (f34); muzzle `muzzle` samfire.shp 18 frames **8 facings** at `LocalOffset 0,0,320`; no recoil animation | minibib `mbSAM` |
| `sbag` | `WithWallSpriteBody` `idle` sbag.shp 16 frames, frame = adjacency bits | **none** (only 16 frames defined; flag: no damaged art) | — | `RenderSprites Palette: effect` (not player-coloured) | — |

Wall adjacency (`Traits/Render/WithWallSpriteBody.cs` L48-57 and L113-125): frame index = bit field over neighbours of the same wall `Type` (`sandbag`) in the 4 cardinal cells: **north (y−1) = 1, east (x+1) = 2, south (y+1) = 4, west (x−1) = 8**; recomputed when a neighbour is added/removed (`SetDirty`). Line-building (`LineBuild Range 8`) is a placement feature, not needed for the simulation.

### 4.5 Effects, projectiles, smudges (`misc.yaml`)

All explosion sequences live in image **`explosion`** (`Defaults: Length: *, ZOffset 2047`): `piff` (piff.shp), `piffs`, `water_piff`, `small_explosion` (veh-hit3.shp), `med_explosion` (veh-hit2.shp), `med_explosion_air` (veh-hit1.shp, ZOffset 511), `small_explosion_air` (flak.shp), `napalm` (napalm2.shp), `building_napalm` (napalm2 flipped), `self_destruct` (art-exp1.shp), `building` (fball1.shp, offset 0,-9), `large_explosion` (frag1.shp, offset -2,0), `large_napalm` (napalm3.shp), `large_splash`/`med_splash`/`small_splash`. Projectile images: `50cal:idle` (no facings), `dragon:idle` 32 facings, `missile:idle` 32 facings, `120mm:idle`; all `ZOffset 1023`. Trails: `smokey:idle` (Length *, ZOffset 1023). Smudges: `craters:cr1..cr6`, `scorches:sc1..sc6` (tileset-specific tiles). Smoke: `smoke_m` `idle`/`start` (49)/`loop` (42). Decoration: `allyrepair:repair` (160 ms).

---

## 5. Pathfinding and movement rules (enough to look right)

### 5.1 Grid, occupancy, passability

- Cells are 1024 wu squares; a ground unit's position is `CenterOfCell(cell) + SubCellOffset`. `MapGrid.SubCellOffsets` (`OpenRA.Game/Map/MapGrid.cs` L120-127): index 0 = full cell `(0,0)`, 1 top-left `(-299,-256)`, 2 top-right `(256,-256)`, 3 centre `(0,0)`, 4 bottom-left `(-299,256)`, 5 bottom-right `(256,256)`; `DefaultSubCell` = index 3 (centre).
- `Locomotor.SharesCell` (`world.yaml`): **foot = true** → up to **5 infantry per cell** (sub-cells 1-5, a new entrant takes a free sub-cell, preferring its current one); vehicles (tracked/wheeled) occupy the full cell → **one vehicle per cell**, and a vehicle cannot enter a cell with any infantry it cannot crush, nor can infantry enter a vehicle's cell. Buildings occupy their footprint cells (`=` rows in `Footprint` are bib-only/transit cells); trees/rocks are immovable actors.
- Terrain cost (`Traits/World/Locomotor.cs` L83-131): `cost = 10000 / speed%` for listed terrain (Clear 100, Rough tracked 88 → 113, Road 125 → 80); unlisted terrain (Water, Rock, Wall…) is impassable (`short.MaxValue`). Height jumps > 1 are impassable (flat maps: ignore).
- Actor blocking (`CanMoveFreelyInto`/`IsBlockedBy`, L218-332), parametrised by `BlockedByActor` ∈ {None, Immovable, Stationary, All}:
  - cell with free space (or free sub-cell for sharers) → passable;
  - every actor in the cell crushable by us (crush class match and not allied) → passable (we will crush);
  - `check ≤ Stationary` and no stationary actor there → passable (moving units are ignored);
  - `check ≤ Immovable` and no immovable actor (buildings, trees, paused/immovable mobiles) → passable; allied movable units are ignored at this level (they will be nudged);
  - otherwise blocked unless the blocker is a transit-only building cell or a temporary blocker we may remove.
- A* (`Pathfinder/PathSearch.cs`, `DensePathGraph.cs` L196-230): 8-neighbour grid, step cost = terrain cost × (√2 for diagonals), plus a `LaneBiasCost 1` on alternate rows/columns to make opposing streams of units keep to lanes; heuristic = diagonal-distance using the minimum terrain cost. A hierarchical pathfinder caches reachability; you can ignore it.

### 5.2 Move execution (`Activities/Move/Move.cs`)

```
path = A*(from, dest, check = Immovable)                 # ignores moving/movable allies (L130-136, 259, 300)
loop (each cell step):
    next = path.pop()
    if next is blocked right now (CanEnterCell(next) false, check All):
        if near enough to dest (nearEnough cells) and no better free neighbour: stop here (done)
        if blocked by something immovable: repath (Immovable) and continue
        NotifyBlocker(next)                               # friendly idle blocker queues Nudge → steps to an adjacent free cell
        if !hasWaited: wait WaitAverage = 40 ticks (locomotor default; WaitSpread unused here); hasWaited = true; retry
        after the wait: if the cell is being evacuated keep waiting, else repath with check = All;
        if no path and we ourselves are blocking others: back off to a free neighbouring cell (UnblockDestination)
        else give up
    facing needed = direction to next cell
    if !TurnsWhileMoving and facing differs: queue Turn(firstFacing)   # vehicles stop and rotate at TurnSpeed; infantry AlwaysTurnInPlace with TurnSpeed 512 = instant
    MoveFirstHalf: from current pos to the midpoint between cells; MoveSecondHalf: to the next cell centre (+ sub-cell offset)
      each tick progress += MovementSpeedForCell(ToCell) (wu); position = lerp(from, to, progress/distance); leftover progress carries into the next part
      (straight step = 1024 wu, diagonal = 1448; facing lerps across the step for turn-in-place units)
```
`nearEnough`: attack-move/`MoveTo(cell, 8)` lets the unit stop anywhere within 8 cells of the ordered cell once it is blocked; plain move orders use 0. `Nudge` (`Activities/Move/Nudge.cs`): an **idle friendly** blocker moves to an adjacent free cell away from the nudger (`GetAdjacentCell`); a non-idle blocker just flags `IsBlocking`. Aircraft nudge by flying a random 512..2048 wu offset.

Approximation for the port: A* over cells; blocked cells = building footprints, trees, map edge; vehicles 1 per cell, infantry 5 per cell; compute the path ignoring friendly units; when the next cell is occupied by a friendly unit ask it to step aside if idle, wait 40 ticks, then repath avoiding all units; tanks ignore enemy infantry and sandbags in the path and crush them; move at `Speed × terrain%` wu per tick along cell centres; vehicles rotate in place at 20/tick before each direction change, infantry turn instantly.

---

## 6. Things I could not find or that deviate from your question (flags)

1. `IdleBaseUnitsMaximum` is a `UnitBuilderBotModule` parameter (production), not a squad parameter.
2. `MaxBaseRadius` exists on `SquadManagerBotModuleInfo` but is unused by the squad code at this commit.
3. The air squad's `FindDefenselessTarget` line-of-approach test is inverted in the source (§2.2); it makes AI helicopters effectively passive against undefended enemies. Implement the intended semantics and note the deviation.
4. The fuzzy library (`OpenRA-FuzzyLogicLibrary 1.0.1`) is a NuGet dependency; Mamdani defaults (min/max/centroid) are assumed, not read from source. A crisp approximation is given in §1.6.
5. `weap` uses `WithProductionDoorOverlay` only; no `WithProductionOverlay` "producing" animation exists for it.
6. `hpad` has `WithResupplyAnimation` (`active`), no `WithDockingAnimation`.
7. `sbag` has no damaged frames in its sequence (`idle` only, 16 adjacency frames) and no `BlocksProjectiles`, so bullets pass over it; `^Wall` has no death explosion.
8. `e1` `liedown`/`standup` sequences are defined but never played by `WithInfantryBody`.
9. `1tnk` has no husk; `heli` only leaves a husk when it dies airborne.
10. Squad targeting uses `IsPreferredEnemyUnit`, which does not honour `NoAutoTarget`, so a sandbag can be the "closest enemy" a squad walks to; the units themselves will then never auto-fire at it (NoAutoTarget) — consider excluding `Wall` from squad target selection.
11. `BusyAttack` only recognises the infantry `Attack` and `FlyAttack` activity types; tanks therefore receive a fresh attack-move order every squad update while in `GroundUnitsAttackState`.
12. All `AutoTargetPriority` entries use `Priority 1`; there is no unit-type preference anywhere in RA auto-targeting — only distance.
