# UX Research Report — PCD Web Dashboard

*Produced by research agent, March 2026*

I used the UX brief and prototype context as the baseline for this review. The brief asks for rail-by-rail recommendations across Dashboard, Jobs, Buildings, and Settings, and the prototype context shows a desktop-only 3-column app with mocked data, no GPS1 workflow, no calendar/map, no notifications, and no client/contact UI yet.

## Executive take

Your prototype is already pointed in the right direction in two important ways: it treats **Buildings** as a first-class object and it separates **solo** from **firm** contexts. That is smarter than most generic field-service tools, which usually lead with customers/jobs first and only treat properties as secondary records. Where the prototype currently breaks from real-world usage is that it still behaves like a **generic admin dashboard** more than a **morning operations console for a plumber/LMP firm**. Competitor tools and user feedback both suggest the core experience should revolve around: **what needs attention today, who is going where, what deadline is at risk, and what paperwork or money is still outstanding**. ([Jobber Help Center][1])

---

## 1. Competitor analysis matrix

| Tool | Dashboard / Home | Jobs / Dispatch | Buildings / Properties / Compliance | Settings / Admin | Best fit for PCD | Sources |
|---|---|---|---|---|---|---|
| **ServiceTitan** | Dispatch-centric; strong scheduling and ops visibility | Very strong: dispatch board, messaging, holding area, weekly view | Good location/contact handling, but not LL152-native | Deep permissions + notifications, but complexity is a known pain | Best for multi-crew firms, not solo-first | ([ServiceTitan][2]) |
| **Housecall Pro** | Jobs dashboard + homepage employee map | Strong small-team scheduling and field workflow | Customer-first; properties are less central than in compliance work | Solid team roles/permissions; mixed sentiment on support/changes | Good small-team baseline, weaker for deep compliance ops | ([Housecall Pro Help Center][3]) |
| **Jobber** | Action-oriented dashboard with recommended, assigned, outstanding, upcoming work | Strong: quick-create, multiple schedule views, mobile-readiness | Clear property model, but still client-owned | Good permissions, reporting, lead source, team productivity | Best baseline for solo/small firms | ([Jobber Help Center][1]) |
| **ServiceM8** | Metrics for jobs completed, first-time-fix, margin, feedback | Strong job/action queue and scheduling discipline | Better location intelligence than most SMB tools | Good security roles | Strong model for owner-operator to small team ops | ([ServiceM8 Help Center][4]) |
| **Workiz** | Real-time "all in one place" positioning | Strong drag/drop scheduling and GPS dispatch | Less asset/compliance-centric | Good user/role management | Useful reference for dispatch/map patterns | ([Workiz][5]) |
| **SafetyCulture** | Scheduled inspections start from Home; inspection-first | Strong inspection execution, weak FSM dispatch | Strong asset/site/action model; better for evidence + follow-up than CRM | Best-in-class notification granularity + permission sets | Best inspiration for inspections/forms/actions layer | ([SafetyCulture Help Center][6]) |
| **NYC DOB NOW / GPS forms** | No operational dashboard | No dispatch/job management | This is the mandatory certification system of record | Filing rules and deadlines, not team software | Must be wrapped by your UX, not replaced by it | ([New York City Government][7]) |

**What the matrix says:** the market splits into two camps. Field-service suites are good at **dispatch, customers, scheduling, and money**, while inspection/compliance tools are good at **evidence capture, assets, and follow-up actions**. PCD needs both. ([Jobber Help Center][8])

---

## 2. User workflow insights

### Solo plumber

Real feedback suggests many solo or 1-2 person shops still run on a simple stack: Google Calendar for scheduling, QuickBooks for invoicing, and notes/spreadsheets for job details. Multiple Reddit threads describe ServiceTitan/Jobber-class tools as too bloated or too expensive for solo operators, while official mobile flows in Jobber and Housecall Pro emphasize "assigned work + quick create + finish the job" rather than deep back-office dashboards. ([Reddit][9])

**Implication:** solo users do not want to land on a management cockpit full of abstract metrics. They want: next stop, who to contact, what's due, quick notes/photos, and a fast way to mark progress and send paperwork. ([Housecall Pro Help Center][10])

### Firm admin / LMP

Admins managing multiple techs care much more about **unassigned work, schedule changes, overdue items, map visibility, receivables, and team productivity**. Jobber's insights dashboard includes lead source, receivables, projected income, job value, and top-performing team members. Housecall Pro's homepage emphasizes an employee map. ServiceTitan's dispatch updates focus on holding areas, weekly views, and centralized activity panels. ServiceM8 explicitly teaches owners to keep unscheduled jobs empty and optimize first-time-fix and profit. ([Jobber Help Center][11])

**Implication:** firm mode should feel like an **operations center**, not just a slightly relabeled solo dashboard. ([Jobber Help Center][11])

### Field technician

The common technician workflow is very linear: receive assignment, travel, arrive, do work, capture notes/photos/findings, finish, and move on. Housecall Pro's training literally teaches field techs to press **On My Way → Start → Finish** on every job. Jobber's app centers assigned/scheduled visits and lets teams quick-create from the schedule. The strongest complaints about field apps are about slowness, timers, weak search, and connectivity in front of customers. ([Housecall Pro Help Center][10])

**Implication:** your field-state model should stay simple, and anything that adds taps without helping completion or filing will be felt as overhead. ([Housecall Pro Help Center][10])

---

## 3. Pain points catalog

1. **Too bloated / too expensive for small shops.** This came up repeatedly in Reddit threads and comparison discussions; bigger FSM suites are often seen as appropriate only once the business has multiple crews or larger revenue volume. ([Reddit][9])

2. **Field apps fail at the worst possible time.** Housecall Pro's Play review mentions connection issues in the field in front of customers; ServiceTitan's mobile review complains about slower refresh, restart loops, loss of timer utility, and worse material search. ([Google Play][12])

3. **Reporting and job-cost visibility are hard to trust or extract.** Users said the bigger pain isn't just dispatching but knowing what jobs actually made money; Jobber users complain about bugs/lags, and ServiceTitan users complain about reporting/permissions complexity. ([Reddit][13])

4. **Invoice/admin workflows become a time sink.** One Jobber complaint describes reopening and moving jobs around just to create one consolidated invoice. Another Reddit post describes 20+ hours a week on quoting, invoicing, CRM updates, and scheduling. ([Reddit][14])

5. **Support, onboarding, and constant changes create distrust.** Housecall Pro reviews repeatedly mention slow support, aggressive upsells, and disruptive product changes; ServiceTitan reviews include strong criticism of support and configuration complexity. ([Capterra][15])

6. **Permissions/settings can be dangerous if too broad.** ServiceTitan users complain that settings access is too coarse and permissions are hard to manage; that is especially relevant for a compliance product where filings, forms, and company details cannot be casually changed. ([Reddit][16])

7. **Rigid mandatory workflows annoy technicians.** The strongest anti-pattern I found is over-engineered required checklists/statuses that slow the field user down. A ServiceTitan complaint about huge mandatory questionnaires is exactly the sort of friction to avoid. ([Reddit][16])

---

## 4. Rail-by-rail recommendations

### ⌂ Dashboard

#### What you got right

The prototype already surfaces urgency and recent activity, and the separate firm/solo framing is directionally correct. That matches how Jobber, Housecall Pro, ServiceM8, and SafetyCulture all differentiate between "what needs attention now" and deeper management/reporting areas. ([Jobber Help Center][1])

#### What to change

Your current cards feel generic: Active Jobs, Approaching Deadlines, Overdue, Completed, Needs Review. For LL152, the first screen should be more like **Action Required Today**. For firm admins, I would replace or demote "Completed" and promote: **Due in 30/60/90 days, Unassigned inspections, GPS1 sent but GPS2 not filed, Correction certifications due, Buildings needing owner follow-up**. For solo mode, default to **My next inspection, Today's stops, paperwork due, and money/owner follow-up**. Jobber and ServiceM8 both bias home toward action queues; SafetyCulture even starts scheduled inspections from Home. ([Jobber Help Center][1])

#### What's missing

You need a **today strip** or **dispatch strip** on the dashboard, even before you build a full calendar rail. Competitors consistently surface where people are going next: Housecall has an employee map, ServiceTitan has holding/activity views, Jobber has assigned/outstanding work, and Workiz emphasizes dispatch/GPS context. ([Housecall Pro Help Center][17])

#### Recommendation

Make Dashboard adapt by role:

* **Solo:** Today, Next Stop, Due Soon, Awaiting Owner, Quick Add.
* **Firm admin:** Unassigned, Due Soon, Overdue, Awaiting Filing, Map/Tech availability, Team exceptions.
* **Technician web/mobile:** My assigned inspections, start/finish, photos/findings, notes. ([Housecall Pro Help Center][10])

---

### ☰ Jobs

#### What you got right

A filterable table is the right default for desktop office users, especially firm admins. Competitors do not abandon lists; they usually layer schedule/map views on top of them. ([Housecall Pro Help Center][18])

#### What to change

Your current job model still reads like generic FSM. LL152 work needs statuses that reflect the real compliance chain, not just Open / In Progress / Completed. A better state model is something like: **New → Scheduled → On Site → Inspection Complete → GPS1 Sent to Owner → GPS2 Filed → Correction Required / Closed**. NYC's process makes the handoff explicit: GPS1 goes to the owner, GPS2 goes to DOB, and corrections can require follow-up certifications. ([New York City Government][7])

#### What's missing

You need at least two more job views:

1. **Calendar / dispatch view** for firms.
2. **Today agenda view** for solo/tech users.
   ServiceTitan, Housecall Pro, Jobber, ServiceM8, and Workiz all push scheduling/dispatch much harder than your current prototype. ([ServiceTitan][19])

The job detail also needs real sections for:

* site + owner/contact
* inspection checklist/scope
* findings + photos
* GPS1/GPS2 docs/status
* timeline/audit log
* source / lead source
* corrections / follow-up work

Right now the prototype acknowledges Findings only as a placeholder, and the prototype context itself says GPS1 capture is still missing.

#### Recommendation

Keep the table, but add:

* **Quick create** from Buildings and from the schedule, not only from a form flow.
* **Unassigned / holding area** for firms.
* **Simple field buttons** like Housecall's On My Way / Start / Finish logic rather than overloading techs with admin states.
* **Lead/source tracking** in the job record, because Jobber and your own domain model both show that source matters operationally and commercially. ([Jobber Help Center][20])

---

### ⊞ Buildings

#### What you got right

Making Buildings a dedicated rail is one of your best decisions. Most FSM tools bury the location under the customer, but LL152 is genuinely **building/BIN-centered**. DOB deadlines and filings are tied to the building and its gas-piping status, not just to a customer relationship. ([New York City Government][7])

#### What to change

The current card grid is visually clean, but it should not be the only main office view. For LMP firms, the default should probably be a **table/list** with sortable columns and saved filters; cards should be secondary. Competitors that work well at scale give ops teams denser views, while more contextual property/asset records live one click deeper. ([Jobber Help Center][21])

#### What's missing

The building record needs to become the canonical compliance record:

* BIN
* address
* borough / community district
* gas/no-gas status
* current cycle/subcycle
* next due date
* last inspection date
* open correction status
* owner/client/contact
* prior jobs / prior filings / notes

This is especially important because your prototype explicitly has **no client/contact concept in the UI yet**, even though the domain supports it. Mainstream FSMs solve this with clients/properties or client sites; SafetyCulture solves it with assets/sites. PCD needs the compliance version of that. ([Jobber Help Center][21])

#### Recommendation

Add:

* **List + map + cards** as three modes.
* a **Building Profile** page with timeline/history/forms.
* **prospect mode** for imported DOB rosters.
* filters for **due window, borough/community district, gas status, inspection status, assigned plumber/team, prospect vs active client**.

If Jobs are the work container, Buildings should be the compliance container. ([New York City Government][7])

---

### ⚙ Settings

#### What you got right

Having a dedicated settings rail and team/company concepts is correct. Role-based access is standard across the tools I reviewed. ([Jobber Help Center][22])

#### What to change

The **Solo / Firm toggle** should not live as a visible production setting. Competitors treat this as account structure, plan, or permissions, not as a day-to-day toggle. Exposing it as a normal setting risks confusing users and breaking trust about what data/mode they are in. ([Housecall Pro Help Center][23])

#### What's missing

Settings is currently far too thin for a compliance product. You need:

* **Users & roles**
* **Notification preferences**
* **Templates/checklists/forms**
* **Import center / data quality / anomalies**
* **Company + license + seal/signatory details**
* **Integrations**
* **Audit/activity access**
* **Billing / plan**

Notification granularity is especially important because SafetyCulture, Jobber, Housecall, and ServiceTitan all recognize that teams need different alert channels and role-based visibility. ([SafetyCulture Help Center][24])

#### Recommendation

Make Settings a true admin area with four sections:

1. **Organization**
2. **Team & permissions**
3. **Notifications & templates**
4. **Imports, filing, and integrations**

For PCD specifically, I would also add a **Compliance config** section for license number, form defaults, owner-facing report defaults, and filing guidance around GPS1/GPS2. ([New York City Government][25])

---

## 5. Key UI patterns to steal

### 1. Home should be an action queue, not a vanity dashboard

Steal the Jobber / ServiceM8 / SafetyCulture pattern of surfacing assignments, outstanding work, and scheduled work from the home screen. That is much closer to a 6am plumber workflow than static KPI cards. ([Jobber Help Center][1])

### 2. Add a dispatch layer with an unassigned bucket

ServiceTitan's holding area and weekly dispatch direction are especially relevant for firm mode. Even a lightweight version would massively improve your Jobs and Dashboard rails. ([ServiceTitan][19])

### 3. Use a canonical property/building profile

Jobber's client/property split, ServiceM8's client sites/location insights, and SafetyCulture's asset/site model all point to the same pattern: one place for the location record, then hang work, notes, history, and actions off it. For you, that record should be the Building Profile. ([Jobber Help Center][21])

### 4. Keep the field-tech state machine brutally simple

Housecall Pro's field checklist is simple for a reason. Start, do the work, finish, document. Avoid the trap of turning every compliance nuance into a technician-facing status. Keep filing/admin states mostly office-side. ([Housecall Pro Help Center][10])

### 5. Bake in quick-create everywhere

Jobber's quick-create and schedule-direct patterns are worth copying. In a product like this, users should be able to create a job from the dashboard, schedule, building profile, or activity stream without a multi-step wizard. ([Jobber Help Center][20])

### 6. Treat inspections as evidence that creates actions

SafetyCulture's best idea is the inspection → action linkage. For PCD, an inspection should be able to create structured findings, corrections, deadlines, and filing states. That is a stronger fit than generic "recent activity." ([SafetyCulture Help Center][6])

### 7. Separate office UX from field UX

The public walkthrough ecosystem reinforces this split: Jobber tutorials focus heavily on scheduling, Housecall Pro on schedule/dispatch/mobile usage, and SafetyCulture on starting/completing inspections. Your product should not pretend one screen serves dispatcher, LMP owner, and tech equally well. ([YouTube][26])

---

## Bottom line

**What you got right:** first-class Buildings rail, role awareness, sidebar filters, and a clean desktop shell.

**What you got wrong:** the current experience is still too generic-FSM on Dashboard and too generic-admin on Jobs.

**What you're missing:** dispatch/calendar, client/contact layer, GPS1/GPS2 workflow, notifications, and a true compliance-centric Building Profile.

If I were sequencing the next iteration, I'd do **Dashboard first**, then **Jobs**, then **Buildings**, then **Settings** — because the biggest current risk is that the product opens like a report instead of a workday.

---

## Sources

[1]: https://help.getjobber.com/hc/en-us/articles/360033835353-Dashboard
[2]: https://www.servicetitan.com/features/dispatch-software
[3]: https://help.housecallpro.com/en/articles/690728-dashboard-reports-overview
[4]: https://support.servicem8.com/help-center/servicem8-add-ons/reports/jobs-completed-in-the-business-dashboard-report
[5]: https://www.workiz.com/features/
[6]: https://help.safetyculture.com/en-US/003525/
[7]: https://www.nyc.gov/site/buildings/property-or-business-owner/gas-piping-inspections.page
[8]: https://help.getjobber.com/hc/en-us/articles/115009379027-Job-Basics
[9]: https://www.reddit.com/r/Plumbing/comments/1r68cug/is_jobberservicetitan_overkill_for_solo_guys_i/
[10]: https://help.housecallpro.com/en/articles/4423283-employee-training-materials
[11]: https://help.getjobber.com/hc/en-us/articles/30100867609367-Insights-Dashboard
[12]: https://play.google.com/store/apps/details?hl=en_US&id=housecall.pros
[13]: https://www.reddit.com/r/Plumbing/comments/1rqe4dh/plumberswhat_appsoftware_do_you_use_to_handle/
[14]: https://www.reddit.com/r/sweatystartup/comments/1bfw00i/not_happy_with_jobber_beware/
[15]: https://www.capterra.com/p/140363/HouseCall-Pro/reviews/
[16]: https://www.reddit.com/r/HVAC/comments/1c4g3pi/whats_your_biggest_problem_with_service_titan/
[17]: https://help.housecallpro.com/en/articles/6974306-homepage-overview-faq
[18]: https://help.housecallpro.com/en/articles/6934643-navigating-housecall-pro
[19]: https://www.servicetitan.com/blog/fall-2025-release-guide
[20]: https://help.getjobber.com/hc/en-us/articles/7061327071639-Jobber-App-Basics
[21]: https://help.getjobber.com/hc/en-us/articles/115010161128-Properties
[22]: https://help.getjobber.com/hc/en-us/articles/115009568687-User-Permissions
[23]: https://help.housecallpro.com/en/articles/1073431-team-member-roles-permissions
[24]: https://help.safetyculture.com/en-US/000032/
[25]: https://www.nyc.gov/site/buildings/property-or-business-owner/ll152-faqs.page
[26]: https://www.youtube.com/watch?v=-h0IFjAcO0k
