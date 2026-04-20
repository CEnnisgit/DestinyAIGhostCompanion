# PDA-SDD Diagrams

Visual representations of the PDA-SDD model and its document structures.

---

## Figure 1: PDA-SDD Model

*Three phases with essential/optional outputs, backed by versioning and centralized storage.*

```mermaid
flowchart TB
    subgraph PRE["<b>Pre-Implementation</b>"]
        direction TB
        PRE_E["<b>Essential</b><br/>• SRSD<br/>• RLD"]
        PRE_O["<i>Optional</i><br/>• Contracts"]
    end

    subgraph DURING["<b>During-Implementation</b>"]
        direction TB
        DUR_E["<b>Essential</b><br/>• DDD<br/>• CLD<br/>• Project Plan"]
        DUR_O["<i>Optional</i><br/>• WBS"]
    end

    subgraph AFTER["<b>After-Implementation</b>"]
        direction TB
        AFT_E["<b>Essential</b><br/>• SUMD (User Manual)<br/>• Updated SRSD/DDD<br/>• Source Code<br/>• EULA"]
        AFT_O["<i>Optional</i><br/>• Quick Guide<br/>• Updated CLD<br/>• Certifications"]
    end

    PRE --> DURING --> AFTER

    subgraph INFRA["Cross-Phase Infrastructure"]
        V["Versioning System"]
        C["Centralized Storage"]
    end

    style PRE fill:#e3f2fd
    style DURING fill:#fff3e0
    style AFTER fill:#e8f5e9
    style INFRA fill:#f5f5f5
```

---

## Figure 2: SRSD Coding System

*Hierarchical requirement codes for traceability.*

```mermaid
flowchart TD
    SRSD["<b>SRSD</b>"]
    
    SRSD --> SGI["<b>SGI</b><br/>General Info"]
    SRSD --> SFR["<b>SFR</b><br/>Functional"]
    SRSD --> SNFR["<b>SNFR</b><br/>Non-Functional"]

    SGI --> SGI_S["SGI-S<br/>Scope"]
    SGI --> SGI_OJ["SGI-OJ<br/>Objectives"]
    SGI --> SGI_MF["SGI-MF<br/>Main Functions"]

    SFR --> IO["SFR-IO<br/>Input/Output"]
    SFR --> PR["SFR-PR<br/>Processing"]
    SFR --> BR["SFR-BR<br/>Business Rules"]
    SFR --> SR["SFR-SR<br/>Security"]
    SFR --> IR["SFR-IR<br/>Integration"]

    IO --> IODE["IODE<br/>Data Entry"]
    IO --> IODO["IODO<br/>Data Output"]
    IO --> IOR["IOR<br/>Reporting"]

    PR --> PRC["PRC<br/>Calculation"]
    PR --> PRDM["PRDM<br/>Decision"]
    PR --> PRDP["PRDP<br/>Manipulation"]

    BR --> BRC["BRC<br/>Constraints"]
    BR --> BRV["BRV<br/>Validation"]
    BR --> BRW["BRW<br/>Workflow"]

    SR --> SRAN["SRAN<br/>Authentication"]
    SR --> SRAZ["SRAZ<br/>Authorization"]
    SR --> SRAC["SRAC<br/>Access Control"]

    IR --> IRI["IRI<br/>Interface"]
    IR --> IRDX["IRDX<br/>Data Exchange"]
    IR --> IRIN["IRIN<br/>Interoperability"]

    SNFR --> P["SNFR-P<br/>Performance"]
    SNFR --> U["SNFR-U<br/>Usability"]
    SNFR --> S["SNFR-S<br/>Security"]
    SNFR --> R["SNFR-R<br/>Reliability"]
    SNFR --> M["SNFR-M<br/>Maintainability"]

    P --> PRT["PRT<br/>Response"]
    P --> PT["PT<br/>Throughput"]
    P --> PS["PS<br/>Scalability"]

    U --> UEU["UEU<br/>Ease of Use"]
    U --> UE["UE<br/>Efficiency"]
    U --> UA["UA<br/>Aesthetics"]

    S --> SC["SC<br/>Confidentiality"]
    S --> SI["SI<br/>Integrity"]
    S --> SA["SA<br/>Availability"]

    R --> RAV["RAV<br/>Availability"]
    R --> RAC["RAC<br/>Accuracy"]
    R --> RR["RR<br/>Robustness"]

    M --> MM["MM<br/>Modifiability"]
    M --> MT["MT<br/>Testability"]
    M --> MP["MP<br/>Portability"]

    style SRSD fill:#1565c0,color:#fff
    style SGI fill:#42a5f5
    style SFR fill:#66bb6a
    style SNFR fill:#ffa726
```

---

## Figure 3: DDD Structure

*Design document anchored by traceability to SRSD.*

```mermaid
flowchart TD
    DDD["<b>DDD</b><br/>Detailed Design Document"]
    
    DDD --> TM["<b>1. Traceability Matrix</b><br/><i>Links modules → SRSD</i>"]
    DDD --> SA["<b>2. System Architecture</b>"]
    DDD --> DD["<b>3. Data Design</b>"]
    DDD --> ID["<b>4. Interface Design</b>"]
    DDD --> MD["<b>5. Module Design</b>"]

    SA --> SA1["High-Level Diagram"]
    SA --> SA2["Technology Stack"]

    DD --> DD1["ERD"]
    DD --> DD2["Data Structures"]
    DD --> DD3["Database Schema"]

    ID --> ID1["UI Specifications"]
    ID --> ID2["API Specifications"]

    MD --> F1["Module: Feature 1"]
    MD --> F2["Module: Feature 2"]
    MD --> FN["Module: Feature n"]

    F1 --> F1a["• Responsibilities"]
    F1 --> F1b["• Structure"]
    F1 --> F1c["• Interactions"]
    F1 --> F1d["• Algorithms"]
    F1 --> F1e["• Data Structures"]

    style DDD fill:#1565c0,color:#fff
    style TM fill:#ffeb3b,color:#000
    style MD fill:#e8f5e9
```

---

## Figure 4: CLD Structure

*Change log organized by SRSD main functions (SGI-MF).*

```mermaid
flowchart TD
    CLD["<b>CLD</b><br/>Change Log Document"]
    
    CLD --> F1["<b>Feature 1</b><br/><i>(from SGI-MF)</i>"]
    CLD --> F2["<b>Feature 2</b>"]
    CLD --> FN["<b>Feature n</b>"]

    F1 --> L1["Log 001"]
    F1 --> L2["Log 002"]
    F1 --> LN["Log ..."]

    L1 --> L1a["<b>Significance</b><br/>Major/Minor + Domain"]
    L1 --> L1b["<b>Results</b><br/>Success/Failure"]
    L1 --> L1c["<b>Date</b>"]
    L1 --> L1d["<b>Change Summary</b>"]
    L1 --> L1e["<b>Detailed Changes</b>"]
    L1 --> L1f["<b>References</b><br/>SRSD codes"]
    L1 --> L1g["<b>Issue Tracking</b>"]
    L1 --> L1h["<b>Author</b>"]

    style CLD fill:#1565c0,color:#fff
    style F1 fill:#fff3e0
    style L1 fill:#e3f2fd
```

---

## Figure 5: Traceability Spine

*How documents connect across the lifecycle.*

```mermaid
flowchart LR
    subgraph PRE["Pre-Implementation"]
        SRSD["<b>SRSD</b><br/>Coded Requirements<br/>(SGI/SFR/SNFR)"]
    end

    subgraph DURING["During-Implementation"]
        TM["<b>Traceability Matrix</b><br/>SRSD → Modules"]
        DDD["<b>DDD</b><br/>Module Design"]
        CLD["<b>CLD</b><br/>Change History<br/><i>References SRSD codes</i>"]
    end

    subgraph AFTER["After-Implementation"]
        SRSD2["Updated SRSD"]
        DDD2["Updated DDD"]
        SRC["Source Code"]
    end

    SRSD -->|"requirements baseline"| TM
    TM --> DDD
    SRSD -->|"organizes sections"| CLD
    DDD -->|"chronicles changes"| CLD
    
    DDD -->|"delivery"| DDD2
    SRSD -->|"delivery"| SRSD2
    CLD -->|"delivery"| SRC

    style SRSD fill:#1565c0,color:#fff
    style TM fill:#ffeb3b,color:#000
    style CLD fill:#fff3e0
    style PRE fill:#e3f2fd
    style DURING fill:#fff3e0
    style AFTER fill:#e8f5e9
```

---

## Figure 6: RLD Structure

*Pre-stage resource grounding: Humans + Equipment.*

```mermaid
flowchart TD
    RLD["<b>RLD</b><br/>Resources List Document"]
    
    RLD --> HR["<b>Human Resources</b>"]
    RLD --> EQ["<b>Equipments</b>"]

    HR --> HRS["<b>Summary</b><br/>• Job Title<br/>• Sum (Quantity)"]
    HR --> HRD["<b>Details</b><br/>• Name<br/>• Job Title<br/>• Experience<br/>• Qualification<br/>• Hourly Cost"]

    EQ --> HW["<b>Hardware</b><br/>• Computers<br/>• Servers<br/>• Storage Devices"]
    EQ --> SW["<b>Software</b>"]

    SW --> SW1["Dev Environment"]
    SW --> SW2["Version Control"]
    SW --> SW3["DBMS"]
    SW --> SW4["Operating System"]
    SW --> SW5["Design Tools"]
    SW --> SW6["Testing Tools"]
    SW --> SW7["Deployment Tools"]
    SW --> SW8["PM Tools"]
    SW --> SW9["Communication"]
    SW --> SW10["Documentation"]
    SW --> SW11["Virtual Machines"]

    style RLD fill:#1565c0,color:#fff
    style HR fill:#e3f2fd
    style EQ fill:#fff3e0
```

---

## Figure 7: SUMD Structure

*User manual with 8-section structure for onboarding → usage → support.*

```mermaid
flowchart TD
    SUMD["<b>SUMD</b><br/>Software User Manual Document"]
    
    SUMD --> S1["<b>1. Introduction</b><br/>• Overview<br/>• Scope<br/>• Conventions"]
    SUMD --> S2["<b>2. Getting Started</b><br/>• Installation<br/>• System Requirements<br/>• Activation"]
    SUMD --> S3["<b>3. Basic Functionality</b><br/>• UI Overview<br/>• Core Features<br/>• Common Tasks"]
    SUMD --> S4["<b>4. Advanced Features</b><br/>• In-depth Explanations"]
    SUMD --> S5["<b>5. Troubleshooting</b><br/>• Common Problems<br/>• Error Messages<br/>• Technical Support"]
    SUMD --> S6["<b>6. Glossary</b><br/>• Definitions"]
    SUMD --> S7["<b>7. Appendix</b><br/>• Additional Information"]

    style SUMD fill:#1565c0,color:#fff
    style S1 fill:#e8f5e9
    style S2 fill:#e8f5e9
    style S3 fill:#e8f5e9
```

---

## Figure 8: EULA Structure

*Standardized 9-section End User License Agreement.*

```mermaid
flowchart TD
    EULA["<b>EULA</b><br/>End User License Agreement"]
    
    EULA --> E1["1. Grant of License"]
    EULA --> E2["2. Ownership"]
    EULA --> E3["3. Restrictions"]
    EULA --> E4["4. Disclaimer of Warranty"]
    EULA --> E5["5. Indemnification"]
    EULA --> E6["6. Termination of Agreement"]
    EULA --> E7["7. Governing Law & Jurisdiction"]
    EULA --> E8["8. Entire Agreement"]
    EULA --> E9["9. Severability"]

    style EULA fill:#1565c0,color:#fff
    style E1 fill:#ffebee
    style E4 fill:#ffebee
    style E6 fill:#ffebee
```

---

## Reference

- **Source:** Computers 2024, 13, 378 (Figures 2–8)
- **Philosophy:** [PDA_SDD_PHILOSOPHY.md](./PDA_SDD_PHILOSOPHY.md)
- **Spec:** [PDA_SDD_SPEC.md](./PDA_SDD_SPEC.md)

