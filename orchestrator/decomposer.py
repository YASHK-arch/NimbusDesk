"""Decomposition engine transforming a strategic Decision into a validated Task DAG with explicit task kinds."""

from __future__ import annotations

from orchestrator.dag import TaskDAG
from state.schemas import Decision, Task


def decompose_decision(decision: Decision) -> TaskDAG:
    """Decompose a decision into an execution DAG with explicit task kinds and strict ordering.

    Ordering for free_plan:
    agent analyses (parallel) -> conflict_detection -> skeptic_review -> simulation -> report_draft -> verification -> report_finalize.
    """
    dag = TaskDAG()

    if decision.type == "free_plan":
        # 1. Specialist Parallel Analysis Layer
        cfo_task = Task(id="task_cfo_analysis", owner_agent="CFO", kind="agent_analysis", depends_on=[])
        growth_task = Task(id="task_growth_analysis", owner_agent="Growth", kind="agent_analysis", depends_on=[])
        cto_task = Task(id="task_cto_analysis", owner_agent="CTO", kind="agent_analysis", depends_on=[])
        customer_task = Task(id="task_customer_analysis", owner_agent="Customer", kind="agent_analysis", depends_on=[])
        product_task = Task(id="task_product_analysis", owner_agent="Product", kind="agent_analysis", depends_on=[])

        dag.add_task(cfo_task)
        dag.add_task(growth_task)
        dag.add_task(cto_task)
        dag.add_task(customer_task)
        dag.add_task(product_task)

        # 2. Conflict Detection Layer
        conflict_task = Task(
            id="task_conflict_detection",
            owner_agent="Supervisor",
            kind="conflict_detection",
            depends_on=[
                cfo_task.id,
                growth_task.id,
                cto_task.id,
                customer_task.id,
                product_task.id,
            ],
        )
        dag.add_task(conflict_task)

        # 3. Skeptic Review Layer (runs BEFORE simulation to audit and adjust bounds)
        skeptic_task = Task(
            id="task_skeptic_review",
            owner_agent="Skeptic",
            kind="skeptic_review",
            depends_on=[conflict_task.id],
        )
        dag.add_task(skeptic_task)

        # 4. Deterministic Simulation Layer
        simulation_task = Task(
            id="task_simulation_resolution",
            owner_agent="Supervisor",
            kind="simulation",
            depends_on=[skeptic_task.id],
        )
        dag.add_task(simulation_task)

        # 5. Draft Report Generation Layer
        draft_task = Task(
            id="task_report_draft",
            owner_agent="Supervisor",
            kind="report_draft",
            depends_on=[simulation_task.id],
        )
        dag.add_task(draft_task)

        # 6. Real Verification Layer (audits draft report)
        verification_task = Task(
            id="task_workflow_verification",
            owner_agent="Supervisor",
            kind="verification",
            depends_on=[draft_task.id],
        )
        dag.add_task(verification_task)

        # 7. Final Report Finalization
        finalize_task = Task(
            id="task_report_finalize",
            owner_agent="Supervisor",
            kind="report_finalize",
            depends_on=[verification_task.id],
        )
        dag.add_task(finalize_task)

    elif decision.type == "price_change":
        cfo_task = Task(id="task_cfo_price_elasticity", owner_agent="CFO", kind="agent_analysis", depends_on=[])
        growth_task = Task(id="task_growth_demand_curve", owner_agent="Growth", kind="agent_analysis", depends_on=[])
        customer_task = Task(id="task_customer_churn_risk", owner_agent="Customer", kind="agent_analysis", depends_on=[])

        dag.add_task(cfo_task)
        dag.add_task(growth_task)
        dag.add_task(customer_task)

        sim_task = Task(
            id="task_pricing_simulation",
            owner_agent="Supervisor",
            kind="simulation",
            depends_on=[cfo_task.id, growth_task.id, customer_task.id],
        )
        dag.add_task(sim_task)

        skeptic_task = Task(
            id="task_skeptic_price_audit",
            owner_agent="Skeptic",
            kind="skeptic_review",
            depends_on=[sim_task.id],
        )
        dag.add_task(skeptic_task)

        draft_task = Task(
            id="task_report_draft",
            owner_agent="Supervisor",
            kind="report_draft",
            depends_on=[skeptic_task.id],
        )
        dag.add_task(draft_task)

        verification_task = Task(
            id="task_workflow_verification",
            owner_agent="Supervisor",
            kind="verification",
            depends_on=[draft_task.id],
        )
        dag.add_task(verification_task)

        finalize_task = Task(
            id="task_report_finalize",
            owner_agent="Supervisor",
            kind="report_finalize",
            depends_on=[verification_task.id],
        )
        dag.add_task(finalize_task)

    else:
        raise ValueError(f"Cannot decompose unsupported decision type: {decision.type}")

    dag.validate()
    return dag
