// ===================================
// Data
// ===================================

const axioms = [
    {
        number: "Σ.1",
        name: "The Correctness Axiom",
        statement: "A correct solution exists, given a specification's requirements.",
        justification: "Engineering is not improved by ambiguity. If requirements are defined, a solution that satisfies them must exist. If no such solution exists, the requirements are flawed.",
        implications: [
            "Specifications are strictly binding contracts",
            "Solving a problem requires first defining it (specifying)",
            "If a spec cannot be implemented, the spec must change, not the interpretation"
        ]
    },
    {
        number: "Σ.2",
        name: "Deterministic Verification",
        statement: "All behavior must be verifiable through deterministic tests.",
        justification: "Non-deterministic tests are not tests—they're hopes. Flaky tests erode trust. Trust erosion leads to ignored failures. Ignored failures become production incidents.",
        implications: [
            "Tests must be repeatable and isolated",
            "External dependencies must be mocked or controlled",
            "Random behavior must use seeded PRNG for reproducibility",
            "Async timing must not affect test outcomes"
        ]
    },
    {
        number: "Σ.3",
        name: "Traceable Rationale",
        statement: "Every decision must trace to an axiom or postulate.",
        justification: "Decisions without rationale cannot be evaluated, challenged, or evolved. When context is lost, technical debt accumulates invisibly.",
        implications: [
            "Architecture Decision Records (ADRs) are mandatory for significant changes",
            "ADRs must reference governing postulates",
            "Code comments explain 'why,' not 'what'",
            "Pull requests link to specifications and ADRs"
        ]
    },
    {
        number: "Σ.4",
        name: "Emergent Complexity",
        statement: "Complex systems emerge from composing simple, axiom-aligned components.",
        justification: "Complexity is unavoidable; understanding it is not. Systems built from small, well-defined components can be reasoned about. Monolithic complexity cannot.",
        implications: [
            "Favor composition over inheritance",
            "Each component should have a single, clear purpose",
            "Interfaces should be minimal and explicit",
            "Dependencies flow in one direction"
        ]
    },
    {
        number: "Σ.5",
        name: "AI Symbiosis",
        statement: "Human architects define intent; AI agents execute implementation.",
        justification: "Humans excel at judgment, creativity, and strategic thinking. AI excels at pattern application, consistency, and tireless execution. Optimal systems leverage both.",
        implications: [
            "Specifications are the contract between human and agent",
            "AI agents have explicit context files",
            "Agents operate within constitutional constraints",
            "Verification confirms AI output matches human intent"
        ]
    }
];

const methodologyPhases = [
    {
        number: 1,
        name: "Specify",
        question: "What & Why?",
        description: "Define user scenarios, functional requirements, and constraints. Establish the behavioral expectations before any implementation.",
        outputs: ["spec.md", "User Stories", "Acceptance Criteria"],
        postulate: "Π.1.1"
    },
    {
        number: 2,
        name: "Clarify",
        question: "Ambiguous?",
        description: "Resolve ambiguities through stakeholder review. Minimum 3 clarification cycles to ensure specification completeness.",
        outputs: ["Updated spec.md", "Resolved Questions"],
        postulate: "Π.1.1a"
    },
    {
        number: 3,
        name: "Plan",
        question: "How?",
        description: "Design component architecture, select technologies, define API contracts, and create ADRs for significant decisions.",
        outputs: ["plan.md", "ADRs", "Architecture Diagrams"],
        postulate: "Π.3.1, Π.4.1"
    },
    {
        number: 4,
        name: "Tasks",
        question: "When & Where?",
        description: "Decompose plan into atomic, dependency-aware tasks. Order by infrastructure → models → services → endpoints → UI.",
        outputs: ["tasks.md", "Task Dependencies"],
        postulate: "Π.1.2a"
    },
    {
        number: 5,
        name: "Implement",
        question: "Build it",
        description: "Execute Red-Green-Refactor cycle. Write failing tests first, implement minimal code to pass, then refactor for quality.",
        outputs: ["Code", "Tests", "Commits"],
        postulate: "Π.2.1, Π.2.2"
    },
    {
        number: 6,
        name: "Verify",
        question: "Does it work?",
        description: "Confirm implementation matches specification. Run all tests, check coverage, verify acceptance criteria.",
        outputs: ["Test Results", "Coverage Reports"],
        postulate: "Π.5.1b"
    },
    {
        number: 7,
        name: "Analyze",
        question: "What learned?",
        description: "Post-implementation review. Document lessons, update knowledge base, refine postulates if needed.",
        outputs: ["Retrospective", "Process Improvements"],
        postulate: "Π.3.1"
    }
];

const tools = [
    {
        name: "Windsurf",
        category: "Agentic IDE",
        icon: "🌊",
        description: "Flow State engine with deep context awareness. Maintains project understanding across multi-file refactoring."
    },
    {
        name: "Cline",
        category: "Autonomous Agent",
        icon: "🤖",
        description: "Open-source VS Code agent with MCP integration. Grounds specs in live system reality."
    },
    {
        name: "Warp",
        category: "Agentic Terminal",
        icon: "⚡",
        description: "AI-native terminal for DevOps automation. Executes infrastructure specs with natural language."
    },
    {
        name: "Tessl",
        category: "Spec Registry",
        icon: "📚",
        description: "Registry of verified library specifications. Eliminates API hallucination through version-accurate specs."
    },
    {
        name: "Eraser.io",
        category: "Diagram-as-Code",
        icon: "✏️",
        description: "Visual specifications with DiagramGPT. Converts text requirements into technical diagrams."
    },
    {
        name: "Swimm",
        category: "Knowledge Management",
        icon: "📖",
        description: "Code-coupled documentation. Prevents spec drift by linking docs directly to code."
    },
    {
        name: "Qodo",
        category: "Agentic Testing",
        icon: "🧪",
        description: "Autonomous test generation. Validates acceptance criteria with comprehensive test suites."
    },
    {
        name: "CodeRabbit",
        category: "AI Reviewer",
        icon: "🐰",
        description: "Semantic code review. Checks for logic errors and pattern deviations beyond syntax."
    },
    {
        name: "Greptile",
        category: "Context Engine",
        icon: "🔍",
        description: "Semantic codebase indexing. Enables repo-wide intelligence for AI agents."
    },
    {
        name: "LangSmith",
        category: "LLM Ops",
        icon: "🔬",
        description: "Observability for AI workflows. Debug and trace agent decision-making processes."
    }
];

// ===================================
// Navigation
// ===================================

document.addEventListener('DOMContentLoaded', () => {
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Active navigation link on scroll
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');

    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (pageYOffset >= sectionTop - 200) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });

    // Mobile navigation toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (navToggle) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });
    }

    // Initialize content
    renderAxioms();
    renderMethodology();
    renderTools();
});

// ===================================
// Axioms Rendering
// ===================================

function renderAxioms() {
    const axiomsGrid = document.querySelector('.axioms-grid');
    if (!axiomsGrid) return;

    axiomsGrid.innerHTML = axioms.map(axiom => `
        <div class="axiom-card" data-axiom="${axiom.number}">
            <div class="axiom-header">
                <div class="axiom-number">${axiom.number}</div>
                <div class="axiom-expand">▼</div>
            </div>
            <h3 class="axiom-title">${axiom.name}</h3>
            <blockquote class="axiom-statement">"${axiom.statement}"</blockquote>
            <div class="axiom-details">
                <div class="axiom-section">
                    <h4>Justification</h4>
                    <p>${axiom.justification}</p>
                </div>
                <div class="axiom-section">
                    <h4>Implications</h4>
                    <ul>
                        ${axiom.implications.map(imp => `<li>${imp}</li>`).join('')}
                    </ul>
                </div>
            </div>
        </div>
    `).join('');

    // Add click handlers for expansion
    document.querySelectorAll('.axiom-card').forEach(card => {
        card.addEventListener('click', () => {
            card.classList.toggle('expanded');
        });
    });
}

// ===================================
// Methodology Rendering
// ===================================

function renderMethodology() {
    const timeline = document.querySelector('.methodology-timeline');
    if (!timeline) return;

    timeline.innerHTML = methodologyPhases.map(phase => `
        <div class="phase-item">
            <div class="phase-content">
                <div class="phase-number">${phase.number}</div>
                <h3 class="phase-title">${phase.name}</h3>
                <p class="phase-description">${phase.description}</p>
                <div class="phase-outputs">
                    <h4>Outputs</h4>
                    <ul>
                        ${phase.outputs.map(output => `<li>${output}</li>`).join('')}
                    </ul>
                </div>
                <div style="margin-top: 1rem; color: var(--text-muted); font-size: 0.875rem;">
                    <strong>Governing Postulate:</strong> ${phase.postulate}
                </div>
            </div>
            <div class="phase-visual">
                <!-- Placeholder for future phase visualization -->
            </div>
        </div>
    `).join('');
}

// ===================================
// Tools Rendering
// ===================================

function renderTools() {
    const toolsGrid = document.querySelector('.tools-grid');
    if (!toolsGrid) return;

    toolsGrid.innerHTML = tools.map(tool => `
        <div class="tool-card">
            <div class="tool-icon">${tool.icon}</div>
            <h3 class="tool-name">${tool.name}</h3>
            <div class="tool-category">${tool.category}</div>
            <p class="tool-description">${tool.description}</p>
        </div>
    `).join('');
}

// ===================================
// Intersection Observer for Animations
// ===================================

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe elements for fade-in animation
document.addEventListener('DOMContentLoaded', () => {
    const animatedElements = document.querySelectorAll('.problem-card, .path-card, .tool-card');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});

// ===================================
// Search Functionality (Future Enhancement)
// ===================================

function initSearch() {
    // Placeholder for future search implementation
    // Could search across axioms, methodology, and tools
}

// ===================================
// Theme Toggle (Future Enhancement)
// ===================================

function initThemeToggle() {
    // Placeholder for light/dark theme toggle
    // Currently using dark theme by default
}
