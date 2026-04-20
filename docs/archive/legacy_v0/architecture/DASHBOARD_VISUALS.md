# Dashboard Visual Documentation

> Visual architecture snapshots and user flows for the Company Dashboard.
> Optimized for agent context and architectural understanding.

---

## 1. Information Architecture (Navigation Map)

Visualizes the structure of the dashboard application.

```mermaid
graph TD
    Login[Login Page] -->|Authenticate| Dashboard
    
    subgraph "Dashboard (Protected)"
        Dashboard[Dashboard Home]
        
        Dashboard --> Jobs[Jobs List]
        Dashboard --> Techs[Technicians]
        Dashboard --> Settings[Settings]
        
        Jobs -->|Create| CreateJob[Create Job]
        Jobs -->|View| JobDetail[Job Detail]
        
        Techs -->|Add| AddTech[Add Technician Modal]
    end
    
    JobDetail -->|Actions| Assign[Assign Modal]
    JobDetail -->|Actions| Schedule[Schedule Modal]
    JobDetail -->|View| Report[Inspection Report]
```

---

## 2. Component Hierarchy (Planned)

Visualizes the layout and component structure for the planned redesign.

```mermaid
classDiagram
    class App
    class DashboardLayout
    class Sidebar
    class Header
    class PageContent
    
    App *-- DashboardLayout
    DashboardLayout *-- Sidebar
    DashboardLayout *-- Header
    DashboardLayout *-- PageContent
    
    class Sidebar {
        +NavigationItems
        +UserProfile
        +CollapseToggle
    }
    
    class PageContent {
        < renders active page >
    }
    
    class DashboardHome {
        +StatsCards
        +StatusChart
        +ActivityFeed
    }
    
    class JobsPage {
        +SearchInput
        +StatusTabs
        +JobsTable
        +Pagination
    }
    
    PageContent *-- DashboardHome
    PageContent *-- JobsPage
```

---

## 3. Data Fetching & Auth Flow

Visualizes how the frontend retrieves data and handles authentication state.

```mermaid
sequenceDiagram
    participant Page as React Page
    participant AuthHook as useRequireAuth
    participant API as API Client (lib/api)
    participant Backend as Fastify API
    
    Page->>AuthHook: Check Auth
    AuthHook->>API: get /me
    
    alt Not Authenticated
        API-->>AuthHook: 401 Unauthorized
        AuthHook-->>Page: redirect to /login
    else Authenticated
        API-->>AuthHook: User + Company Data
        AuthHook-->>Page: isAuthenticated = true
        
        Page->>API: getJobs(filters)
        API->>Backend: GET /api/v1/jobs
        Backend-->>API: Job[]
        API-->>Page: Job[]
        Page->>Page: render(jobs)
    end
```

---

## 4. Job Management User Flow

Visualizes the user actions available at each stage of the job lifecycle from the dashboard perspective.

```mermaid
stateDiagram-v2
    state "Pending Assignment" as Pending
    state "Scheduled" as Scheduled
    state "In Progress" as InProgress
    state "Completed" as Completed
    state "Cancelled" as Cancelled
    
    [*] --> Pending: Create Job (Manual)
    
    Pending --> Scheduled: Assign Technician
    note right of Pending
        User Action: Click "Assign"
        Select Technician
        Select Date
    end note
    
    Scheduled --> Pending: Unassign
    Scheduled --> Scheduled: Re-assign (Change Tech/Date)
    
    Scheduled --> InProgress: (Waiting for Technician)
    
    InProgress --> Completed: (Waiting for Technician)
    
    Pending --> Cancelled: Cancel Job
    Scheduled --> Cancelled: Cancel Job
    InProgress --> Cancelled: Cancel Job
    
    Completed --> [*]: View Report
    Cancelled --> [*]
```

---

## 5. System Context (Apps & Users)

Visualizes how the Company Dashboard fits into the broader ecosystem.

```mermaid
graph TB
    subgraph "Users"
        Admin[Company Admin]
        Tech[Technician]
        Owner[Building Owner]
    end
    
    subgraph "Interfaces"
        Dashboard[🖥️ Company Dashboard]
        Mobile[📱 Technician App]
        Portal[🏠 Owner Portal]
    end
    
    subgraph "System"
        API[Backend API]
        DB[(Database)]
    end
    
    Admin -->|Manages Jobs| Dashboard
    Tech -->|Completes Jobs| Mobile
    Owner -->|Requests Service| Portal
    
    Dashboard --> API
    Mobile --> API
    Portal --> API
    
    API --> DB
```
