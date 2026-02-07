# Design Document: ADE Compliance Framework

## Overview

The ADE Compliance Framework is an agentic-first system that enforces Axiom Driven Engineering (ADE) principles throughout the software development lifecycle. The framework operates as a constitutional enforcement layer, ensuring that all development activities—whether performed by AI agents or humans—adhere to formal axioms and postulates.

The system architecture follows a layered approach:
- **Compliance Engine**: Core validation logic for axiom checking
- **Integration Layer**: Git hooks, CLI, and programmatic API
- **Governance Layer**: Human Architect review gates and escalation protocols
- **Audit Layer**: Immutable logging and reporting
- **Agent Interface**: Self-governance capabilities for AI agents

The framework is language-agnostic, supporting Python, TypeScript, JavaScript, and Java codebases. It integrates seamlessly into existing workflows through Git hooks, pre-commit checks, and continuous monitoring.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Human Architect                          │
│              (Supreme Authority & Review)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Escalations & Overrides
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Governance Layer                           │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Escalation       │  │ Override         │                │
│  │ Protocol         │  │ Management       │                │
│  └──────────────────┘  └──────────────────┘                │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Compliance Engine                          │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Axiom Validators │  │ Rule Engine      │                │
│  │ - Π.1.1 Spec     │  │ - Check Runner   │                │
│  │ - Π.2.1 Test     │  │ - Result Agg     │                │
│  │ - Π.3.1 Trace    │  │ - Reporting      │                │
│  │ - Π.4.1 Arch     │  └──────────────────┘                │
│  │ - Π.5.3 Escal    │                                       │
│  └──────────────────┘                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Integration Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Git Hooks    │  │ CLI          │  │ API          │      │
│  │ - pre-commit │  │ - Manual     │  │ - Programmatic│     │
│  │ - pre-push   │  │   checks     │  │   interface  │      │
│  │ - pre-PR     │  │ - Reports    │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Audit Layer                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Audit Trail      │  │ Compliance       │                │
│  │ - Immutable Log  │  │ Dashboard        │                │
│  │ - Decision Log   │  │ - Metrics        │                │
│  │ - Override Log   │  │ - Trends         │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ Self-Governance
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Agent Interface                            │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Self-Check       │  │ Compliance       │                │
│  │ - Pre-execution  │  │ Reporting        │                │
│  │ - Uncertainty    │  │ - Attestation    │                │
│  │ - Escalation     │  │ - Traceability   │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Pre-Execution**: Agent performs self-check before tool execution
2. **Validation**: Compliance Engine runs axiom validators
3. **Decision**: Pass → proceed, Fail → block or escalate
4. **Escalation**: Critical decisions route to Human Architect
5. **Logging**: All decisions logged to immutable audit trail
6. **Reporting**: Compliance reports generated and dashboard updated

### Technology Stack

- **Core Language**: Python (for framework implementation)
- **Configuration**: YAML for rules, JSON for reports
- **Storage**: SQLite for audit trail (immutable, append-only)
- **CLI**: Click or Typer for command-line interface
- **Git Integration**: Python git hooks
- **API**: FastAPI for programmatic interface (optional)
- **Language Parsers**: Tree-sitter for multi-language AST parsing

## Components and Interfaces

### 1. Compliance Engine

**Purpose**: Core validation logic that checks axiom adherence

**Key Classes**:

```python
class ComplianceEngine:
    """Main engine for running compliance checks"""
    
    def check_all(self, context: CheckContext) -> ComplianceResult:
        """Run all applicable compliance checks"""
        
    def check_specification_exists(self, context: CheckContext) -> CheckResult:
        """Validate Π.1.1: Specification-first development"""
        
    def check_test_first(self, context: CheckContext) -> CheckResult:
        """Validate Π.2.1: Test-driven development"""
        
    def check_traceability(self, context: CheckContext) -> CheckResult:
        """Validate Π.3.1: Traceability to requirements"""
        
    def check_architecture(self, context: CheckContext) -> CheckResult:
        """Validate Π.4.1: Architecture compliance"""
        
    def check_escalation(self, context: CheckContext) -> CheckResult:
        """Validate Π.5.3: Three-strikes escalation"""

class CheckContext:
    """Context for a compliance check"""
    workspace_root: Path
    spec_directory: Path
    changed_files: List[Path]
    operation_type: OperationType  # commit, push, task_start, etc.
    agent_type: Optional[AgentType]

class ComplianceResult:
    """Result of compliance checks"""
    passed: bool
    checks: List[CheckResult]
    violations: List[Violation]
    escalations: List[Escalation]
    execution_time: float

class CheckResult:
    """Result of a single check"""
    check_name: str
    axiom_reference: str
    passed: bool
    message: str
    severity: Severity  # INFO, WARNING, ERROR, CRITICAL
```

### 2. Axiom Validators

**Purpose**: Individual validators for each axiom category

**Specification Validator (Π.1.1)**:
```python
class SpecificationValidator:
    """Validates specification-first development"""
    
    def validate(self, context: CheckContext) -> CheckResult:
        """Check that specs exist before implementation"""
        # 1. Check for requirements.md
        # 2. Check for design.md
        # 3. Validate format structure
        # 4. Verify approval status
```

**Test-First Validator (Π.2.1)**:
```python
class TestFirstValidator:
    """Validates test-driven development"""
    
    def validate(self, context: CheckContext) -> CheckResult:
        """Check that tests exist before implementation"""
        # 1. Map implementation files to test files
        # 2. Check test coverage
        # 3. Validate test determinism
        # 4. Check test-to-requirement links
```

**Traceability Validator (Π.3.1)**:
```python
class TraceabilityValidator:
    """Validates traceability links"""
    
    def validate(self, context: CheckContext) -> CheckResult:
        """Check traceability from code to requirements to axioms"""
        # 1. Extract traceability markers from code
        # 2. Validate links to requirements
        # 3. Validate requirement-to-axiom links
        # 4. Generate traceability matrix
    
    def extract_traceability_markers(self, file: Path) -> List[TraceLink]:
        """Extract traceability comments from code"""
        # Parse comments like: # Validates: Requirements 1.2, 3.4
```

**Architecture Validator (Π.4.1)**:
```python
class ArchitectureValidator:
    """Validates architecture compliance"""
    
    def validate(self, context: CheckContext) -> CheckResult:
        """Check architecture decisions and ADRs"""
        # 1. Detect architectural changes
        # 2. Check for corresponding ADR
        # 3. Validate ADR format
        # 4. Check against approved patterns
    
    def detect_architectural_change(self, diff: GitDiff) -> bool:
        """Detect if changes affect architecture"""
        # Heuristics: new modules, interface changes, etc.
```

### 3. Governance Layer

**Purpose**: Human Architect review gates and escalation handling

```python
class EscalationProtocol:
    """Handles escalations to Human Architect"""
    
    def should_escalate(self, decision: Decision) -> bool:
        """Determine if decision requires Human review"""
        # Criticality-based routing (< 5% of decisions)
        
    def escalate(self, decision: Decision, context: str) -> EscalationRequest:
        """Create escalation request with full context"""
        
    def record_human_decision(self, decision: HumanDecision) -> None:
        """Record Human Architect decision in audit trail"""

class OverrideManager:
    """Manages Human Architect overrides"""
    
    def request_override(self, violation: Violation, rationale: str) -> Override:
        """Request Human override for compliance violation"""
        
    def apply_override(self, override: Override) -> None:
        """Apply override and log to audit trail"""
        
    def query_overrides(self, filters: OverrideFilters) -> List[Override]:
        """Query override history"""
```

### 4. Audit Layer

**Purpose**: Immutable logging and compliance reporting

```python
class AuditTrail:
    """Immutable audit trail for all decisions"""
    
    def log_decision(self, decision: Decision) -> None:
        """Log decision with axiom reference"""
        # Append-only SQLite database
        
    def log_violation(self, violation: Violation) -> None:
        """Log compliance violation"""
        
    def log_override(self, override: Override) -> None:
        """Log Human Architect override"""
        
    def query(self, filters: AuditFilters) -> List[AuditEntry]:
        """Query audit trail"""
        # Support filtering by date, actor, axiom, component

class ComplianceDashboard:
    """Real-time compliance metrics and visualization"""
    
    def get_metrics(self) -> ComplianceMetrics:
        """Get current compliance metrics"""
        # Violation counts, trends, coverage, etc.
        
    def get_violations_by_axiom(self) -> Dict[str, int]:
        """Get violation counts grouped by axiom"""
        
    def get_traceability_completeness(self) -> float:
        """Calculate percentage of code with traceability"""
```

### 5. Integration Layer

**Purpose**: Git hooks, CLI, and programmatic API

**Git Hooks**:
```python
class PreCommitHook:
    """Pre-commit hook for compliance checks"""
    
    def run(self) -> int:
        """Run compliance checks on staged files"""
        # 1. Get staged files
        # 2. Run compliance checks
        # 3. Block commit if violations found
        # 4. Return exit code (0 = pass, 1 = fail)
        # Must complete within 10 seconds

class PrePushHook:
    """Pre-push hook for extended checks"""
    
    def run(self) -> int:
        """Run extended compliance checks"""
        # More comprehensive than pre-commit
```

**CLI Interface**:
```python
class ComplianceCLI:
    """Command-line interface for manual checks"""
    
    @click.command()
    def check_all():
        """Run all compliance checks"""
        
    @click.command()
    def check_traceability():
        """Run only traceability checks"""
        
    @click.command()
    def generate_report():
        """Generate compliance report"""
        
    @click.command()
    def show_dashboard():
        """Display compliance dashboard"""
```

**Programmatic API**:
```python
class ComplianceAPI:
    """Programmatic interface for tool integration"""
    
    def check_compliance(self, context: CheckContext) -> ComplianceResult:
        """Run compliance checks programmatically"""
        
    def get_status(self, component: str) -> ComplianceStatus:
        """Get compliance status for component"""
        
    def register_custom_rule(self, rule: CustomRule) -> None:
        """Register custom compliance rule"""
```

### 6. Agent Interface

**Purpose**: Self-governance capabilities for AI agents

```python
class AgentSelfCheck:
    """Self-check interface for agents"""
    
    def pre_execution_check(self, operation: Operation) -> SelfCheckResult:
        """Check compliance before executing operation"""
        # Agent calls this before any tool execution
        
    def should_escalate(self, uncertainty: float) -> bool:
        """Determine if agent should escalate to Human"""
        # Based on confidence threshold
        
    def generate_attestation(self, work: CompletedWork) -> Attestation:
        """Generate compliance attestation for completed work"""

class ComplianceReporter:
    """Compliance reporting for agents"""
    
    def generate_report(self, work: CompletedWork) -> ComplianceReport:
        """Generate machine-readable compliance report"""
        # JSON format with schema version
        
    def generate_attestation(self, work: CompletedWork) -> Attestation:
        """Generate signed attestation"""
```

## Data Models

### Core Data Structures

```python
@dataclass
class Axiom:
    """Represents an ADE axiom"""
    reference: str  # e.g., "Π.1.1"
    title: str
    description: str
    category: AxiomCategory  # SPECIFICATION, TEST, TRACEABILITY, ARCHITECTURE, ESCALATION

@dataclass
class Violation:
    """Represents a compliance violation"""
    id: str
    axiom_reference: str
    severity: Severity
    message: str
    file_path: Optional[Path]
    line_number: Optional[int]
    timestamp: datetime
    context: Dict[str, Any]

@dataclass
class TraceLink:
    """Represents a traceability link"""
    source_type: str  # code, test, requirement, axiom
    source_id: str
    target_type: str
    target_id: str
    link_type: str  # implements, validates, traces_to

@dataclass
class Decision:
    """Represents a decision made by agent or human"""
    id: str
    actor: str  # agent_id or "human_architect"
    decision_type: DecisionType
    axiom_reference: str
    rationale: str
    timestamp: datetime
    criticality: Criticality

@dataclass
class Override:
    """Represents a Human Architect override"""
    id: str
    violation_id: str
    rationale: str
    timestamp: datetime
    architect_id: str
    expiration: Optional[datetime]

@dataclass
class Attestation:
    """Agent compliance attestation"""
    agent_id: str
    work_id: str
    axioms_applied: List[str]
    compliance_status: Dict[str, bool]
    timestamp: datetime
    signature: str  # Hash of attestation content

@dataclass
class ComplianceReport:
    """Machine-readable compliance report"""
    schema_version: str
    report_id: str
    timestamp: datetime
    checks: List[CheckResult]
    traceability_matrix: List[TraceLink]
    violations: List[Violation]
    metrics: ComplianceMetrics
```

### Traceability Matrix

The traceability matrix links code → tests → requirements → axioms:

```
Code Module → Test Cases → Requirements → Axioms
    ↓            ↓             ↓            ↓
  auth.py → test_auth.py → Req 1.2 → Π.2.1, Π.3.1
```

Stored as a directed graph for efficient querying.

### Configuration Schema

```yaml
# .ade-compliance.yml
compliance:
  enabled: true
  performance_threshold_seconds: 10
  
  coverage:
    minimum_threshold: 80
    enforce: true
  
  escalation:
    human_review_percentage_target: 5
    criticality_threshold: "high"
  
  hooks:
    pre_commit:
      enabled: true
      checks:
        - specification_exists
        - test_first
        - traceability
    pre_push:
      enabled: true
      checks:
        - all
  
  axioms:
    - reference: "Π.1.1"
      enabled: true
      severity: "error"
    - reference: "Π.2.1"
      enabled: true
      severity: "error"
  
  language_support:
    - python
    - typescript
    - javascript
    - java
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Specification Existence Validation

*For any* implementation task, the Compliance Checker should verify that both requirements.md and design.md exist in the spec directory, and reject tasks that lack specifications.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 2: Test-First Enforcement

*For any* implementation code file, the Compliance Checker should verify that corresponding test files exist with test cases covering the functionality, and block implementation when tests are missing.

**Validates: Requirements 1.2, 3.1, 3.2, 3.3**

### Property 3: Traceability Validation

*For any* code module, test, or requirement, the Compliance Checker should verify that traceability links exist connecting code → tests → requirements → axioms, generate a complete traceability matrix, and block commits when links are missing or broken.

**Validates: Requirements 1.3, 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 4: Architecture Compliance

*For any* code change that affects system architecture, the Compliance Checker should detect the architectural impact, verify compliance with architecture axioms, and validate against approved architectural patterns.

**Validates: Requirements 1.4, 5.3, 5.4**

### Property 5: Compliance Check Blocking

*For any* failed compliance check, the Compliance Checker should block the operation and provide a detailed violation report with specific remediation guidance.

**Validates: Requirements 1.5**

### Property 6: Specification Format Validation

*For any* specification document (requirements or design), the Compliance Checker should validate that it follows the required format structure, including EARS patterns for requirements and "for all" quantification for correctness properties.

**Validates: Requirements 2.4, 10.1, 10.2, 10.3, 10.4**

### Property 7: Test Determinism Validation

*For any* test file, the Compliance Checker should analyze for non-deterministic patterns (external state dependencies, timing dependencies, order dependencies) and flag tests that are not deterministic and repeatable.

**Validates: Requirements 3.4, 8.1, 8.2, 8.3, 8.4**

### Property 8: ADR Requirement Enforcement

*For any* code change that affects system architecture, the Compliance Checker should determine if an ADR is required, verify that the ADR exists with required sections (rationale, alternatives, consequences), and block changes when ADRs are missing.

**Validates: Requirements 5.1, 5.2, 7.1, 7.2, 7.3**

### Property 9: Pre-Commit Hook Behavior

*For any* commit attempt, the Pre-Commit Hook should execute all compliance checks, block commits when checks fail, allow commits when checks pass, and log all results to the audit trail.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4**

### Property 10: Coverage Threshold Enforcement

*For any* code commit, the Compliance Checker should calculate test coverage metrics at module, file, and function levels, compare against configured thresholds, and block commits when coverage falls below thresholds.

**Validates: Requirements 9.1, 9.2, 9.3, 9.4**

### Property 11: Escalation Protocol Routing

*For any* decision requiring Human Architect review (axiom disputes, constitutional amendments, three-strike failures), the Escalation Protocol should route the decision to the Human Architect with full context, record the decision with rationale in the audit trail, and provide all attempted solutions and failure reasons.

**Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**

### Property 12: Audit Trail Immutability

*For any* decision made by an Agent or Human, the System should log it to the Audit Trail with all required fields (timestamp, actor, decision, axiom reference, rationale), ensure the trail is immutable and tamper-evident, and support querying by date, actor, axiom, or component.

**Validates: Requirements 18.1, 18.2, 18.3, 18.4**

### Property 13: Violation Tracking and Alerting

*For any* compliance violation, the System should record it with full context, categorize it by severity/axiom/component, generate trend reports showing patterns over time, and alert the Human Architect when violation rates exceed thresholds.

**Validates: Requirements 19.1, 19.2, 19.3, 19.4**

### Property 14: Override Management

*For any* Human Architect override, the System should record it in the Audit Trail with all required fields (rule overridden, rationale, timestamp, affected components), generate override reports for periodic review, and support querying by axiom, date, or component.

**Validates: Requirements 20.1, 20.2, 20.3, 20.4**

### Property 15: Machine-Readable Compliance Reports

*For any* compliance check execution, the System should generate a report in valid JSON format with schema version, all axiom checks with pass/fail status, and traceability links in structured format that is parseable by standard JSON tools.

**Validates: Requirements 28.1, 28.2, 28.3, 28.4, 28.5**

### Property 16: Agent Attestation Enforcement

*For any* completed work by an Agent, the Agent should provide a compliance attestation listing all applicable axioms with satisfaction status, signed with agent identifier and timestamp, and the System should reject work lacking proper attestation.

**Validates: Requirements 34.1, 34.2, 34.3, 34.4, 34.5**

### Property 17: Criticality-Based Decision Routing

*For any* decision, the System should classify it by criticality (low, medium, high, critical), automatically approve low/medium decisions that pass compliance checks, route high/critical decisions to Human Architect review, track the percentage of decisions requiring human review, and alert when the percentage exceeds 5%.

**Validates: Requirements 35.1, 35.2, 35.3, 35.4, 35.5**

## Error Handling

### Error Categories

1. **Validation Errors**: Specification format violations, missing traceability, etc.
   - Return detailed error messages with specific remediation guidance
   - Block operations until errors are resolved
   - Log to audit trail

2. **System Errors**: File I/O failures, database errors, parser failures
   - Log errors with full stack traces
   - Provide graceful degradation where possible
   - Alert Human Architect for critical system failures

3. **Configuration Errors**: Invalid configuration files, missing required settings
   - Validate configuration on startup
   - Provide clear error messages with examples
   - Use sensible defaults where appropriate

4. **Performance Errors**: Checks exceeding 10-second threshold
   - Log performance warnings
   - Suggest optimizations (incremental checking, caching)
   - Allow Human Architect to adjust thresholds

### Error Recovery

- **Transient Failures**: Retry with exponential backoff
- **Permanent Failures**: Escalate to Human Architect
- **Partial Failures**: Complete what's possible, report what failed
- **Cascading Failures**: Circuit breaker pattern to prevent system overload

### Error Reporting

All errors should include:
- Error code and category
- Detailed message with context
- Suggested remediation steps
- Relevant axiom references
- Timestamp and affected components

## Testing Strategy

### Dual Testing Approach

The ADE Compliance Framework requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and integration points
- Specific compliance check scenarios (e.g., missing requirements.md)
- Error handling paths
- Configuration parsing
- Git hook integration
- CLI command execution
- Edge cases: empty files, malformed JSON, circular traceability

**Property-Based Tests**: Verify universal properties across all inputs
- Minimum 100 iterations per property test
- Each test references its design document property
- Tag format: **Feature: ade-compliance-framework, Property {number}: {property_text}**

### Property-Based Testing Library

**Python**: Use Hypothesis for property-based testing
- Generates random test data (file structures, code samples, configurations)
- Shrinks failing examples to minimal reproducible cases
- Integrates with pytest

### Test Coverage Requirements

- Minimum 80% code coverage (configurable)
- 100% coverage of compliance validators
- 100% coverage of escalation protocol
- 100% coverage of audit trail operations

### Testing Phases

1. **Unit Testing**: Test individual validators and components
2. **Integration Testing**: Test Git hooks, CLI, and API
3. **Property Testing**: Verify universal correctness properties
4. **Performance Testing**: Verify 10-second threshold compliance
5. **End-to-End Testing**: Test complete workflows (commit → check → block/allow)

### Test Data Generation

For property-based tests, generate:
- Random file structures (with/without specs, tests, traceability)
- Random code samples (Python, TypeScript, JavaScript, Java)
- Random Git diffs (architectural vs. non-architectural changes)
- Random compliance configurations
- Random decision scenarios (various criticality levels)

### Continuous Testing

- Run unit tests on every commit
- Run property tests on every push
- Run full test suite on pull requests
- Monitor test execution time (should stay under 10 seconds)

## Implementation Notes

### Language Selection

The framework core will be implemented in **Python** for the following reasons:
- Excellent ecosystem for CLI tools (Click, Typer)
- Strong Git integration libraries (GitPython)
- Tree-sitter bindings for multi-language parsing
- Hypothesis for property-based testing
- SQLite support for audit trail
- Easy distribution via pip

### Multi-Language Support

Use Tree-sitter for parsing multiple languages:
- Python: tree-sitter-python
- TypeScript: tree-sitter-typescript
- JavaScript: tree-sitter-javascript
- Java: tree-sitter-java

Tree-sitter provides consistent AST parsing across languages, enabling language-agnostic traceability extraction.

### Performance Optimization

To meet the 10-second threshold:
- **Incremental Checking**: Only check changed files
- **Caching**: Cache parse results and traceability matrices
- **Parallel Execution**: Run independent checks in parallel
- **Early Exit**: Stop on first critical violation (configurable)
- **Lazy Loading**: Load language parsers on demand

### Deployment

- **Package**: Distribute as Python package via pip
- **Installation**: `pip install ade-compliance-framework`
- **Git Hooks**: Auto-install hooks via `ade-compliance install-hooks`
- **Configuration**: `.ade-compliance.yml` in repository root
- **Updates**: Support automatic updates via pip

### Extensibility

- **Custom Rules**: Plugin system for custom compliance rules
- **Custom Axioms**: Support for project-specific axioms
- **Custom Parsers**: Support for additional languages via Tree-sitter
- **Custom Reports**: Template system for custom report formats

### Security Considerations

- **Audit Trail Integrity**: Use cryptographic hashing to ensure tamper-evidence
- **Access Control**: Restrict override capabilities to Human Architect role
- **Secrets**: Never log sensitive data (API keys, passwords) in audit trail
- **Validation**: Sanitize all inputs to prevent injection attacks

### Migration Path

For existing projects:
1. Install framework: `pip install ade-compliance-framework`
2. Initialize configuration: `ade-compliance init`
3. Run initial audit: `ade-compliance audit --report`
4. Address violations incrementally
5. Enable enforcement: `ade-compliance install-hooks`
6. Monitor dashboard for compliance trends

### Human Architect Interface

The Human Architect interacts with the system through:
- **CLI**: For manual reviews and overrides
- **Dashboard**: For monitoring compliance metrics
- **Escalation Queue**: For reviewing critical decisions
- **Override Interface**: For approving exceptions with rationale
- **Configuration**: For adjusting thresholds and rules

The system ensures the Human Architect maintains supreme authority while minimizing review burden (< 5% of decisions).
