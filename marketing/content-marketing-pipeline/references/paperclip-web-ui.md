# Paperclip Web UI Reference

## App URL

`http://127.0.0.1:3100` (default port)

## Onboarding Flow (`/onboarding`)

4-step modal wizard with tabs: Company → Agent → Task → Launch.

### Step 1: Company
- Company name (required, placeholder "Acme Corp")
- Mission / goal (optional, placeholder "What is this company trying to achieve?")
- Next button disabled until company name is filled

### Step 2: Agent
- Agent name (default: "CEO")
- Adapter type — selectable cards:
  - **Claude Code** (tagged "Recommended") — Local Claude agent
  - **Codex** (tagged "Recommended") — Local Codex agent
  - **More Agent Adapter Types** — expands additional options
- Model selector — dropdown, "Default" is pre-selected
- Adapter environment check — "Test now" button runs a live probe (asks adapter CLI to respond with hello)
- Back / Next buttons

### Step 3: Task
- Task title (e.g. "Hire your first engineer and create a hiring plan")
- Description (optional, multiline textarea, e.g. "You are the CEO. You set the direction for the company...")
- Back / Next buttons

### Step 4: Launch
- Summary shows: Company name, "Company" label, Agent name, adapter type, Task title, "Task" label
- "Create & Open Task" button to finalize
- "Back" to revise

## Sidebar Navigation

- **Workspace switcher** — Top of sidebar, shows company initial + name. Click to open dropdown to switch companies.
- **Open search** — Search button
- **Collapse sidebar** — Toggle sidebar
- Main nav:
  - New Task (button)
  - Dashboard
  - Inbox
- WORK section:
  - Tasks
  - Routines
  - Goals
  - Artifacts
- Projects (collapsible):
  - Per-company project list with action menus
  - "New project" button
- Agents (collapsible):
  - Lists all agents in current company with action menus
  - "New agent" button
- Bottom nav:
  - Org
  - Skills
  - Costs
  - Activity
  - Settings

## Dashboard Widgets

- Agents count (enabled/running/paused/errors)
- Tasks In Progress (open/blocked)
- Month Spend (budget status)
- Pending Approvals
- Run Activity chart
- Tasks by Priority chart
- Tasks by Status chart
- Success Rate chart
- Recent Activity feed
- Recent Tasks list

## "Create Another Company"

After initial onboarding, a banner at the top of the page offers "Create another company" with a "Start Onboarding" button. This re-opens the onboarding modal.

## AIPharmaXchange Workspace

The user's active workspace with these agents and projects:

### Agents (10)
- BrandGuardian
- CEO
- TestAgent
- ContentDirector
- GitHubOSSLead
- LinkedInStrategist
- MarketingDirector
- NewsletterEditor
- ResearchAnalyst
- ResearchSynthesizer

### Projects (3)
- LinkedIn Growth (Pillar 2)
- Newsletter Growth (Pillar 1)
- Advocacy & GitHub (Pillar 3)
