# LedgerLine — Business Plan (DRAFT, Nov 16 2026)

> Status: **draft for Theo's approval.** Anything that changes the business model is marked **PROPOSED** and is not in `plan-and-decisions.md` yet.
> Sources were checked 2026-11-16 and are listed at the end. **[A]** marks an assumption, not a sourced fact.
> No real payments: pricing and trial flows are shown on the pricing page only (out of scope this week).

---

## 1. Market size (TAM / SAM / SOM)

**Correction to the meeting note "big TAM":** the music-lesson *industry* is large (about $725M a year in US private lesson revenue, per IBISWorld 2026). But that is money teachers earn from lessons, **not** money they spend on software. LedgerLine's market is the software budget of teacher-led studios, which is much smaller. Pitch it as a niche you can win, not a giant market.

**What we know (sourced anchors)**
- US private music lessons industry revenue: **$724.8M in 2026**. It is highly fragmented, with no company above 5% share (IBISWorld).
- MTNA, the national music-teacher association: **~17,000 members** (Wikipedia, current). **73%** are independent teachers (MTNA demographics). It covers all instruments, not just piano.
- Utah Music Teachers Association (UMTA): **500+ teachers**. It has been an MTNA affiliate since 1956 (Salt Lake County Arts).
- Average 60-minute independent-studio lesson: **$65.72** (median $60), from the MTNA 2024 Member Survey.
- No reliable count of US private *piano* teachers exists. Job-site estimates (e.g. ~13.6k "piano instructors employed") exclude self-employed teachers, so we treat them as low-quality.

**Adult-learner trend (meeting claim), only partly supported**
- About **9.6%** of US adults played an instrument in the 12 months ending Feb 2020, or about 23.7M people (NEA).
- NEA's 2022 survey found a greater share of adults playing instruments than in 2017.
- YouGov (2022, n=3,000): about half of Americans who never learned an instrument wish they had, and **47%** of them name piano. Only **9%** of people who play an instrument started at 18 or older.
- **Takeaway:** interest in piano among adults is strong and instrument playing rose from 2017 to 2022. "Many adults are *starting* piano" is not well measured, and most of the search results claiming adult "surges" were unreliable sites, so they are not used here. Say "strong adult interest," not "an adult boom."

**Sizing (Teacher Studio, at the PROPOSED $8–10/mo = $96–120/yr)**

| Layer | Definition | Teachers | Annual value |
|---|---|---|---|
| **TAM** | All US private piano teachers who could buy studio practice software | **[A]** 15k / 30k / 60k (low / mid / high scenarios; no reliable census exists) | $1.4–1.8M / $2.9–3.6M / $5.8–7.2M |
| **SAM** | Teachers we can realistically reach: MTNA independent teachers (proxy; includes non-piano) | ~17,000 × 73% ≈ **12,400** | ≈ **$1.2–1.5M** |
| **SOM, year 1** | Utah first: **[A]** 5% of UMTA's 500+ teachers | ≈ **25** | ≈ **$2.4–3.0k ARR** |
| **SOM, year 2** | **[A]** 1% of SAM, regionally | ≈ **124** | ≈ **$12–15k ARR** |

- Student Solo is treated as a secondary market, per the meeting's teacher-led focus. As a rough upper bound only: 23.7M adult instrument players × 31% who play piano (NAMM/Gallup, an older survey) ≈ 7M people. This mixes years and surveys, so don't present it as a fact.
- **[A]** For the video, the honest line is: "A small, fragmented, underserved software niche. We start with ~25 Utah teachers and grow through teacher associations."

---

## 2. Competitive moat

A **moat** is a lasting reason customers stay and competitors can't easily copy you. **A low price is not a moat:** My Music Staff could cut its price tomorrow. LedgerLine has **no moat today** (it's a week-old prototype). These are the moats it *could* build:

1. **Progress history (switching costs).** Every week a studio uses LedgerLine, it builds up per-piece stage history and practice logs for every student. Leaving means losing that record. This gets stronger with each week of use.
2. **Studio-wide adoption.** One teacher brings 10–30 students and their families onto the product. A teacher switching tools must move the whole studio, and parents get used to the weekly card.
3. **Insights data network (long-term).** As more studios opt in, the benchmarks get better, such as how long pieces take to reach "performance ready." Better benchmarks make Insights more valuable for teachers and publishers. This only works with real opt-in data and the 10+ rule. Generated demo data is not a moat.
4. **Trust with teachers.** The incumbent has years of reviews (My Music Staff: 4.8/5 from 761 Capterra reviews). Earning trust through teacher associations is slow, and that slowness protects you once you have it.

---

## 3. Differentiation

**Positioning (PROPOSED): "Convenience + price, built on a practice-first product."** Price and convenience get a teacher to try LedgerLine. The verified practice features are why they stay.

| | My Music Staff | LedgerLine |
|---|---|---|
| Price | $16.95/mo + $4.95 per extra teacher | PROPOSED $8–10/mo |
| Focus | Studio admin: scheduling, attendance, billing, lesson notes | Practice-first |
| Practice log | Time + notes, timer, file uploads | Per piece, logged the same day |
| Piece progress | Generic labels (In-Progress, Completed, Requested…) | 6 stages per piece: learning notes → … → performance ready |
| Parent view | Lesson notes in the portal; no weekly summary found | Weekly progress card (shareable link) |

- **Convenience is a claim we must prove.** It isn't verified yet. Measure it in Thursday's usability checklist and the tester sessions (for example, a student logs practice in under 30 seconds **[A target]**), and only then put it in the copy.
- **Honest limits:** practice logs are self-reported (LedgerLine replaces week-later recall; it doesn't verify practice). There is no scheduling or billing.
- **Open positioning question:** should LedgerLine *replace* My Music Staff, or be used *alongside* it? Teachers who rely on My Music Staff for billing may not switch, but might add a practice tool. "Alongside" means the price is compared against $0, not $16.95. Decide before writing the landing copy.

---

## 4. Business model and pricing (PROPOSED)

| Plan | Current (plan doc) | PROPOSED | Annual (PROPOSED: "2 months free," ≈17% off) |
|---|---|---|---|
| Free | 1 teacher + up to 3 students, or solo basic logs | **Replace with a 14-day trial** (see options below) | — |
| Student Solo | ~$3/mo | **$3–5/mo** | $30–50/yr |
| Teacher Studio | ~$8/mo | **$8–10/mo** | $80–100/yr |
| Practice Insights | per report, price TBD | Unchanged: per report, price set Thu | — |

- Students with a teacher still pay nothing; the Teacher Studio plan covers them.
- Pricing anchor for the copy: **$8/mo is about 12% of one average lesson** ($65.72, MTNA 2024).
- The ≈17% annual discount ("2 months free") is a common convention, not a sourced benchmark **[A]**.

**Risks of the meeting's "$0.01 charge to capture payment info"**
1. **It costs more than it collects.** Stripe's standard US fee is 2.9% + 30¢ per successful card payment, so a $0.01 charge costs about $0.30, plus refund handling.
2. **Card-testing fraud.** Fraudsters test stolen cards with exactly these small or $0 transactions. Stripe reports card testing is up 100x+ since 2019 and that small merchants can be overwhelmed within hours. A $0.01 charge page invites it.
3. **Fewer signups (conversion drop).** Requiring a card raises trial-to-paid conversion but cuts how many people start a trial. The evidence is mixed: ChartMogul-based benchmarks put card-required trials at roughly 25–35% trial-to-paid, against much lower rates for no-card trials, while Chargebee found no-card trials did *better* end to end (1.2% vs 0.6% of visitors). For a new brand that needs teachers to try it at all, fewer signups is the bigger risk **[A]**.
4. **Under-13 students can't pay.** Children don't have cards. Teachers (Studio) or parents (Solo, for minors) must pay, and collecting a child's data needs parental consent (COPPA). The trial flow must ask for a teacher or parent account.
5. **Confusing statement charges** lead to support emails and possible disputes **[A]**.

**Alternatives**

| Option | How | Pros | Cons |
|---|---|---|---|
| **A. 14-day trial, no card** (recommended for now) | Sign up, use everything, prompted to pay on day 14 | Most signups; no fraud surface; works for teachers testing with students | Lower trial-to-paid rate |
| B. 14-day trial, card required, **no charge** | Save the card without charging it (Stripe's Setup Intents API is built for this) | Higher trial-to-paid rate; no $0.01 fee | Fewer signups; still a card-testing surface; needs fraud tools |
| C. Keep a small Free tier | Current plan | Feeds the opt-in Insights data network; no-risk entry | Some users never pay |
| D. $0.01 charge | Meeting idea | — | All five risks above; **not recommended** |

**Tradeoff to note:** removing Free shrinks the pool of studios that could opt into Insights, which weakens moat #3. Option A plus a "studio stays readable after the trial ends" policy **[A]** keeps most of that benefit.

---

## 5. Marketing plan (teacher-first)

**Who we target:** independent piano teachers with 10–30 students, starting in Utah. Lead with the benefit, then the feature: *"Know what each student practiced before they walk in."*

| Channel | Action | Why it fits |
|---|---|---|
| UMTA local chapters | Ask to demo for 10 minutes at a chapter meeting (chapters such as Nebo meet monthly) | 500+ Utah teachers; trust spreads through peers |
| MTNA local affiliates | After Utah, approach other states' local associations (500+ nationally) | Same playbook, national reach |
| Studio referrals | "Refer a teacher, both get a month free" (PROPOSED; display only) | Teachers trust other teachers more than ads |
| Progress card loop | Parents receive the card each week. A small "Made with LedgerLine" footer (PROPOSED, post-feature-lock idea → later list) | The card is the most marketable feature; every share is free reach |
| First case study | Saturday's piano-teacher tester: their feedback and a quote (with permission) | Real proof beats claims |
| Pricing page + landing page | Lead with the progress card and "about 12% of one lesson's price" | Already in scope (Thu–Fri) |

**Metrics to track [A]:** trial → paid rate, students per teacher, logs per student per week, progress-card views per week, and teacher churn after 90 days.

---

## Roadmap (future, NOT this week): AI scoring and rankings

**Idea from the meeting:** AI scores practice recordings on a universal scale, then compares students within a studio or against top players, with rankings.

**Status:** future roadmap only. Audio recording is already a *stretch* item this week, and AI scoring sits beyond it.

**Data it would need**
- Audio recordings of practice, per piece, across many students and recording setups
- Reference performances to compare against (licensing: recordings of top players are copyrighted)
- Labeled examples (teacher-graded takes) to train and check the scoring
- Piece and stage metadata (which we already collect)

**Privacy and fairness concerns**
- **Minors:** under COPPA, an audio file containing a child's voice counts as personal information. Practice recordings may capture voices, so this needs verifiable parental consent before collecting from under-13s, plus a clear deletion policy. *(I'm not a lawyer.)*
- **Rankings conflict with the 10+ rule.** Insights only show groups of 10+ so no individual can be singled out, and rankings name individuals by design. If it is ever built: opt-in only (with parental consent for minors), within one studio, nicknames instead of real names, and cross-studio comparisons only as group percentiles.
- **Fairness:** scores would vary with microphone quality and instrument (35% of students practice mainly on a digital piano or keyboard, per MTNA 2024). A "universal" score could punish students for their equipment, not their playing.
- **Wellbeing:** public rankings of children's practice can discourage beginners. Make teacher-only views the default.

---

## Sources (checked 2026-11-16)
- IBISWorld, Private Music Classes in the US (market size 2026; fragmentation): https://www.ibisworld.com/united-states/market-research-reports/private-music-classes-industry/
- MTNA membership ~17,000 (Wikipedia): https://en.wikipedia.org/wiki/Music_Teachers_National_Association
- MTNA member demographics (73% independent): https://www.mtna.org/Demographics.html
- MTNA 2024 Member Survey highlights (lesson rates; digital-piano share): https://certification.mtna.org/downloads/Business/General/MemberSurvey2024_Highlights.pdf
- UMTA 500+ teachers; MTNA affiliate since 1956: https://www.saltlakecountyarts.org/?p=11919 and https://www.saltlakecountyarts.org/?p=12866
- UMTA chapter meetings (Nebo): https://servedaily.com/arts-and-culture/utah-music-teachers-association-extends-an-invitation-to-local-music-teachers
- NEA, adults playing an instrument (9.6%, 23.7M): https://www.arts.gov/sites/default/files/NationalReportforADPAccess.pdf
- NEA, 2022 vs 2017 instrument playing: https://nea.gov/stories/research-quick-study/quick-study-october-19-2023
- YouGov 2022 musical instrument survey: https://yougov.com/en-us/articles/43512-young-americans-increasingly-exposed-music
- NAMM (piano 31% of players; older Gallup data): https://ww1.namm.org/node/284
- My Music Staff pricing: https://www.mymusicstaff.com/?p=75253
- My Music Staff practice log: https://www.mymusicstaff.com/student-portal/
- My Music Staff progress labels + lesson notes: https://www.mymusicstaff.com/?p=64549
- My Music Staff reviews (Capterra): https://www.capterra.com/p/148451/My-Music-Staff/pricing/
- Stripe pricing (2.9% + 30¢): https://stripe.com/pricing
- Stripe on card testing: https://stripe.com/newsroom/news/card-testing-surge
- Stripe Setup Intents (save card without payment): https://docs.stripe.com/payments/save-and-reuse
- Trial conversion benchmarks (ChartMogul via Userpilot): https://userpilot.com/blog/free-trial-conversion-rate/
- Chargebee, card vs no-card trials: https://www.chargebee.com/blog/credit-card-trials-credit-card-trials-go/
- FTC, COPPA and voice recordings: https://ftc.gov/system/files/documents/public_statements/1266473/coppa_policy_statement_audiorecordings.pdf
- eCFR 16 CFR 312.2 (definition of personal information): https://www.ecfr.gov/current/title-16/chapter-I/subchapter-C/part-312