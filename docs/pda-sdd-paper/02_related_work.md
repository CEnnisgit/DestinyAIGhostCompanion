# §3: Related Work & Background

## Software Documentation Landscape

Software documentation is a fundamental artifact throughout the software development lifecycle, from pre-coding to post-deployment. It captures a system's rationale, design, functionality, and operation. Despite its critical role, many deployed systems have inadequate, ambiguous, or obsolete documentation — often stemming from the perceived burden of technical writing and the significant time/resources required.

### Foundational Artifacts

- **Software Requirements Specification (SRS)** — Crafted early in the system lifecycle, articulating functional and non-functional requirements. Considered pivotal for system success.
- **User's Manual** — End-user documentation for system operation.
- **End User License Agreement (EULA)** — Critical legal artifact.

International organizations like IEEE and ISO have developed comprehensive guidelines for these documents, but concerns persist regarding human error and subjective interpretation during authoring.

### Existing Tools and Their Limitations

| Tool / Approach | Strength | Limitation |
|----------------|----------|------------|
| **IBM DOORS** | Robust requirements traceability for large, complex projects | Focused on requirements management only, not holistic documentation |
| **GitBook** | Collaborative content creation, version control, automated publishing | No structured guidance for full-spectrum development documentation |
| **Stoplight** | API documentation excellence | Limited to API documentation niche |
| **MBSE Tools** | Integrated design and analysis with linked artifacts | Requires specialized expertise, significant upfront investment |

**Common gap:** These tools operate in silos, demand significant integration overhead, and fail to provide the unified, holistic view of documentation's evolution needed across the entire lifecycle.

### The Evolving Landscape

- **Agile:** Documentation must function as a living, iteratively updated artifact. In practice, this means "just-enough" documentation and prioritizing working product over extensive written materials.
- **DevOps:** Necessitates documentation that supports automation and seamless deployment — "documentation as code" via versioning and automated publication within CI/CD pipelines.
- **Architecture as Code:** Frameworks that treat architectural definitions as machine-readable assets to automate compliance and reduce bottlenecks.
- **AI/LLMs:** Increasingly used to automate generation, updates, and maintenance of documentation, enhancing efficiency and consistency. But introduces challenges like "hallucinated" content, requiring human oversight.

### Research Gap

There is a notable lack of sustained attention on holistic software documentation processes. No existing framework provides a universally general, simple, and efficient solution for managing **all facets** of documentation across the **entire development lifecycle** for **all diverse stakeholders**.

The PDA-SDD model is conceptualized to bridge this gap — a holistic framework combining traditional principles with contemporary realities.
