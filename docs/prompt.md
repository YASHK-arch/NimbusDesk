# Antigravity Build Prompt --- VentureTwin Simulation Workspace

## Mission

Build the **VentureTwin financial modelling and business simulation
workspace** shown in the supplied reference screenshot, using the
existing project repository and its current technology choices.

The screenshot is the primary visual reference for the simulation
workspace layout. Reproduce its overall information architecture and
interaction pattern---not its exact branding, text, or SAP-specific
functionality.

The product is a decision-intelligence workspace for SaaS executives. A
CEO should be able to edit business assumptions, run simulations,
compare conservative/realistic/optimistic outcomes, and ask the AI
system to investigate results. The interface must feel like a polished,
professional financial modelling application---not a generic chatbot
dashboard.

**Important:** This is an implementation task, not a request for a
design proposal. Inspect the repository, understand the existing
application, and then implement the feature end-to-end.

------------------------------------------------------------------------

## 1. First: inspect the existing project

Before changing code:

1.  Inspect the full repository structure, package files, existing
    routes, components, styles, state management, API clients, and
    backend endpoints.
2.  Identify the current frontend framework and existing design system.
3.  Identify which simulation, agent, and API functionality is already
    implemented.
4.  Reuse existing components and conventions wherever possible.
5.  Do not replace the project's architecture or rewrite working
    features just to match this prompt.
6.  Do not introduce a second frontend framework, duplicate API layer,
    or unnecessary dependencies.
7.  If a backend capability is not implemented yet, create a clearly
    separated integration boundary and use explicitly labelled demo data
    only where necessary.
8.  Do not claim that a mocked feature is connected to a real agent,
    data source, or simulation engine.

After inspection, provide a short implementation plan, then proceed with
the implementation without waiting for approval unless a genuinely
blocking ambiguity exists.

------------------------------------------------------------------------

## 2. Product and screen structure

Build a single **Simulation Workspace** with four major
horizontal/vertical regions.

### A. Top application toolbar

A compact toolbar spanning the workspace width. It should contain:

-   A small workspace/menu icon at the far left, if consistent with the
    existing app.
-   The four text menus: **File**, **Edit**, **Tools**, **Display**.
-   A subtle divider.
-   Undo and Redo icon buttons.
-   A Run/Refresh or Re-run Simulation icon/button where appropriate.
-   A bookmark/save-view control if supported by the application.
-   Clear hover, active, disabled, and keyboard-focus states.

Keep the toolbar visually restrained, similar to the supplied reference:
white or near-white surface, thin bottom border, compact spacing, small
typography, and understated icons.

### B. Simulation context row

Directly below the toolbar, show the current simulation context:

-   A labelled **Date / Forecast Period** control.
-   Default to a sensible year or period based on available data.
-   Use a date/year picker appropriate to the current model.
-   Changing the period must update the selected simulation context and
    trigger recalculation only when the model supports it.
-   Show the simulation name or company context if this fits the
    existing product structure without overcrowding the row.

### C. Main three-column workspace

Use a responsive three-column layout:

1.  **Left: Drivers panel** --- approximately 30--32% of available
    width.
2.  **Centre: Simulation results** --- approximately 48--52%.
3.  **Right: AI assistant / intelligence panel** --- approximately
    20--24%.

At desktop widths, keep all three regions visible, with independent
vertical scrolling where needed. Use subtle separators and consistent
panel padding. Avoid excessive rounded cards, heavy shadows, gradients,
or oversized headings.

At smaller widths, convert the columns into a sensible tabbed, drawer,
or stacked layout. Do not allow horizontal overflow.

------------------------------------------------------------------------

## 3. Left panel --- Drivers

Create a panel titled **Drivers**.

### Panel header

Include:

-   Drivers title.
-   Search input with a search icon.
-   A more-actions button (`...`) for driver-panel actions.
-   A filter button.
-   Optional driver count or active-filter indicator if useful.

### Driver table

Use a compact table-like layout with columns:

-   **Driver**
-   **Value Range**
-   **Distribution**

Group drivers into collapsible sections. Use the following initial
groups and example fields where they fit the current SaaS simulation
model:

**General** - Inflation

**Net Revenue** - Price Increase - GDP Growth - Discounts

**Operating Expenses** - Salary Increase - Infrastructure Cost per
User - Support Cost per Ticket

For the SaaS free-plan model, also support relevant business drivers
such as:

-   Monthly free sign-ups
-   Free-to-paid conversion
-   Paid customer churn
-   Free-user churn
-   Paid-plan cannibalization
-   Activation rate
-   Support tickets per free user
-   Infra cost per free user

Do not force every field into the initial visible list. Organize the
available variables by category and make the panel searchable.

### Driver controls

Each driver row should support, as appropriate:

-   Low and high range values.
-   Unit label (%, currency, users, months, etc.).
-   Distribution selector, such as Normal, Uniform, or Triangular.
-   Validation for missing, invalid, or inverted ranges.
-   Clear indication when a value has been modified from its baseline.
-   Tooltip or helper text explaining the driver.

Interactions:

-   Search filters drivers immediately.
-   Group headers expand/collapse.
-   Editing a driver updates the working model state.
-   Invalid values show inline validation; do not silently accept them.
-   The **Reset** button restores the original model assumptions after
    confirmation or with a clear undo path.
-   The more-actions menu may contain Add Driver, Manage Groups, and
    Reset Drivers if supported.

Do not fabricate precise company data. If using seed values, identify
them as synthetic/demo assumptions in the UI.

------------------------------------------------------------------------

## 4. Centre panel --- Simulation results

This is the primary visual focus.

### Results header

Include:

-   Heading: **Simulation Result**
-   **Output Variable** dropdown.
-   Primary **Re-run Simulation** button.

The output variable selector should be populated from metrics actually
supported by the model. For the SaaS use case, candidates include:

-   MRR
-   ARR
-   Operating Income / Net Contribution
-   Gross Margin
-   Cash Runway
-   Paying Customers
-   Free Users
-   Infrastructure Cost
-   Support Load

Do not display metrics that the active simulation cannot calculate.

### Main probability distribution chart

Build a large probability distribution visualization, inspired by the
reference screenshot.

It should:

-   Display the selected output variable on the horizontal axis.
-   Display probability/density on the vertical axis.
-   Distinguish **Conservative**, **Realistic**, and **Optimistic**
    scenario regions.
-   Show scenario boundary/marker lines and their corresponding values.
-   Include useful hover tooltips with values and probability
    information.
-   Include a legend or clear in-chart labels.
-   Update when a new simulation result arrives.
-   Handle loading, empty, and error states.

Use the charting library already present in the repository. If none
exists, choose one lightweight chart library compatible with the current
frontend and explain the choice in the implementation summary.

The chart must use actual simulator output when the simulation engine is
connected. If it is currently a prototype, use labelled synthetic/demo
output and keep the data adapter replaceable.

### Scenario Groups

Below the chart, show three scenario cards:

1.  **Pessimistic / Conservative**
2.  **Realistic / Expected**
3.  **Optimistic**

Each card should contain:

-   Scenario name and a distinct but restrained visual accent.
-   Probability or likelihood only if the model provides it.
-   Selected output metric and value.
-   Range or interval if available.
-   A compact list of influential assumptions or driver averages.
-   A clear positive/negative movement indicator only when there is a
    valid baseline comparison.

Clicking a scenario card should select/highlight that scenario and
update any relevant detail view. Do not use arbitrary percentages or
imply statistical confidence where none exists.

Add a small settings control near the Scenario Groups heading if the
model supports scenario configuration.

------------------------------------------------------------------------

## 5. Right panel --- AI assistant and intelligence

Create a persistent right-side panel titled **AI Assistant** or
**Decision Assistant**.

It should resemble the conversation panel in the reference image, but
use VentureTwin terminology and styling.

### Conversation area

Support:

-   User messages aligned to the right.
-   Assistant/agent messages aligned to the left.
-   Compact message spacing.
-   Timestamps or agent attribution where useful.
-   Loading/thinking state.
-   Error and retry state.
-   Scrollable conversation history.

### Composer

At the bottom, include:

-   A multi-line prompt input with placeholder such as **Ask about this
    simulation...**
-   Send button.
-   Optional attachment/context button only if supported.
-   Enter to send and Shift+Enter for a new line.
-   Disabled state while a request is being submitted, without
    preventing the user from reading history.

### Context-aware AI actions

The assistant should understand the currently selected simulation,
output variable, scenario, and driver values. Provide quick actions
where useful, for example:

-   Summarize simulation results
-   Explain the biggest cost drivers
-   Investigate a scenario
-   Compare scenarios
-   Identify assumptions that could change the recommendation

These actions must call the existing backend/agent workflow when
available. If the workflow is not yet connected, show a clearly labelled
demo response and keep the service integration isolated.

### Customer / Business Intelligence feed

Support a feed of business situations that may warrant investigation.
This is a distinct concept from the normal chat transcript.

Example feed items (label these as synthetic/demo scenarios unless
sourced from actual data):

-   **Pricing sensitivity:** Enterprise customers may resist a proposed
    price increase.
-   **Free-tier demand:** Smaller customer segments may respond
    positively to a limited free plan.
-   **Feature demand:** Basic-tier customers are requesting advanced
    analytics.
-   **Churn signal:** A customer segment shows a possible increase in
    churn.

Each feed item should include:

-   Severity or type badge.
-   Short title.
-   Concise description.
-   Origin, such as Customer Intelligence Agent or seeded demo data.
-   Time/period, if available.
-   **Investigate** action.
-   Dismiss or mark-as-reviewed action, if supported.

When the user clicks **Investigate**, send the selected scenario to the
supervisor/orchestrator as a new investigation request. The supervisor
should decide which specialist agents are relevant. Do not simply
display a fake animation.

Keep the feed visually distinct from the conversation. It may be a tab
or collapsible section within the right panel if space is limited.

------------------------------------------------------------------------

## 6. Navbar menus --- exact functional specification

All four menus must be real dropdown menus, not decorative labels. Use
accessible menu semantics, keyboard navigation, click-outside dismissal,
Escape-to-close, and visible focus states.

Do not implement menu items as dead ends. Every item must either perform
a meaningful action, open a working dialog/panel, or be visibly disabled
with a short explanation when the capability is not implemented.

### A. File menu

Group and implement these items:

**Simulation** - New Simulation - Open Simulation - Recent Simulations -
Close Simulation

**Save** - Save - Save As - Duplicate Simulation - Version History

**Data** - Import Data - Export Data

**Reports** - Export Report (PDF where supported) - Share Simulation
(only if sharing is implemented; otherwise disabled with explanation)

Expected behaviour:

-   New Simulation opens a creation flow or starts a blank supported
    model.
-   Open Simulation opens a selection dialog/list.
-   Save persists the current configuration using the existing
    persistence layer.
-   Save As creates a separate copy.
-   Duplicate Simulation creates a new simulation based on the current
    one.
-   Recent Simulations lists actual locally/API-persisted recent items;
    do not invent history.
-   Import Data accepts supported CSV/XLSX/JSON formats and validates
    the schema before applying.
-   Export Data downloads the current inputs/results in a supported
    format.
-   Export Report generates a report from the current simulation state.
-   Version History displays actual saved versions if versioning exists;
    otherwise show a clearly labelled not-yet-available state.

### B. Edit menu

Include:

-   Undo
-   Redo
-   Cut
-   Copy
-   Paste
-   Reset Parameters
-   Select All Drivers
-   Find Driver
-   Edit Driver Properties
-   Edit Model Assumptions
-   Preferences

Expected behaviour:

-   Undo/Redo operate on driver and model edits where feasible.
-   Disable Undo/Redo when no corresponding history exists.
-   Reset Parameters restores baseline assumptions and clearly
    communicates the effect.
-   Select All Drivers selects all visible/selectable driver rows.
-   Find Driver focuses the driver search input.
-   Edit Driver Properties opens a contextual editor for the selected
    driver.
-   Edit Model Assumptions opens the model-level assumptions editor.
-   Preferences opens a small settings dialog for relevant workspace
    preferences.

Do not show Cut/Copy/Paste as active if the application has no
meaningful selection/clipboard model. In that case, implement them for
selected driver rows or disable them with a reason.

### C. Tools menu

Use grouped sections:

**Simulation** - Run Simulation - Monte Carlo Simulation - What-if
Analysis - Scenario Comparison - Stress Testing - Break-even Analysis -
Forecasting

**Model Management** - Driver Manager - Distribution Manager -
Dependency Manager - Correlation Manager - Model Validator - Assumption
Ledger

**AI Intelligence** - Ask AI Analyst - Agent Analysis - Generate
Scenarios - Conflict Analysis - Risk Detection - Recommendation Engine -
Explain Results

**Advanced Analysis** - Sensitivity Analysis - Sensitivity Tornado -
Flip-point Analysis - Simulation History - Model Diagnostics - Agent
Execution Logs

Expected behaviour:

-   Run Simulation and Monte Carlo Simulation call the appropriate
    simulation service.
-   What-if Analysis opens a controlled way to change one or more
    assumptions and compare the result with the baseline.
-   Scenario Comparison allows supported scenarios to be selected and
    compared.
-   Stress Testing applies explicit stress assumptions and runs the
    model.
-   Break-even Analysis and Forecasting must use model calculations, not
    LLM-generated numbers.
-   Driver Manager, Distribution Manager, Dependency Manager, and
    Correlation Manager open focused panels/dialogs only if those model
    capabilities exist.
-   Model Validator runs deterministic checks.
-   Assumption Ledger displays each assumption, value/range, provenance,
    confidence (if provided), and source.
-   Ask AI Analyst focuses the assistant composer.
-   Agent Analysis invokes the supervisor/agent workflow with the
    current simulation context.
-   Generate Scenarios asks the scenario-generation capability to create
    candidate scenarios; label AI-generated assumptions appropriately.
-   Conflict Analysis displays actual detected conflicts or a clear
    empty state.
-   Risk Detection and Recommendation Engine use the implemented
    workflow; never fabricate findings.
-   Explain Results asks the assistant to explain the current simulator
    output while preserving the numerical source of truth.
-   Sensitivity Analysis and Sensitivity Tornado use simulator output.
-   Flip-point Analysis computes the threshold at which a preferred
    strategy changes.
-   Simulation History and Agent Execution Logs display
    persisted/run-time records if available.
-   Model Diagnostics displays deterministic validation and execution
    diagnostics.

If a tool is not yet implemented, keep the menu item visible only if it
helps communicate planned functionality, but disable it and provide a
concise "Not implemented yet" explanation. Do not create fake results.

### D. Display menu

Group into:

**Panels** - Show/Hide Drivers - Show/Hide Simulation Results -
Show/Hide AI Assistant - Show/Hide Scenario Groups - Reset Workspace
Layout

**Visualization** - Output Variable - Chart Type - Show Probability
Distribution - Show Confidence Intervals - Show Data Labels - Show
Gridlines

**Workspace** - Full Screen - Zoom In - Zoom Out - Reset Zoom - Theme:
Light / Dark / System

Expected behaviour:

-   Panel toggles visibly show/hide the corresponding region.
-   Reset Workspace Layout restores the default three-column layout.
-   Output Variable stays synchronized with the results header selector.
-   Chart Type changes the chart only to supported types.
-   Probability distribution and confidence interval controls should
    only be enabled when the required data exists.
-   Full Screen uses the browser Fullscreen API or a suitable
    workspace-level full-screen mode.
-   Zoom controls should affect the workspace content without making
    controls inaccessible.
-   Theme selection persists across reloads if the app already has a
    preferences mechanism.

------------------------------------------------------------------------

## 7. Visual design requirements

Follow the supplied screenshot's overall visual language:

-   Professional enterprise financial-modelling software.
-   Light theme as the initial/default theme.
-   White and very light neutral-grey surfaces.
-   Thin grey borders and subtle separators.
-   Compact typography and dense but readable information.
-   Blue as the primary action colour.
-   Muted red, violet, and teal accents for conservative, realistic, and
    optimistic scenario groups.
-   Small, consistent icons.
-   Restrained shadows and corner radii.
-   Clear hierarchy between toolbar, panel headings, chart, cards, and
    supporting text.

Avoid:

-   A generic AI-chat landing-page look.
-   Giant hero headings.
-   Excessive gradients or glassmorphism.
-   Oversized rounded cards.
-   Decorative charts with invented data.
-   Random animation or constant pulsing.
-   Excessive whitespace that reduces the amount of useful modelling
    information visible.

Use the screenshot as a layout and density reference. Adapt it to the
VentureTwin brand and SaaS decision use case.

------------------------------------------------------------------------

## 8. Functional and technical requirements

1.  Keep UI state, simulation state, and persisted data clearly
    separated.
2.  Use typed models/interfaces for drivers, assumptions, scenarios,
    simulation results, messages, and feed items.
3.  Keep menu actions in a centralized command/action layer rather than
    embedding complex logic in menu components.
4.  Keep chart components presentational; obtain data from the
    simulation service/state.
5.  Ensure changing driver values updates the model state and marks the
    simulation as **Modified / Results out of date** until rerun.
6.  A completed run should update the chart, scenario cards, run
    timestamp, and relevant history.
7.  Show loading, success, empty, validation, and error states.
8.  Avoid hardcoded numerical simulation results in production-facing
    components. Seeded demo data must be explicitly marked.
9.  Do not let an LLM generate final financial numbers. Financial
    outputs must come from deterministic model calculations or the
    existing simulation engine.
10. Keep agent and simulation APIs behind service adapters so the UI
    does not depend on a particular LLM provider.
11. If the project already uses WebSockets/SSE for agent activity, reuse
    it. Otherwise, do not introduce streaming infrastructure unless
    required by existing scope.
12. Preserve existing authentication and routing behaviour.
13. Make the layout usable at common desktop resolutions, especially
    1366×768 and 1920×1080.
14. Add accessible labels, semantic controls, keyboard support, and
    adequate contrast.

------------------------------------------------------------------------

## 9. Suggested component breakdown

Adapt names and folder locations to the existing repository. Do not
force this exact structure if the project already has an established
convention.

-   `SimulationWorkspace`
-   `WorkspaceToolbar`
-   `FileMenu`
-   `EditMenu`
-   `ToolsMenu`
-   `DisplayMenu`
-   `SimulationContextBar`
-   `DriversPanel`
-   `DriverSearch`
-   `DriverGroup`
-   `DriverRow`
-   `SimulationResultsPanel`
-   `OutputVariableSelector`
-   `ProbabilityDistributionChart`
-   `ScenarioGroups`
-   `ScenarioCard`
-   `DecisionAssistantPanel`
-   `ConversationThread`
-   `AssistantComposer`
-   `BusinessIntelligenceFeed`
-   `IntelligenceFeedItem`
-   `WorkspacePreferencesDialog`
-   `ImportDataDialog`
-   `SimulationPickerDialog`
-   `AssumptionLedgerPanel`

Keep components small and reusable. Avoid one enormous page component.

------------------------------------------------------------------------

## 10. Acceptance criteria

The work is complete only when all of the following are true:

### Layout

-   [ ] The simulation workspace follows the reference's toolbar +
    context row + three-column layout.
-   [ ] Drivers occupy the left panel, simulation results occupy the
    centre, and AI assistant/intelligence occupies the right.
-   [ ] The layout works at 1366×768 and 1920×1080 without accidental
    horizontal scrolling.
-   [ ] Responsive behaviour is implemented for narrower screens.

### Menus

-   [ ] File, Edit, Tools, and Display open functional dropdowns.
-   [ ] Menus are keyboard accessible and close on Escape/click outside.
-   [ ] Every enabled menu item performs a real action or opens a
    functional dialog/panel.
-   [ ] Unsupported features are clearly disabled rather than pretending
    to work.

### Drivers

-   [ ] Drivers are grouped and collapsible.
-   [ ] Search and filter work.
-   [ ] Values, ranges, units, and distributions are editable where
    supported.
-   [ ] Invalid values are validated.
-   [ ] Editing a driver marks results as out of date.
-   [ ] Reset restores baseline assumptions.

### Simulation

-   [ ] Output variable selection works.
-   [ ] Re-run Simulation invokes the real simulation service or a
    clearly labelled demo adapter.
-   [ ] Chart and scenario cards use the same current result data.
-   [ ] Loading, error, and empty states are present.
-   [ ] No unsupported metrics or fabricated certainty are displayed.

### AI and intelligence

-   [ ] Assistant messages and composer work with the existing
    backend/service adapter.
-   [ ] Context-aware actions include the current simulation context.
-   [ ] Business Intelligence Feed is visually distinct from chat.
-   [ ] Investigate sends the selected feed scenario to the
    supervisor/orchestrator when available.
-   [ ] Demo/seeded scenarios are clearly labelled.

### Quality

-   [ ] No existing working functionality is broken.
-   [ ] No major console errors or failed network requests.
-   [ ] No dead buttons or misleading success messages.
-   [ ] Existing tests pass; add focused tests for new behaviour where
    the project has a test setup.
-   [ ] Code is formatted and type/lint checks pass where configured.

------------------------------------------------------------------------

## 11. Implementation order

Work in this order to avoid building a polished but non-functional
mockup:

1.  Repository inspection and implementation plan.
2.  Workspace shell and responsive three-column layout.
3.  Toolbar and all four dropdown menus.
4.  Driver state, grouped driver editor, search, validation, reset,
    undo/redo where feasible.
5.  Simulation results header, output selector, chart, and scenario
    cards.
6.  Connect the simulation run action to the existing backend/model.
7.  AI assistant panel and context-aware actions.
8.  Business Intelligence Feed and Investigate flow.
9.  Display preferences, panel visibility, theme, and full-screen
    controls.
10. Tests, accessibility pass, responsive polish, and final
    verification.

Do not spend time on decorative polish before the core interactions
work.

------------------------------------------------------------------------

## 12. Final handoff

When finished, provide:

1.  A concise summary of what was implemented.
2.  The important files/components created or modified.
3.  Which actions are fully implemented, which use demo data, and which
    remain planned/disabled.
4.  Any backend endpoints or environment variables required.
5.  Commands to run the application and tests.
6.  Any known limitations.

**Final instruction:** Build the workspace to match the supplied
reference image's structure and density, while adapting the content and
behaviour to VentureTwin. Prioritize a functional, coherent simulation
product over a static visual clone. Do not silently invent integrations,
data, simulation outputs, agent activity, or business findings.
