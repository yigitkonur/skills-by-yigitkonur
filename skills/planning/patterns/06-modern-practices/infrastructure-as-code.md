# Infrastructure as Code

**One-line summary:** Infrastructure as Code (IaC) treats server provisioning, networking, and configuration as software artifacts -- version-controlled, tested, reviewed, and deployed through the same pipeline as application code.

---

## Origin

The concept emerged from the DevOps movement in the late 2000s. Mark Burgess's CFEngine (1993) was an early predecessor. Puppet (2005) and Chef (2009) formalized configuration management. HashiCorp's Terraform (2014) popularized declarative infrastructure provisioning with its HCL language and multi-cloud provider model. AWS CloudFormation (2011) brought IaC to the cloud-native world. Kief Morris's *Infrastructure as Code* (O'Reilly, 2016; 2nd edition 2020) is the definitive reference. The core insight: manual infrastructure changes do not scale, cannot be reproduced, and cannot be audited.

---

## The Problem It Solves

Manual infrastructure management creates "snowflake servers" -- each environment is subtly different because it was configured by hand at different times by different people. Reproducing an environment requires tribal knowledge. Disaster recovery means hoping someone documented the setup steps (they did not). Scaling means repeating manual steps (and making new mistakes). Auditing means reading change logs (if they exist). IaC solves all of these by making infrastructure changes deterministic, repeatable, reviewable, and version-controlled.

---

## The Principle Explained

**Declarative vs. Imperative.** Declarative IaC (Terraform, CloudFormation, Pulumi with declarative mode) describes the desired end state: "I want a VPC with two subnets and an RDS instance." The tool figures out how to get there. Imperative IaC (Ansible playbooks, Pulumi with imperative mode, custom scripts) describes the steps: "Create a VPC, then create subnet A, then create subnet B." Declarative is generally preferred because it handles idempotency naturally and supports drift detection.

**Idempotency** means applying the same configuration multiple times produces the same result. If the infrastructure already matches the desired state, nothing changes. This eliminates the "did it run already?" problem and makes re-runs safe. Idempotency is essential for reliable CI/CD pipelines and disaster recovery.

**Drift detection** identifies when actual infrastructure has diverged from the declared state -- someone made a manual change in the console, a process modified a security group, or a deployment partially failed. Tools like Terraform plan, AWS Config, and Pulumi preview compare the real state against the declared state, showing exactly what has drifted and what will change.

---

## Code Examples

### BAD: Manual Infrastructure (Shell Scripts)

```typescript
// Imperative, non-idempotent, no state tracking
// deploy-infra.sh equivalent expressed as TypeScript for comparison

async function deployInfrastructure(): Promise<void> {
  // No idempotency: running this twice creates duplicates
  const vpc = await aws.createVpc({ cidrBlock: "10.0.0.0/16" });
  const subnet = await aws.createSubnet({
    vpcId: vpc.id,
    cidrBlock: "10.0.1.0/24",
  });

  // No drift detection: if someone changed the security group manually,
  // this script has no way to know or correct it
  const sg = await aws.createSecurityGroup({
    vpcId: vpc.id,
    name: "web-sg",
  });

  // No state file: if this fails halfway, there is no way to resume
  // or know what was already created
  await aws.addIngressRule(sg.id, { port: 443, cidr: "0.0.0.0/0" });
  await aws.addIngressRule(sg.id, { port: 80, cidr: "0.0.0.0/0" });

  // Hardcoded values: no parameterization, no environments
  const db = await aws.createRdsInstance({
    engine: "postgres",
    instanceClass: "db.t3.medium",
    subnetGroupId: subnet.id,
    securityGroupIds: [sg.id],
    masterUsername: "admin",
    masterPassword: "password123", // secret in code!
  });

  console.log(`Database endpoint: ${db.endpoint}`);
  // No outputs, no state, no audit trail
}
```

### GOOD: Declarative IaC with Pulumi (TypeScript)

```typescript
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

// Configuration: parameterized, environment-specific
const config = new pulumi.Config();
const environment = pulumi.getStack(); // "dev", "staging", "prod"
const dbInstanceClass = config.require("dbInstanceClass");

// Declarative: describe desired state, not steps
// Idempotent: running twice produces the same result

const vpc = new aws.ec2.Vpc("app-vpc", {
  cidrBlock: "10.0.0.0/16",
  enableDnsHostnames: true,
  tags: { Name: `app-vpc-${environment}`, Environment: environment },
});

const privateSubnetA = new aws.ec2.Subnet("private-a", {
  vpcId: vpc.id,
  cidrBlock: "10.0.1.0/24",
  availabilityZone: "us-east-1a",
  tags: { Name: `private-a-${environment}` },
});

const privateSubnetB = new aws.ec2.Subnet("private-b", {
  vpcId: vpc.id,
  cidrBlock: "10.0.2.0/24",
  availabilityZone: "us-east-1b",
  tags: { Name: `private-b-${environment}` },
});

const dbSecurityGroup = new aws.ec2.SecurityGroup("db-sg", {
  vpcId: vpc.id,
  description: "Allow PostgreSQL access from application subnets only",
  ingress: [
    {
      protocol: "tcp",
      fromPort: 5432,
      toPort: 5432,
      cidrBlocks: [privateSubnetA.cidrBlock, privateSubnetB.cidrBlock],
    },
  ],
  egress: [
    { protocol: "-1", fromPort: 0, toPort: 0, cidrBlocks: ["0.0.0.0/0"] },
  ],
  tags: { Name: `db-sg-${environment}` },
});

// Secrets managed properly: not in code
const dbPassword = config.requireSecret("dbPassword");

const dbSubnetGroup = new aws.rds.SubnetGroup("db-subnets", {
  subnetIds: [privateSubnetA.id, privateSubnetB.id],
  tags: { Name: `db-subnets-${environment}` },
});

const database = new aws.rds.Instance("app-db", {
  engine: "postgres",
  engineVersion: "15.4",
  instanceClass: dbInstanceClass,
  allocatedStorage: 20,
  dbSubnetGroupName: dbSubnetGroup.name,
  vpcSecurityGroupIds: [dbSecurityGroup.id],
  username: "app_admin",
  password: dbPassword,
  skipFinalSnapshot: environment !== "prod",
  backupRetentionPeriod: environment === "prod" ? 30 : 1,
  multiAz: environment === "prod",
  tags: { Name: `app-db-${environment}`, Environment: environment },
});

// Outputs: discoverable, typed, cross-stack referenceable
export const vpcId = vpc.id;
export const databaseEndpoint = database.endpoint;
export const databasePort = database.port;
```

---

## Tools Comparison

| Tool | Language | State | Multi-Cloud | Approach |
|---|---|---|---|---|
| **Terraform** | HCL (declarative) | Remote state file | Yes (broad) | Declarative, plan-apply cycle |
| **Pulumi** | TypeScript, Python, Go, etc. | Managed or self-hosted | Yes (broad) | Imperative code, declarative engine |
| **CloudFormation** | JSON/YAML | AWS-managed | AWS only | Declarative, stack-based |
| **AWS CDK** | TypeScript, Python, Java, etc. | Synthesizes to CloudFormation | AWS only | Imperative code, declarative output |
| **Ansible** | YAML (playbooks) | Stateless | Yes | Imperative, push-based |
| **Crossplane** | Kubernetes CRDs (YAML) | Kubernetes state | Yes | Declarative, Kubernetes-native |

---

## When NOT to Apply

- **One-off experiments.** Spinning up a single EC2 instance for a 2-hour test does not need a Terraform module. The AWS console is fine.
- **Rapidly changing prototypes.** When the infrastructure shape is unknown and changing daily, the IaC overhead can slow exploration. Switch to IaC once the architecture stabilizes.
- **Teams without IaC experience.** Adopting Terraform across a team that has never used it requires training time. A poorly written Terraform codebase can be worse than well-documented manual procedures.
- **Immutable infrastructure with container orchestration.** If your entire infrastructure is Kubernetes pods defined in Helm charts, you may not need a separate IaC layer for compute resources.

---

## Tensions & Trade-offs

- **Declarative simplicity vs. imperative power:** Declarative tools struggle with conditional logic, loops, and dynamic infrastructure. Imperative tools (Pulumi, CDK) handle complexity but can become spaghetti.
- **State management overhead:** Terraform's state file is a single point of failure. Remote state with locking (S3 + DynamoDB) adds operational complexity. Pulumi manages state for you but adds a dependency on their service.
- **Speed of iteration vs. safety:** A `terraform plan` before every change is safe but slow. Teams may be tempted to skip plans or auto-approve, undermining the safety net.
- **DRY modules vs. clarity:** Highly parameterized Terraform modules are reusable but hard to understand. Sometimes copying and adapting is clearer than abstracting.

---

## Real-World Consequences

- **GitLab's database deletion incident (2017)** could have been recovered faster with IaC. The team had to rebuild infrastructure partially from memory because not all configuration was codified.
- **Spotify** manages thousands of microservices with Terraform and Backstage, enabling developers to self-service infrastructure through templated IaC modules.
- **Capital One** uses IaC for compliance: every infrastructure change goes through code review and automated policy checks (Open Policy Agent), satisfying regulatory requirements.

---

## Key Quotes

> "If you can't reproduce your infrastructure from code, you don't have infrastructure -- you have a collection of hopes." -- Kief Morris

> "Treat your infrastructure like cattle, not pets." -- Bill Baker (attributed)

> "The goal of infrastructure as code is to make the provisioning of infrastructure a boring, repeatable, and automated process." -- Martin Fowler

> "Plan to throw one away; you will, anyhow." -- Fred Brooks (applicable to first IaC attempts)

---

## Further Reading

- *Infrastructure as Code* by Kief Morris (O'Reilly, 2nd edition 2020)
- *Terraform: Up and Running* by Yevgeniy Brikman (O'Reilly, 3rd edition 2022)
- Pulumi documentation (pulumi.com/docs) -- TypeScript-first IaC
- "Infrastructure as Code: What Is It? Why Is It Important?" by ThoughtWorks Technology Radar
- *The Phoenix Project* by Gene Kim, Kevin Behr, George Spafford (2013) -- cultural context for IaC adoption
